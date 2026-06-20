from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.static_data_service import get_nearest_airports, get_nearest_railway

router = APIRouter()


@router.get("/airports/nearest")
async def nearest_airports(
    lat: float = Query(...),
    lon: float = Query(...),
    limit: int = Query(default=3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    return await get_nearest_airports(db, lat, lon, limit)


@router.get("/railway/nearest")
async def nearest_railway(
    lat: float = Query(...),
    lon: float = Query(...),
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    return await get_nearest_railway(db, lat, lon, limit)
