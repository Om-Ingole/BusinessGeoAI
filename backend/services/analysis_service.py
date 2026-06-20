"""
Core analysis orchestration extracted from the router.
Called by:
  • routers/location.py   (HTTP endpoint)
  • agents/tools.py        (ADK tool functions — never HTTP-self-calls)
"""
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from schemas import AnalyzeRequest
from services import aqi_service, cache_service, score_service, static_data_service
from services.agent_service import generate_insights
from services.location_providers.hybrid import get_provider

logger = logging.getLogger(__name__)

ALL_CATEGORIES = [
    "hospitals", "schools", "bus_stops", "railway", "metro",
    "corporates", "housing", "pharmacies", "banks", "supermarkets",
]


async def analyze_location(req: AnalyzeRequest, db: AsyncSession) -> dict:
    """
    Full location analysis pipeline.
    Returns a dict matching AnalyzeResponse schema.
    """
    warnings: list[str] = []
    provider = get_provider()

    # 1. Resolve coordinates
    if req.lat is not None and req.lon is not None:
        try:
            geo = await provider.reverse_geocode(req.lat, req.lon)
        except Exception as e:
            warnings.append(f"Reverse geocode failed: {e}")
            geo = {
                "lat": req.lat,
                "lon": req.lon,
                "display_name": f"{req.lat},{req.lon}",
                "provider": "fallback",
                "district": "",
                "city": "",
                "state": "",
                "postcode": None,
            }
        geo["lat"] = req.lat
        geo["lon"] = req.lon
    elif req.query:
        try:
            geo = await provider.geocode(req.query)
        except Exception as e:
            raise ValueError(f"Could not geocode '{req.query}': {e}") from e
    else:
        raise ValueError("Provide query or lat+lon")

    lat = float(geo["lat"])
    lon = float(geo["lon"])
    radius_m = int(req.radius_km * 1000)
    district = geo.get("district") or geo.get("city") or ""
    state = geo.get("state") or ""
    geo_provider = geo.get("provider", "osm")

    # 2. Check cache
    query_hash = cache_service.make_hash(lat, lon, req.radius_km)
    cached = await cache_service.get_cached(db, query_hash)
    if cached:
        return cached

    # 3. Fan-out: all external data concurrently
    (
        poi,
        aqi,
        airports,
        railway_stations,
        demographics,
        crime,
        msme_sectors,
    ) = await asyncio.gather(
        provider.fetch_poi(lat, lon, radius_m, ALL_CATEGORIES),
        aqi_service.get_nearest_aqi(lat, lon, state),
        static_data_service.get_nearest_airports(db, lat, lon),
        static_data_service.get_nearest_railway(db, lat, lon),
        static_data_service.get_demographics(db, district, state),
        static_data_service.get_crime(db, district, state),
        static_data_service.get_msme_sectors(db, district, state),
        return_exceptions=True,
    )

    # 4. Coerce exceptions to safe defaults
    if isinstance(poi, Exception):
        logger.warning(f"POI fetch failed: {poi}")
        warnings.append("POI data unavailable")
        poi = {}
    if isinstance(aqi, Exception):
        logger.warning(f"AQI fetch failed: {aqi}")
        aqi = {"error": "unavailable", "station": None}
    if isinstance(airports, Exception):
        logger.warning(f"Airport fetch failed: {airports}")
        airports = []
    if isinstance(railway_stations, Exception):
        logger.warning(f"Railway fetch failed: {railway_stations}")
        railway_stations = []
    if isinstance(demographics, Exception):
        logger.warning(f"Demographics fetch failed: {demographics}")
        demographics = None
    if isinstance(crime, Exception):
        logger.warning(f"Crime fetch failed: {crime}")
        crime = None
    if isinstance(msme_sectors, Exception):
        logger.warning(f"MSME fetch failed: {msme_sectors}")
        msme_sectors = []

    nearest_railway = railway_stations[0] if railway_stations else None

    # Determine POI provider metadata
    first_poi_provider = "osm"
    if poi:
        for cat_items in poi.values():
            if cat_items:
                first_poi_provider = cat_items[0].get("provider", "osm")
                break
    fallback_used = geo.get("fallback", False)
    missing_sources = []
    if not demographics:
        missing_sources.append("demographics")
    if isinstance(aqi, dict) and aqi.get("error"):
        missing_sources.append("aqi")
    if not crime:
        missing_sources.append("crime")
    if not msme_sectors:
        missing_sources.append("msme")

    # 5. Score
    viability_score, score_breakdown, data_confidence = score_service.calculate_viability_score(
        poi=poi,
        demographics=demographics,
        crime=crime,
        aqi=aqi,
        nearest_railway=nearest_railway,
        msme_sectors=msme_sectors,
        fallback_used=fallback_used,
        missing_sources=missing_sources,
    )

    # 6. Footfall proxy
    total_amenities = sum(len(v) for v in poi.values()) if poi else 0
    footfall_proxy = {
        "poi_density_score": round(min(100, total_amenities * 2), 1),
        "total_amenities": total_amenities,
        "peak_hours_est": "6PM–9PM est.",
    }

    # 7. Deterministic insights
    agent_insights = generate_insights(
        poi=poi,
        demographics=demographics,
        crime=crime,
        aqi=aqi,
        airports=airports,
        railway_stations=railway_stations,
        msme_sectors=msme_sectors,
        viability_score=viability_score,
        score_breakdown=score_breakdown,
        poi_provider=first_poi_provider,
        fallback_used=fallback_used,
        missing_sources=missing_sources,
    )

    # 8. Build response
    aqi_clean = None
    if isinstance(aqi, dict) and not aqi.get("error") and aqi.get("station"):
        aqi_clean = aqi

    result = {
        "location": {
            "query": req.query,
            "lat": lat,
            "lon": lon,
            "display_address": geo.get("display_name"),
            "district": district,
            "city": geo.get("city"),
            "state": state,
            "pin_code": geo.get("postcode"),
        },
        "viability_score": viability_score,
        "score_breakdown": score_breakdown,
        "data_confidence": data_confidence,
        "demographics": demographics,
        "aqi": aqi_clean,
        "crime": crime,
        "poi": poi,
        "airports": airports,
        "nearest_railway": nearest_railway,
        "railway_stations": railway_stations,
        "msme_sectors": msme_sectors,
        "footfall_proxy": footfall_proxy,
        "agent_insights": agent_insights,
        "provider": geo_provider,
        "partial": bool(warnings),
        "warnings": warnings,
    }

    return result
