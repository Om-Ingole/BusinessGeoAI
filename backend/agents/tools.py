"""
ADK tool functions for the location intelligence agent.
Each function is a plain Python async function; ADK auto-wraps them as tools.

IMPORTANT: Tools must NOT receive request-scoped DB sessions.
           They open their own session via AsyncSessionLocal.
"""
import json
import logging
import os

from database import AsyncSessionLocal
from schemas import AnalyzeRequest
from services.analysis_service import analyze_location
from services import cache_service
from services.agent_service import summarize_report_for_agent
from services.location_providers.hybrid import get_provider
from utils.haversine import haversine

logger = logging.getLogger(__name__)

MAX_CHARS = int(os.getenv("ADK_MAX_CONTEXT_REPORT_CHARS", "30000"))


async def analyze_location_tool(
    query: str = "",
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float = 1.0,
    business_type: str = "retail",
) -> dict:
    """
    Run a full location analysis for an Indian address, pin code, or coordinates.
    Returns the analysis report as a structured dict.

    Args:
        query: Indian address, place name, or pin code. Use if lat/lon not known.
        lat: Latitude (-90 to 90). Use together with lon if known.
        lon: Longitude (-180 to 180). Use together with lat if known.
        radius_km: Search radius in km (0.5, 1, 2, or 5). Default 1.
        business_type: Type of business being evaluated (e.g. retail, cafe, clinic).
    """
    try:
        req = AnalyzeRequest(
            query=query or None,
            lat=lat,
            lon=lon,
            radius_km=max(0.5, min(5.0, radius_km)),
            business_type=business_type,
        )
    except Exception as e:
        return {"error": f"Invalid request: {e}"}

    async with AsyncSessionLocal() as db:
        try:
            result = await analyze_location(req, db)
        except Exception as e:
            logger.warning(f"analyze_location_tool failed: {e}")
            return {"error": str(e)}

    # Store in cache so get_cached_report_tool can retrieve it
    loc = result.get("location", {})
    query_hash = cache_service.make_hash(loc.get("lat", 0), loc.get("lon", 0), radius_km)
    async with AsyncSessionLocal() as db:
        await cache_service.set_cache(
            db, query_hash,
            loc.get("lat", 0), loc.get("lon", 0),
            loc.get("display_address", ""),
            loc.get("district", ""),
            loc.get("state", ""),
            result,
        )

    result["_analysis_id"] = query_hash
    return result


async def get_cached_report_tool(analysis_id: str) -> dict:
    """
    Retrieve a previously computed analysis report by its ID.

    Args:
        analysis_id: The analysis_id returned by analyze_location_tool.
    """
    async with AsyncSessionLocal() as db:
        cached = await cache_service.get_cached(db, analysis_id)
    if not cached:
        return {"error": f"No report found for analysis_id={analysis_id}"}
    return cached


async def compare_locations_tool(
    locations: list[dict],
    business_type: str = "retail",
) -> dict:
    """
    Run analysis on 2-4 locations and compare them side by side.

    Args:
        locations: List of dicts, each with 'query' and optional 'radius_km'.
                   Example: [{"query": "Indiranagar, Bengaluru", "radius_km": 1}]
        business_type: Business type to evaluate for each location.
    """
    if not locations or len(locations) < 2:
        return {"error": "Provide at least 2 locations for comparison"}
    if len(locations) > 4:
        locations = locations[:4]

    reports = []
    for loc_req in locations:
        result = await analyze_location_tool(
            query=loc_req.get("query", ""),
            lat=loc_req.get("lat"),
            lon=loc_req.get("lon"),
            radius_km=loc_req.get("radius_km", 1.0),
            business_type=business_type,
        )
        if "error" not in result:
            reports.append(result)

    if not reports:
        return {"error": "All location analyses failed"}

    comparison = []
    for r in reports:
        loc = r.get("location", {})
        breakdown = r.get("score_breakdown", {})
        comparison.append({
            "location": loc.get("display_address", loc.get("query", "Unknown")),
            "viability_score": r.get("viability_score"),
            "data_confidence": r.get("data_confidence"),
            "footfall": breakdown.get("footfall_proxy"),
            "transport": breakdown.get("transport_access"),
            "demographics": breakdown.get("demographics"),
            "crime_safety": breakdown.get("crime_safety"),
            "air_quality": breakdown.get("air_quality"),
            "business_density": breakdown.get("business_density"),
            "total_amenities": r.get("footfall_proxy", {}).get("total_amenities", 0),
            "best_use_cases": r.get("agent_insights", {}).get("best_use_cases", []),
            "key_risks": [risk.get("title") for risk in r.get("agent_insights", {}).get("risks", [])],
        })

    comparison.sort(key=lambda x: x.get("viability_score", 0), reverse=True)
    winner = comparison[0]["location"]
    reasons = []
    if len(comparison) > 1:
        top, second = comparison[0], comparison[1]
        for dim in ["footfall", "transport", "crime_safety", "air_quality"]:
            if (top.get(dim) or 0) > (second.get(dim) or 0) + 0.5:
                reasons.append(f"Better {dim.replace('_', ' ')} ({top[dim]:.1f} vs {second[dim]:.1f})")

    return {
        "winner": winner,
        "comparison": comparison,
        "reasons": reasons[:4],
        "risks": [r for entry in comparison for r in entry.get("key_risks", [])],
        "confidence": round(sum(c.get("data_confidence", 0.5) for c in comparison) / len(comparison), 2),
    }


