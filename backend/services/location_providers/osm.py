"""OpenStreetMap provider — wraps existing Nominatim + Overpass services."""
import logging
from services.location_providers.base import BaseLocationProvider
from services import geocoder, overpass

logger = logging.getLogger(__name__)

ALL_CATEGORIES = [
    "hospitals", "schools", "bus_stops", "railway", "metro",
    "corporates", "housing", "pharmacies", "banks", "supermarkets",
]


class OSMProvider(BaseLocationProvider):
    def provider_name(self) -> str:
        return "osm"

    async def geocode(self, query: str) -> dict:
        result = await geocoder.geocode(query)
        result["provider"] = "osm"
        return result

    async def reverse_geocode(self, lat: float, lon: float) -> dict:
        result = await geocoder.reverse_geocode(lat, lon)
        result["provider"] = "osm"
        return result

    async def fetch_poi(
        self,
        lat: float,
        lon: float,
        radius_m: int,
        categories: list[str],
    ) -> dict:
        all_poi = await overpass.fetch_all_poi(lat, lon, radius_m)
        # Annotate each item with provider field
        for cat, items in all_poi.items():
            for item in items:
                item.setdefault("provider", "osm")
        # Return only requested categories, defaulting missing ones to []
        return {cat: all_poi.get(cat, []) for cat in categories}
