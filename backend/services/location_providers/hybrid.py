"""
Hybrid provider: Google Maps first, OSM fallback.
Controlled by LOCATION_PROVIDER env var: google | osm | hybrid (default).
"""
import logging
import os

import httpx

from services.location_providers.base import BaseLocationProvider
from services.location_providers.osm import OSMProvider

logger = logging.getLogger(__name__)

# Categories where OSM is always preferred over Google
OSM_PREFERRED_CATEGORIES = {"housing"}


def get_provider() -> BaseLocationProvider:
    """Factory: return the configured provider singleton."""
    mode = os.getenv("LOCATION_PROVIDER", "hybrid").lower()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")

    if mode == "osm" or not api_key:
        return OSMProvider()

    from services.location_providers.google_maps import GoogleMapsProvider
    google = GoogleMapsProvider(api_key)

    if mode == "google":
        return google

    # hybrid
    return HybridProvider(google, OSMProvider())


class HybridProvider(BaseLocationProvider):
    """
    Tries Google first for geocoding and POI.
    Falls back to OSM on quota errors, network failures, or missing key.
    Always uses OSM for housing category.
    """

    def __init__(self, google: BaseLocationProvider, osm: BaseLocationProvider):
        self._google = google
        self._osm = osm
        self._fallback_used = False

    def provider_name(self) -> str:
        return "hybrid"

    async def geocode(self, query: str) -> dict:
        try:
            result = await self._google.geocode(query)
            result["provider"] = "google"
            return result
        except Exception as e:
            logger.warning(f"Google geocode failed, falling back to OSM: {e}")
            result = await self._osm.geocode(query)
            result["provider"] = "osm"
            result["fallback"] = True
            return result

    async def reverse_geocode(self, lat: float, lon: float) -> dict:
        try:
            result = await self._google.reverse_geocode(lat, lon)
            result["provider"] = "google"
            return result
        except Exception as e:
            logger.warning(f"Google reverse geocode failed, falling back to OSM: {e}")
            result = await self._osm.reverse_geocode(lat, lon)
            result["provider"] = "osm"
            result["fallback"] = True
            return result

    async def fetch_poi(
        self,
        lat: float,
        lon: float,
        radius_m: int,
        categories: list[str],
    ) -> dict:
        google_cats = [c for c in categories if c not in OSM_PREFERRED_CATEGORIES]
        osm_cats = [c for c in categories if c in OSM_PREFERRED_CATEGORIES]

        results: dict[str, list] = {cat: [] for cat in categories}

        # Google fetch (non-OSM-preferred categories)
        if google_cats:
            try:
                google_results = await self._google.fetch_poi(lat, lon, radius_m, google_cats)
                results.update(google_results)
            except (httpx.HTTPStatusError, RuntimeError) as e:
                logger.warning(f"Google POI fetch failed ({e}), falling back to OSM for all categories")
                osm_cats = categories  # full OSM fallback

        # OSM fetch (OSM-preferred + fallback)
        if osm_cats:
            try:
                osm_results = await self._osm.fetch_poi(lat, lon, radius_m, osm_cats)
                results.update(osm_results)
            except Exception as e:
                logger.warning(f"OSM POI fetch also failed: {e}")

        return results

    async def compute_routes(self, origin: dict, destinations: list[dict], mode: str = "DRIVE") -> list:
        return await self._google.compute_routes(origin, destinations, mode)
