import httpx
import asyncio
import logging
from utils.haversine import haversine

logger = logging.getLogger(__name__)

OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]
HEADERS = {"User-Agent": "IndiaLocationIntelPlatform/1.0 (contact@locationintel.dev)"}

_mirror_index = 0


def _next_mirror() -> str:
    global _mirror_index
    url = OVERPASS_MIRRORS[_mirror_index % len(OVERPASS_MIRRORS)]
    _mirror_index += 1
    return url

# 3 batched queries — each has 3-4 filter types, avoiding the 504 from a single 20-union query
BATCH_FILTERS = [
    # Batch A: healthcare + education
    {
        "filters": [
            ('["amenity"~"hospital|clinic"]', "hospitals"),
            ('["amenity"~"school|college|university"]', "schools"),
            ('["amenity"="pharmacy"]', "pharmacies"),
            ('["amenity"~"bank|atm"]', "banks"),
        ],
    },
    # Batch B: transport
    {
        "filters": [
            ('["highway"="bus_stop"]', "bus_stops"),
            ('["railway"~"station|halt"]', "railway"),
            ('["station"="subway"]', "metro"),
        ],
    },
    # Batch C: commerce + residential
    {
        "filters": [
            ('["office"~"company|it|coworking"]', "corporates"),
            ('["building"~"apartments|residential"]', "housing"),
            ('["shop"~"supermarket|mall"]', "supermarkets"),
        ],
    },
]


def _build_batch_query(lat: float, lon: float, radius_m: int, filters: list) -> str:
    unions = []
    for f, _ in filters:
        unions.append(f"node{f}(around:{radius_m},{lat},{lon});")
        unions.append(f"way{f}(around:{radius_m},{lat},{lon});")
    body = "\n  ".join(unions)
    return f"[out:json][timeout:20];\n(\n  {body}\n);\nout center tags;"


def _categorize_element(tags: dict, category_hints: list[tuple[str, str]]) -> str | None:
    """Match element tags against the category-filter pairs for a batch."""
    amenity = tags.get("amenity", "")
    highway = tags.get("highway", "")
    railway = tags.get("railway", "")
    station = tags.get("station", "")
    office = tags.get("office", "")
    building = tags.get("building", "")
    shop = tags.get("shop", "")

    for _, cat in category_hints:
        if cat == "hospitals" and amenity in ("hospital", "clinic"):
            return cat
        if cat == "schools" and amenity in ("school", "college", "university"):
            return cat
        if cat == "pharmacies" and amenity == "pharmacy":
            return cat
        if cat == "banks" and amenity in ("bank", "atm"):
            return cat
        if cat == "bus_stops" and highway == "bus_stop":
            return cat
        if cat == "railway" and railway in ("station", "halt"):
            return cat
        if cat == "metro" and (station == "subway" or railway == "subway_entrance"):
            return cat
        if cat == "corporates" and office in ("company", "it", "coworking"):
            return cat
        if cat == "housing" and building in ("apartments", "residential"):
            return cat
        if cat == "supermarkets" and shop in ("supermarket", "mall"):
            return cat
    return None


def _parse_element(e: dict, origin_lat: float, origin_lon: float) -> dict:
    if e["type"] == "node":
        lat, lon = e.get("lat", 0), e.get("lon", 0)
    else:
        c = e.get("center", {})
        lat, lon = c.get("lat", 0), c.get("lon", 0)

    tags = e.get("tags", {})
    name = (tags.get("name") or tags.get("name:en")
            or tags.get("amenity") or tags.get("shop") or "Unknown")
    dist = haversine(origin_lat, origin_lon, lat, lon) if lat and lon else None

    return {
        "name": name,
        "lat": lat,
        "lon": lon,
        "distance_km": round(dist, 3) if dist else None,
        "tags": {k: v for k, v in tags.items()
                 if k in ("amenity", "shop", "office", "building", "healthcare", "name", "highway", "railway", "station")},
    }


async def _fetch_batch(lat: float, lon: float, radius_m: int, batch: dict, retries: int = 3) -> dict:
    """Fetch one batch of POI types."""
    filters = batch["filters"]
    query = _build_batch_query(lat, lon, radius_m, filters)
    results = {cat: [] for _, cat in filters}

    for attempt in range(retries):
        mirror = _next_mirror()
        try:
            async with httpx.AsyncClient(timeout=22, headers=HEADERS) as client:
                resp = await client.post(mirror, data={"data": query})
                if resp.status_code == 429:
                    logger.warning(f"Overpass 429 ({mirror}), retrying in 3s")
                    await asyncio.sleep(3)
                    continue
                if resp.status_code >= 500:
                    logger.warning(f"Overpass {resp.status_code} ({mirror}), trying next mirror")
                    continue
                resp.raise_for_status()
                elements = resp.json().get("elements", [])
            break
        except httpx.TimeoutException:
            logger.warning(f"Overpass timeout ({mirror}, attempt {attempt+1})")
            continue
        except httpx.HTTPError as e:
            logger.warning(f"Overpass error ({mirror}): {e}")
            return results
    else:
        return results

    for e in elements:
        tags = e.get("tags", {})
        cat = _categorize_element(tags, filters)
        if cat:
            results[cat].append(_parse_element(e, lat, lon))

    for cat in results:
        results[cat].sort(key=lambda x: x.get("distance_km") or 999)

    return results


async def fetch_all_poi(lat: float, lon: float, radius_m: int) -> dict:
    """Fetch all POI types in 3 concurrent batched Overpass requests (one per mirror)."""
    batch_results = await asyncio.gather(
        *[_fetch_batch(lat, lon, radius_m, batch, retries=2) for batch in BATCH_FILTERS],
        return_exceptions=True,
    )
    all_results = {}
    for result in batch_results:
        if isinstance(result, dict):
            all_results.update(result)
    return all_results


async def fetch_poi(lat: float, lon: float, radius_m: int, poi_type: str) -> list:
    """Fetch a single POI type (for /api/poi endpoint)."""
    all_poi = await fetch_all_poi(lat, lon, radius_m)
    return all_poi.get(poi_type, [])
