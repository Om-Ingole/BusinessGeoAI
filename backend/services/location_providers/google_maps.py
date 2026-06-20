"""
Google Maps Platform provider.
Uses httpx — no Google Maps Python SDK required.
APIs used:
  • Geocoding API          (maps.googleapis.com/maps/api/geocode/json)
  • Places API Nearby      (places.googleapis.com/v1/places:searchNearby)
  • Places Text Search     (places.googleapis.com/v1/places:searchText)
  • Routes API             (routes.googleapis.com/directions/v2:computeRoutes)
"""
import asyncio
import logging
import os
from typing import Optional

import httpx

from services.location_providers.base import BaseLocationProvider
from utils.haversine import haversine

logger = logging.getLogger(__name__)

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACES_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
PLACES_TEXT_URL = "https://places.googleapis.com/v1/places:searchText"
ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

MAX_RESULTS = int(os.getenv("GOOGLE_PLACES_MAX_RESULTS_PER_TYPE", "20"))
ENABLE_DETAILS = os.getenv("GOOGLE_PLACES_ENABLE_DETAILS", "false").lower() == "true"

DEFAULT_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,"
    "places.location,places.primaryType,places.types,"
    "places.businessStatus,places.rating,places.userRatingCount,"
    "places.googleMapsUri"
)

# Maps our internal category names → Google Place types
GOOGLE_PLACE_TYPE_MAP: dict[str, list[str]] = {
    "hospitals": ["hospital", "doctor", "health"],
    "schools": ["school", "university"],
    "bus_stops": ["bus_station"],
    "railway": ["train_station"],
    "metro": ["subway_station", "transit_station"],
    "pharmacies": ["pharmacy"],
    "banks": ["bank", "atm"],
    "supermarkets": ["supermarket", "shopping_mall", "grocery_store"],
}

# Categories better served by OSM; we skip Google for these
OSM_PREFERRED = {"housing", "corporates"}

# Text search queries for categories Google doesn't have explicit types for
TEXT_SEARCH_QUERIES: dict[str, list[str]] = {
    "corporates": [
        "corporate office near {lat},{lon}",
        "IT company near {lat},{lon}",
        "coworking space near {lat},{lon}",
    ],
}


