"""
Deterministic (rule-based) location intelligence insights.
No LLM required — runs on every /api/analyze response.
"""
from __future__ import annotations


def generate_insights(
    poi: dict,
    demographics: dict | None,
    crime: dict | None,
    aqi: dict | None,
    airports: list,
    railway_stations: list,
    msme_sectors: list,
    viability_score: float,
    score_breakdown: dict,
    poi_provider: str = "osm",
    fallback_used: bool = False,
    missing_sources: list | None = None,
) -> dict:
    if missing_sources is None:
        missing_sources = []

    risks: list[dict] = []
    opportunities: list[dict] = []
    best_use_cases: list[str] = []

    p = poi or {}
    hospitals = p.get("hospitals", [])
    schools = p.get("schools", [])
    pharmacies = p.get("pharmacies", [])
    bus_stops = p.get("bus_stops", [])
    metro = p.get("metro", [])
    railway = p.get("railway", [])
    supermarkets = p.get("supermarkets", [])
    banks = p.get("banks", [])
    housing = p.get("housing", [])
    corporates = p.get("corporates", [])

    total_amenities = sum(len(v) for v in p.values())

    # ── Risks ─────────────────────────────────────────────────────────────────

    aqi_val = aqi.get("pollutant_avg") if aqi and not aqi.get("error") else None
    if aqi_val is not None and aqi_val > 200:
        risks.append({
            "severity": "high",
            "title": "Poor air quality",
            "evidence": f"Nearest CPCB station reports AQI {int(aqi_val)} ({aqi.get('aqi_category', 'Poor')})",
            "recommendation": "Avoid health-sensitive business positioning; consider adding filtration messaging",
        })
    elif aqi_val is not None and aqi_val > 100:
        risks.append({
            "severity": "medium",
            "title": "Moderate air quality",
            "evidence": f"AQI {int(aqi_val)} — {aqi.get('aqi_category', 'Moderate')}",
            "recommendation": "Monitor seasonal variation; acceptable for most businesses",
        })

    crimes_per_lakh = crime.get("latest_crimes_per_lakh") if crime else None
    if crimes_per_lakh is not None and crimes_per_lakh > 300:
        risks.append({
            "severity": "high",
            "title": "High crime rate",
            "evidence": f"{int(crimes_per_lakh)} IPC crimes per lakh population",
            "recommendation": "Factor in security costs; consider insurance and CCTV investment",
        })
    elif crimes_per_lakh is not None and crimes_per_lakh > 150:
        risks.append({
            "severity": "medium",
            "title": "Elevated crime rate",
            "evidence": f"{int(crimes_per_lakh)} IPC crimes per lakh population",
            "recommendation": "Standard security measures recommended",
        })

    if score_breakdown.get("transport_access", 5) < 3:
        risks.append({
            "severity": "medium",
            "title": "Poor transport connectivity",
            "evidence": f"{len(bus_stops)} bus stops, nearest railway {railway_stations[0].get('distance_km', '?')} km" if railway_stations else "No railway data",
            "recommendation": "Walk-in traffic will be limited; parking or delivery model advised",
        })

    if missing_sources:
        risks.append({
            "severity": "low",
            "title": "Incomplete data",
            "evidence": f"Missing: {', '.join(missing_sources)}",
            "recommendation": "Confidence is reduced; verify locally before decisions",
        })

    # ── Opportunities ─────────────────────────────────────────────────────────

    transport_score = score_breakdown.get("transport_access", 0)
    if transport_score >= 6:
        evidence_parts = []
        if bus_stops:
            evidence_parts.append(f"{len(bus_stops)} bus stops")
        if metro:
            evidence_parts.append(f"{len(metro)} metro/subway points")
        if railway_stations:
            evidence_parts.append(f"Railway {railway_stations[0].get('distance_km', '?')} km away")
        opportunities.append({
            "title": "Strong public transit access",
            "evidence": ", ".join(evidence_parts) or "Good transport score",
            "recommendation": "Suitable for walk-in retail, F&B, and daily services",
        })

    demo = demographics or {}
    literacy = demo.get("literacy_rate")
    urban_pct = demo.get("urban_pct")
    if literacy and literacy > 85 and urban_pct and urban_pct > 70:
        opportunities.append({
            "title": "Educated urban demographic",
            "evidence": f"Literacy {literacy:.1f}%, urban {urban_pct:.0f}%",
            "recommendation": "Premium and knowledge-economy businesses may perform well",
        })

    if len(hospitals) >= 3 or total_amenities > 40:
        opportunities.append({
            "title": "High amenity density",
            "evidence": f"{total_amenities} total amenities including {len(hospitals)} hospitals",
            "recommendation": "High footfall catchment; anchor businesses likely to thrive",
        })

    msme_top = [s.get("sector_name") for s in (msme_sectors or [])[:3] if s.get("sector_name")]
    if msme_top:
        opportunities.append({
            "title": "Active local business ecosystem",
            "evidence": f"Top MSME sectors: {', '.join(msme_top)}",
            "recommendation": "Synergies possible with existing local sector",
        })

    # ── Best use cases ────────────────────────────────────────────────────────

    if len(hospitals) >= 2 or len(pharmacies) >= 3:
        best_use_cases.append("clinic/diagnostics")
        best_use_cases.append("pharmacy")

    if len(schools) >= 3 or len(housing) >= 5:
        best_use_cases.append("education services")
        best_use_cases.append("family grocery")

    if transport_score >= 6 and total_amenities >= 20:
        best_use_cases.append("retail")
        best_use_cases.append("quick-service restaurant")

    if len(corporates) >= 3 or (msme_top and any("IT" in s or "Software" in s for s in msme_top)):
        best_use_cases.append("cafe/co-working")
        best_use_cases.append("B2B services")

    if not best_use_cases:
        best_use_cases.append("mixed-use / evaluate further")

    # ── Next questions ────────────────────────────────────────────────────────

    next_questions = ["What business type are you evaluating?"]
    if len(best_use_cases) > 1:
        next_questions.append(f"Are you targeting {best_use_cases[0]} or {best_use_cases[1]}?")
    if aqi_val and aqi_val > 100:
        next_questions.append("Do air quality restrictions affect your business category?")
    if score_breakdown.get("transport_access", 5) < 5:
        next_questions.append("Do you rely on walk-in traffic or destination visits?")
    next_questions.append("Do you care more about footfall or affluent demographics?")

    # ── Summary ───────────────────────────────────────────────────────────────

    score_label = (
        "excellent" if viability_score >= 8 else
        "good" if viability_score >= 6.5 else
        "average" if viability_score >= 4 else
        "poor"
    )
    summary = (
        f"This location scores {viability_score}/10 ({score_label}) for commercial viability. "
        f"{'Strong' if transport_score >= 6 else 'Limited'} transit access, "
        f"{'good' if not aqi_val or aqi_val < 100 else 'concerning'} air quality, "
        f"and {total_amenities} nearby amenities. "
        f"Best suited for: {', '.join(best_use_cases[:3])}."
    )

    # ── Confidence ────────────────────────────────────────────────────────────

    confidence = 0.8
    if fallback_used:
        confidence -= 0.1
    confidence -= len(missing_sources) * 0.05
    if poi_provider == "google":
        confidence += 0.05
    confidence = round(max(0.2, min(1.0, confidence)), 2)

    return {
        "summary": summary,
        "best_use_cases": list(dict.fromkeys(best_use_cases))[:6],  # deduplicate, cap at 6
        "risks": risks,
        "opportunities": opportunities,
        "next_questions": next_questions[:4],
        "confidence": confidence,
        "data_quality": {
            "poi_provider": poi_provider,
            "fallback_used": fallback_used,
            "missing_sources": missing_sources,
        },
    }


