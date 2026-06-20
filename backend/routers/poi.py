from fastapi import APIRouter, Query
from services.location_providers.hybrid import get_provider
from services.analysis_service import ALL_CATEGORIES

router = APIRouter()


@router.get("/poi")
async def get_poi(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius: float = Query(default=1.0, ge=0.5, le=5.0),
    types: str = Query(default="hospitals,schools,bus_stops"),
):
    radius_m = int(radius * 1000)
    requested = [t.strip() for t in types.split(",") if t.strip() in ALL_CATEGORIES]
    if not requested:
        return {}

    provider = get_provider()
    # Fetch all requested categories in one provider call (no duplicate fetches)
    results = await provider.fetch_poi(lat, lon, radius_m, requested)
    return results
