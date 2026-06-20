import httpx
import logging
import os
from utils.haversine import haversine

logger = logging.getLogger(__name__)

DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY", "")
AQI_RESOURCE_ID = "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"

AQI_CATEGORIES = [
    (50, "Good"),
    (100, "Satisfactory"),
    (200, "Moderate"),
    (300, "Poor"),
    (400, "Very Poor"),
    (float("inf"), "Severe"),
]


def _categorize_aqi(value: float) -> str:
    for threshold, label in AQI_CATEGORIES:
        if value <= threshold:
            return label
    return "Severe"


async def get_nearest_aqi(lat: float, lon: float, state: str) -> dict:
    if not DATA_GOV_API_KEY:
        return {"error": "AQI service unavailable (DATA_GOV_API_KEY not set)", "station": None}
    url = f"https://api.data.gov.in/resource/{AQI_RESOURCE_ID}"
    params = {
        "api-key": DATA_GOV_API_KEY,
        "format": "json",
        "limit": 500,
        "filters[state]": state,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            stations = resp.json().get("records", [])
    except httpx.HTTPError as e:
        logger.warning(f"AQI API error: {e}")
        return {"error": "AQI service unavailable", "station": None}

    nearest = None
    min_dist = float("inf")

    for s in stations:
        try:
            s_lat = float(s.get("latitude") or s.get("station_latitude") or 0)
            s_lon = float(s.get("longitude") or s.get("station_longitude") or 0)
            if not s_lat or not s_lon:
                continue
            dist = haversine(lat, lon, s_lat, s_lon)
            avg = s.get("pollutant_avg") or s.get("avg") or 0
            if dist < min_dist and avg:
                min_dist = dist
                try:
                    aqi_val = float(avg)
                except (ValueError, TypeError):
                    aqi_val = None
                nearest = {
                    "station": s.get("station") or s.get("station_name", "Unknown"),
                    "city": s.get("city", state),
                    "pollutant_id": s.get("pollutant_id", "PM2.5"),
                    "pollutant_avg": aqi_val,
                    "aqi_category": _categorize_aqi(aqi_val) if aqi_val else "Unknown",
                    "distance_km": round(dist, 2),
                }
        except (ValueError, TypeError):
            continue

    return nearest or {"error": "No nearby AQI station found", "station": None}
