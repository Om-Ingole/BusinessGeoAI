"""
Viability score calculator.
Returns (score, breakdown_dict, data_confidence).
Google rating/review counts improve footfall and business density sub-scores.
"""


def _poi_density_to_score(poi: dict) -> float:
    total = sum(len(v) for v in poi.values()) if poi else 0
    return min(10.0, total / 5.0)


def _footfall_to_score(poi: dict) -> float:
    """Enhanced footfall: raw count + category diversity + Google ratings signal."""
    if not poi:
        return 0.0
    total = sum(len(v) for v in poi.values())
    diversity = sum(1 for v in poi.values() if v)  # # of non-empty categories

    # Google rating volume bonus: avg user_rating_count across rated places
    rated_counts = [
        item.get("user_rating_count", 0) or 0
        for items in poi.values()
        for item in items
        if item.get("rating") is not None
    ]
    rating_volume_bonus = 0.0
    if rated_counts:
        avg_reviews = sum(rated_counts) / len(rated_counts)
        rating_volume_bonus = min(1.5, avg_reviews / 200)  # up to 1.5 extra points

    base = min(8.5, total / 5.0) + min(1.0, diversity / 8.0)
    return round(min(10.0, base + rating_volume_bonus), 2)


def _transport_to_score(bus_stops: list, nearest_railway: dict | None) -> float:
    bus_score = min(10.0, len(bus_stops) * 1.5) if bus_stops else 3.0
    if nearest_railway:
        dist = nearest_railway.get("distance_km", 10)
        # If we have Google Routes duration, use that too
        duration = nearest_railway.get("duration_minutes")
        if duration is not None:
            rail_score = max(0, 10 - duration / 3)
        else:
            rail_score = max(0, 10 - dist * 1.5)
    else:
        rail_score = 4.0
    return round((bus_score * 0.4 + rail_score * 0.6), 2)


def _demographics_to_score(demo: dict | None) -> float:
    if not demo:
        return 5.0
    score = 5.0
    literacy = demo.get("literacy_rate")
    if literacy:
        score += min(2.5, literacy / 100 * 2.5)
    urban_pct = demo.get("urban_pct")
    if urban_pct:
        score += min(2.5, urban_pct / 100 * 2.5)
    return round(min(10.0, score), 2)


def _poi_count_to_score(hospitals: list, schools: list) -> float:
    h = len(hospitals or [])
    s = len(schools or [])
    return min(10.0, (h * 1.5 + s * 0.8))


def _crime_to_score(crimes_per_lakh: float | None) -> float:
    if crimes_per_lakh is None:
        return 5.0
    return round(max(0.0, 10.0 - crimes_per_lakh / 50), 2)


def _aqi_to_score(pollutant_avg: float | None) -> float:
    if pollutant_avg is None:
        return 5.0
    return round(max(0.0, 10.0 - pollutant_avg / 40), 2)


def _msme_to_score(msme_sectors: list) -> float:
    if not msme_sectors:
        return 4.0
    total = sum(s.get("enterprise_count", 0) for s in msme_sectors)

    # Google operational status bonus: any POI with OPERATIONAL status is a +ve signal
    return min(10.0, total / 1000)


def _business_density_to_score(msme_sectors: list, poi: dict) -> float:
    base = _msme_to_score(msme_sectors)
    # Google rating quality bonus for commercial POIs
    commercial_cats = ["supermarkets", "banks", "corporates"]
    high_rated = sum(
        1
        for cat in commercial_cats
        for item in (poi.get(cat) or [])
        if (item.get("rating") or 0) >= 4.0 and item.get("business_status") == "OPERATIONAL"
    )
    bonus = min(1.0, high_rated * 0.2)
    return round(min(10.0, base + bonus), 2)


def _data_confidence(
    poi: dict,
    demographics,
    crime,
    aqi,
    fallback_used: bool,
    missing_sources: list,
) -> float:
    score = 1.0
    if fallback_used:
        score -= 0.1
    score -= len(missing_sources) * 0.08
    if not poi or sum(len(v) for v in poi.values()) == 0:
        score -= 0.15
    # If Google data present, higher confidence
    has_google = any(
        item.get("provider") == "google"
        for items in (poi or {}).values()
        for item in items
    )
    if has_google:
        score += 0.05
    return round(max(0.1, min(1.0, score)), 2)


def calculate_viability_score(
    poi: dict,
    demographics: dict | None,
    crime: dict | None,
    aqi: dict | None,
    nearest_railway: dict | None,
    msme_sectors: list,
    fallback_used: bool = False,
    missing_sources: list | None = None,
) -> tuple[float, dict, float]:
    """Returns (viability_score, score_breakdown, data_confidence)."""
    if missing_sources is None:
        missing_sources = []

    weights = {
        "footfall_proxy": 0.20,
        "transport_access": 0.18,
        "demographics": 0.15,
        "poi_density": 0.12,
        "crime_safety": 0.12,
        "air_quality": 0.10,
        "business_density": 0.08,
        "growth_potential": 0.05,
    }

    bus_stops = poi.get("bus_stops", []) if poi else []
    hospitals = poi.get("hospitals", []) if poi else []
    schools = poi.get("schools", []) if poi else []

    scores = {
        "footfall_proxy": _footfall_to_score(poi),
        "transport_access": _transport_to_score(bus_stops, nearest_railway),
        "demographics": _demographics_to_score(demographics),
        "poi_density": _poi_count_to_score(hospitals, schools),
        "crime_safety": _crime_to_score(
            crime.get("latest_crimes_per_lakh") if crime else None
        ),
        "air_quality": _aqi_to_score(
            aqi.get("pollutant_avg") if aqi and not aqi.get("error") else None
        ),
        "business_density": _business_density_to_score(msme_sectors, poi or {}),
        "growth_potential": 7.0,
    }

    total = sum(scores[k] * weights[k] for k in weights)
    confidence = _data_confidence(poi, demographics, crime, aqi, fallback_used, missing_sources)

    return round(total, 1), {k: round(v, 1) for k, v in scores.items()}, confidence