async def business_fit_tool(report: dict, business_type: str) -> dict:
    """
    Evaluate how well a location suits a specific business type using existing report data.

    Args:
        report: Full analysis report dict (as returned by analyze_location_tool).
        business_type: Business type string, e.g. 'cafe', 'clinic', 'pharmacy',
                       'retail', 'qsr', 'office', 'supermarket'.
    """
    if not report or "viability_score" not in report:
        return {"error": "Invalid or empty report provided"}

    score = report.get("viability_score", 0)
    breakdown = report.get("score_breakdown", {})
    poi = report.get("poi") or {}
    insights = report.get("agent_insights") or {}
    demo = report.get("demographics") or {}

    bt = business_type.lower().strip()

    reasons: list[str] = []
    risks: list[str] = []
    checks: list[str] = []

    hospitals = len(poi.get("hospitals", []))
    pharmacies = len(poi.get("pharmacies", []))
    schools = len(poi.get("schools", []))
    bus_stops = len(poi.get("bus_stops", []))
    housing = len(poi.get("housing", []))
    corporates = len(poi.get("corporates", []))
    total = report.get("footfall_proxy", {}).get("total_amenities", 0)

    # Rule-based scoring adjustments per business type
    bt_score = score
    if bt in ("cafe", "coffee"):
        if corporates >= 3:
            reasons.append(f"{corporates} nearby corporate offices support weekday footfall")
            bt_score += 0.5
        if bus_stops >= 5:
            reasons.append(f"{bus_stops} bus stops provide transit catchment")
        if breakdown.get("air_quality", 5) < 5:
            risks.append("Poor AQI may affect outdoor seating plans")
        checks.append("Check nearby cafe competition via nearby_competition_tool")

    elif bt in ("clinic", "diagnostics", "doctor"):
        if hospitals >= 2:
            reasons.append(f"Medical cluster: {hospitals} hospitals nearby boost credibility")
            bt_score += 0.5
        if pharmacies >= 2:
            reasons.append(f"{pharmacies} pharmacies indicate medical demand")
        checks.append("Verify parking and ground-floor accessibility")

    elif bt in ("pharmacy", "medical store"):
        if hospitals >= 1 or pharmacies >= 1:
            reasons.append("Healthcare POI cluster supports pharmacy footfall")
        if breakdown.get("demographics", 5) >= 7:
            reasons.append("High-literacy urban population — good prescription adherence market")

    elif bt in ("retail", "shop", "boutique"):
        if total >= 30:
            reasons.append(f"{total} total amenities indicate high footfall zone")
        if bus_stops >= 4:
            reasons.append(f"Good bus connectivity ({bus_stops} stops)")
        checks.append("Check nearest supermarket/mall competition")

    elif bt in ("school", "coaching", "education"):
        if schools >= 2:
            risks.append(f"Already {schools} schools nearby — high competition")
        if housing >= 3:
            reasons.append(f"{housing} residential buildings ensure student catchment")

    elif bt in ("grocery", "supermarket"):
        if housing >= 5:
            reasons.append(f"{housing} residential buildings provide resident catchment")
        if breakdown.get("demographics", 5) >= 6:
            reasons.append("Urban population supports daily grocery demand")

    elif bt in ("office", "coworking"):
        if breakdown.get("transport_access", 5) >= 7:
            reasons.append("Excellent transport access for employee commutes")
        if corporates >= 2:
            reasons.append(f"Existing corporate cluster ({corporates} offices) signals B2B demand")

    elif bt in ("qsr", "restaurant", "food"):
        if total >= 25:
            reasons.append(f"High footfall zone ({total} amenities)")
        if bus_stops >= 3 or housing >= 4:
            reasons.append("Residential/transit mix drives meal-time traffic")

    # Generic risk flags regardless of business type
    crimes = report.get("crime", {}) or {}
    if crimes.get("latest_crimes_per_lakh", 0) > 250:
        risks.append("High crime rate — security investment required")

    aqi_val = (report.get("aqi") or {}).get("pollutant_avg")
    if aqi_val and aqi_val > 200:
        risks.append("Poor AQI — relevant for health-conscious customers")

    bt_score = round(min(10.0, max(0.0, bt_score)), 1)
    fit = "Good" if bt_score >= 6.5 else "Maybe" if bt_score >= 4 else "Poor"

    if not reasons:
        reasons.append(f"General viability score {score}/10")

    return {
        "fit": fit,
        "score": bt_score,
        "business_type": business_type,
        "reasons": reasons,
        "risks": risks,
        "recommended_next_checks": checks + [q for q in insights.get("next_questions", [])[:2]],
    }