def summarize_report_for_agent(report: dict, max_chars: int = 30000) -> str:
    """
    Compact text summary of a full analysis report for LLM context injection.
    Keeps the most decision-relevant data; full POI lists excluded (use tools).
    """
    loc = report.get("location", {})
    breakdown = report.get("score_breakdown", {})
    demo = report.get("demographics") or {}
    aqi = report.get("aqi") or {}
    crime = report.get("crime") or {}
    airports = report.get("airports", [])
    railway = report.get("railway_stations", [])
    msme = report.get("msme_sectors", [])
    footfall = report.get("footfall_proxy") or {}
    insights = report.get("agent_insights") or {}
    poi = report.get("poi") or {}

    poi_summary = {cat: len(items) for cat, items in poi.items() if items}
    top_poi: list[str] = []
    for cat in ["hospitals", "schools", "pharmacies", "bus_stops", "metro", "banks", "supermarkets"]:
        items = poi.get(cat, [])
        if items:
            nearest = items[0]
            top_poi.append(f"  {cat}: {len(items)} found, nearest '{nearest.get('name')} {nearest.get('distance_km')} km'")

    lines = [
        f"LOCATION: {loc.get('display_address')} ({loc.get('lat')}, {loc.get('lon')})",
        f"District: {loc.get('district')}, State: {loc.get('state')}, PIN: {loc.get('pin_code')}",
        "",
        f"VIABILITY SCORE: {report.get('viability_score')}/10  (confidence: {report.get('data_confidence')})",
        "Score breakdown:",
    ] + [f"  {k}: {v}" for k, v in breakdown.items()] + [
        "",
        f"POI COUNTS: {poi_summary}",
        "Key POIs:",
    ] + top_poi + [
        "",
        f"TRANSPORT: {len(poi.get('bus_stops', []))} bus stops, "
        f"{len(poi.get('metro', []))} metro, "
        f"nearest railway: {railway[0].get('station_name') if railway else 'N/A'} "
        f"({railway[0].get('distance_km')} km)" if railway else "",
        "",
        f"AIRPORTS: " + ", ".join(f"{a.get('name')} ({a.get('iata_code')}) {a.get('distance_km')} km" for a in airports[:3]),
        "",
        f"AQI: {aqi.get('pollutant_avg')} ({aqi.get('aqi_category')}) at {aqi.get('station')}",
        f"CRIME: {crime.get('latest_crimes_per_lakh')} per lakh ({crime.get('district')}, {crime.get('state')})",
        "",
        f"DEMOGRAPHICS: Pop {demo.get('total_population')}, "
        f"Urban {demo.get('urban_pct')}%, Literacy {demo.get('literacy_rate')}%",
        "",
        f"TOP MSME SECTORS: " + ", ".join(f"{s.get('sector_name')} ({s.get('enterprise_count')})" for s in msme[:5]),
        "",
        f"INSIGHTS SUMMARY: {insights.get('summary')}",
        f"Best use cases: {', '.join(insights.get('best_use_cases', []))}",
        f"Risks: " + "; ".join(f"{r.get('severity')}: {r.get('title')}" for r in insights.get("risks", [])),
        "",
        f"PROVIDER: {report.get('provider')}  PARTIAL: {report.get('partial')}",
        f"WARNINGS: {'; '.join(report.get('warnings', [])) or 'none'}",
        f"FOOTFALL: {footfall.get('total_amenities')} amenities, score {footfall.get('poi_density_score')}",
    ]

    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n...[truncated]"
    return text
