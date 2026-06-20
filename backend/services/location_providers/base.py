from abc import ABC, abstractmethod


class BaseLocationProvider(ABC):
    """Common interface all location providers must satisfy."""

    @abstractmethod
    async def geocode(self, query: str) -> dict:
        """Forward geocode a query string → {lat, lon, display_name, district, city, state, postcode, provider}"""

    @abstractmethod
    async def reverse_geocode(self, lat: float, lon: float) -> dict:
        """Reverse geocode coordinates → same shape as geocode()"""

    @abstractmethod
    async def fetch_poi(
        self,
        lat: float,
        lon: float,
        radius_m: int,
        categories: list[str],
    ) -> dict:
        """
        Fetch POI for the requested categories.
        Returns {category: [PoiItem-like dicts]} for every requested category.
        Categories not returned default to empty list.
        """

    async def fetch_place_details(self, place_id: str) -> dict:
        """Optional: fetch enriched details for a single place. Default: no-op."""
        return {}

    async def compute_routes(
        self,
        origin: dict,
        destinations: list[dict],
        mode: str = "DRIVE",
    ) -> list:
        """Optional: compute travel times. Default: empty list (Haversine used instead)."""
        return []

    def provider_name(self) -> str:
        return self.__class__.__name__
