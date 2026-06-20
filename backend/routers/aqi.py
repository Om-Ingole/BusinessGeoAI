from fastapi import APIRouter, Path, Query
from services.aqi_service import get_nearest_aqi

router = APIRouter()


@router.get("/aqi/{state}")
async def get_aqi(
    state: str = Path(...),
    lat: float = Query(...),
    lon: float = Query(...),
):
    return await get_nearest_aqi(lat, lon, state)