async def nearby_competition_tool(
    lat: float,
    lon: float,
    radius_km: float = 1.0,
    business_type: str = "cafe",
) -> dict:
    """
    Find nearby competitor businesses using Google Places text search.

    Args:
        lat: Latitude of the origin location.
        lon: Longitude of the origin location.
        radius_km: Search radius in km.
        business_type: Type of business to search for (e.g. cafe, pharmacy, restaurant).
    """
    provider = get_provider()
    radius_m = int(radius_km * 1000)

    # Use text search for competition lookup
    try:
        from services.location_providers.google_maps import GoogleMapsProvider, PLACES_TEXT_URL, DEFAULT_FIELD_MASK
        import httpx, os
        api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
        if not api_key:
            return {"error": "GOOGLE_MAPS_API_KEY not configured; cannot search competitors"}

        headers = {
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": DEFAULT_FIELD_MASK,
            "Content-Type": "application/json",
        }
        body = {
            "textQuery": f"{business_type} near {lat},{lon}",
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": float(radius_m),
                }
            },
            "maxResultCount": 15,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(PLACES_TEXT_URL, headers=headers, json=body)
            resp.raise_for_status()
        places = resp.json().get("places", [])
        competitors = []
        for p in places:
            loc = p.get("location", {})
            p_lat = loc.get("latitude", 0)
            p_lon = loc.get("longitude", 0)
            dist = haversine(lat, lon, p_lat, p_lon) if p_lat and p_lon else None
            competitors.append({
                "name": p.get("displayName", {}).get("text", "Unknown"),
                "rating": p.get("rating"),
                "user_rating_count": p.get("userRatingCount"),
                "distance_km": round(dist, 3) if dist else None,
                "business_status": p.get("businessStatus"),
                "google_maps_uri": p.get("googleMapsUri"),
            })
        competitors.sort(key=lambda x: x.get("distance_km") or 999)
        return {"competitors": competitors, "count": len(competitors), "radius_km": radius_km}

    except Exception as e:
        logger.warning(f"Competition search failed: {e}")
        return {"error": str(e), "competitors": []}


async def route_access_tool(
    origin_lat: float,
    origin_lon: float,
    destinations: list[dict],
    mode: str = "DRIVE",
) -> dict:
    """
    Compute travel time and distance from origin to multiple destinations.

    Args:
        origin_lat: Latitude of origin.
        origin_lon: Longitude of origin.
        destinations: List of dicts with keys: lat, lon, name.
        mode: Travel mode — DRIVE, TWO_WHEELER, TRANSIT, or WALK.
    """
    if not destinations:
        return {"routes": [], "error": "No destinations provided"}

    provider = get_provider()
    origin = {"lat": origin_lat, "lon": origin_lon}
    valid_modes = {"DRIVE", "TWO_WHEELER", "TRANSIT", "WALK"}
    mode = mode.upper() if mode.upper() in valid_modes else "DRIVE"

    try:
        routes = await provider.compute_routes(origin, destinations, mode)
        return {"routes": routes, "mode": mode}
    except Exception as e:
        logger.warning(f"route_access_tool failed: {e}")
        # Haversine fallback
        routes = []
        for dest in destinations:
            dist = haversine(origin_lat, origin_lon, dest.get("lat", 0), dest.get("lon", 0))
            routes.append({
                "destination_name": dest.get("name", ""),
                "distance_km": round(dist, 2),
                "duration_minutes": None,
                "mode": mode,
                "fallback": True,
            })
        return {"routes": routes, "mode": mode, "fallback": True}
