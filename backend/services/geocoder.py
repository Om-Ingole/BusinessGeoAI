import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
HEADERS = {"User-Agent": "IndiaLocationIntelPlatform/1.0 (contact@locationintel.dev)"}


async def geocode(query: str, retries: int = 3) -> dict:
    params = {
        "q": query,
        "countrycodes": "in",
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    for attempt in range(retries):
        await asyncio.sleep(1)  # Nominatim rate limit: 1 req/sec
        try:
            async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
                resp = await client.get(NOMINATIM_URL, params=params)
                resp.raise_for_status()
                results = resp.json()
            if results:
                return _parse_result(results[0])
        except httpx.HTTPError as e:
            logger.warning(f"Nominatim attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
    raise ValueError(f"Could not geocode: {query}")


async def reverse_geocode(lat: float, lon: float) -> dict:
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1,
        "zoom": 14,
    }
    await asyncio.sleep(1)
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            resp = await client.get(NOMINATIM_REVERSE_URL, params=params)
            resp.raise_for_status()
            result = resp.json()
        return _parse_result(result)
    except httpx.HTTPError as e:
        logger.warning(f"Reverse geocode failed: {e}")
        return {"lat": lat, "lon": lon, "display_name": f"{lat},{lon}"}


def _parse_result(r: dict) -> dict:
    addr = r.get("address", {})
    return {
        "lat": float(r["lat"]) if "lat" in r else float(r.get("lat", 0)),
        "lon": float(r["lon"]) if "lon" in r else float(r.get("lon", 0)),
        "display_name": r.get("display_name", ""),
        "district": (addr.get("county")
                     or addr.get("city_district")
                     or addr.get("district")
                     or addr.get("suburb")
                     or addr.get("city")),
        "city": addr.get("city") or addr.get("town") or addr.get("village"),
        "state": addr.get("state"),
        "postcode": addr.get("postcode"),
        "country": addr.get("country_code", "in").upper(),
    }