class GoogleMapsProvider(BaseLocationProvider):
    def __init__(self, api_key: str):
        self._key = api_key

    def provider_name(self) -> str:
        return "google"

    # ── Geocoding ─────────────────────────────────────────────────────────────

    async def geocode(self, query: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                GEOCODE_URL,
                params={"address": query, "region": "in", "key": self._key},
            )
            resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "OK" or not data.get("results"):
            raise ValueError(f"Google geocode failed for '{query}': {data.get('status')}")
        return self._parse_geocode_result(data["results"][0])

    async def reverse_geocode(self, lat: float, lon: float) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                GEOCODE_URL,
                params={"latlng": f"{lat},{lon}", "key": self._key},
            )
            resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "OK" or not data.get("results"):
            raise ValueError(f"Google reverse geocode failed for {lat},{lon}")
        return self._parse_geocode_result(data["results"][0])

    def _parse_geocode_result(self, result: dict) -> dict:
        loc = result["geometry"]["location"]
        components = {c["types"][0]: c["long_name"] for c in result.get("address_components", []) if c.get("types")}
        return {
            "lat": loc["lat"],
            "lon": loc["lng"],
            "display_name": result.get("formatted_address", ""),
            "district": (
                components.get("administrative_area_level_3")
                or components.get("administrative_area_level_2")
                or components.get("locality")
            ),
            "city": components.get("locality") or components.get("administrative_area_level_2"),
            "state": components.get("administrative_area_level_1"),
            "postcode": components.get("postal_code"),
            "country": components.get("country", "India"),
            "provider": "google",
        }

    # ── POI ───────────────────────────────────────────────────────────────────

    async def fetch_poi(
        self,
        lat: float,
        lon: float,
        radius_m: int,
        categories: list[str],
    ) -> dict:
        results: dict[str, list] = {cat: [] for cat in categories}
        tasks = []

        for cat in categories:
            if cat in OSM_PREFERRED:
                continue  # caller (hybrid) will fill these from OSM
            if cat in GOOGLE_PLACE_TYPE_MAP:
                tasks.append((cat, self._fetch_nearby(lat, lon, radius_m, cat)))
            elif cat in TEXT_SEARCH_QUERIES:
                tasks.append((cat, self._fetch_text_search(lat, lon, radius_m, cat)))

        # Run category fetches concurrently
        if tasks:
            fetched = await asyncio.gather(*[t for _, t in tasks], return_exceptions=True)
            for (cat, _), items in zip(tasks, fetched):
                if isinstance(items, Exception):
                    logger.warning(f"Google Places fetch failed for '{cat}': {items}")
                else:
                    results[cat] = items

        return results

    async def _fetch_nearby(self, lat: float, lon: float, radius_m: int, category: str) -> list:
        place_types = GOOGLE_PLACE_TYPE_MAP[category]
        headers = {
            "X-Goog-Api-Key": self._key,
            "X-Goog-FieldMask": DEFAULT_FIELD_MASK,
            "Content-Type": "application/json",
        }
        body = {
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": float(radius_m),
                }
            },
            "includedTypes": place_types,
            "maxResultCount": min(MAX_RESULTS, 20),
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(PLACES_NEARBY_URL, headers=headers, json=body)
            if resp.status_code == 429:
                raise RuntimeError("Google Places quota exceeded")
            resp.raise_for_status()
        places = resp.json().get("places", [])
        return [self._normalize_place(p, lat, lon) for p in places]

    async def _fetch_text_search(self, lat: float, lon: float, radius_m: int, category: str) -> list:
        queries = TEXT_SEARCH_QUERIES.get(category, [])
        all_results: list = []
        headers = {
            "X-Goog-Api-Key": self._key,
            "X-Goog-FieldMask": DEFAULT_FIELD_MASK,
            "Content-Type": "application/json",
        }
        for q_template in queries[:2]:  # limit to 2 text search queries per category
            query = q_template.format(lat=lat, lon=lon)
            body = {
                "textQuery": query,
                "locationBias": {
                    "circle": {
                        "center": {"latitude": lat, "longitude": lon},
                        "radius": float(radius_m),
                    }
                },
                "maxResultCount": 10,
            }
            try:
                async with httpx.AsyncClient(timeout=20) as client:
                    resp = await client.post(PLACES_TEXT_URL, headers=headers, json=body)
                    resp.raise_for_status()
                places = resp.json().get("places", [])
                all_results.extend([self._normalize_place(p, lat, lon) for p in places])
            except httpx.HTTPError as e:
                logger.warning(f"Text search failed for '{query}': {e}")
        # Deduplicate by id
        seen = set()
        unique = []
        for p in all_results:
            if p["id"] not in seen:
                seen.add(p["id"])
                unique.append(p)
        return unique

    def _normalize_place(self, place: dict, origin_lat: float, origin_lon: float) -> dict:
        loc = place.get("location", {})
        p_lat = loc.get("latitude", 0)
        p_lon = loc.get("longitude", 0)
        dist = haversine(origin_lat, origin_lon, p_lat, p_lon) if p_lat and p_lon else None
        return {
            "id": place.get("id", ""),
            "provider": "google",
            "name": place.get("displayName", {}).get("text", "Unknown"),
            "lat": p_lat,
            "lon": p_lon,
            "distance_km": round(dist, 3) if dist is not None else None,
            "rating": place.get("rating"),
            "user_rating_count": place.get("userRatingCount"),
            "business_status": place.get("businessStatus"),
            "address": place.get("formattedAddress"),
            "google_maps_uri": place.get("googleMapsUri"),
            "types": place.get("types", []),
            "tags": {},
        }

    # ── Routes ────────────────────────────────────────────────────────────────

    async def compute_routes(
        self,
        origin: dict,
        destinations: list[dict],
        mode: str = "DRIVE",
    ) -> list:
        results = []
        for dest in destinations[:10]:  # cap to 10 destinations per call
            try:
                route = await self._compute_single_route(origin, dest, mode)
                results.append(route)
            except Exception as e:
                logger.warning(f"Route computation failed for {dest}: {e}")
                # Fallback to Haversine
                dist = haversine(
                    origin["lat"], origin["lon"],
                    dest["lat"], dest["lon"],
                )
                results.append({
                    "destination_name": dest.get("name", ""),
                    "distance_km": round(dist, 2),
                    "duration_minutes": None,
                    "mode": mode,
                    "fallback": True,
                })
        return results

    async def _compute_single_route(self, origin: dict, dest: dict, mode: str) -> dict:
        body = {
            "origin": {"location": {"latLng": {"latitude": origin["lat"], "longitude": origin["lon"]}}},
            "destination": {"location": {"latLng": {"latitude": dest["lat"], "longitude": dest["lon"]}}},
            "travelMode": mode,
        }
        headers = {
            "X-Goog-Api-Key": self._key,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(ROUTES_URL, headers=headers, json=body)
            resp.raise_for_status()
        routes = resp.json().get("routes", [])
        if not routes:
            raise ValueError("No routes returned")
        r = routes[0]
        duration_s = int(r.get("duration", "0s").rstrip("s") or 0)
        return {
            "destination_name": dest.get("name", ""),
            "distance_km": round(r.get("distanceMeters", 0) / 1000, 2),
            "duration_minutes": round(duration_s / 60, 1),
            "mode": mode,
            "fallback": False,
        }
