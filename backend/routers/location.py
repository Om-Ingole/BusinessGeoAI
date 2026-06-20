import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal, get_db
from schemas import AnalyzeRequest, AnalyzeResponse
from services import cache_service
from services.analysis_service import analyze_location

logger = logging.getLogger(__name__)
router = APIRouter()


async def _write_cache_fresh(query_hash: str, lat: float, lon: float,
                              address: str, district: str, state: str, result: dict):
    """Open a fresh DB session for background cache write (avoids session lifecycle issues)."""
    async with AsyncSessionLocal() as db:
        await cache_service.set_cache(db, query_hash, lat, lon, address, district, state, result)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_location_endpoint(
    req: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await analyze_location(req, db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Only write cache for fresh (non-cached) results
    if not result.get("_from_cache"):
        loc = result.get("location", {})
        query_hash = cache_service.make_hash(
            loc.get("lat", 0), loc.get("lon", 0),
            req.radius_km,
        )
        background_tasks.add_task(
            _write_cache_fresh,
            query_hash,
            loc.get("lat", 0),
            loc.get("lon", 0),
            loc.get("display_address", ""),
            loc.get("district", ""),
            loc.get("state", ""),
            result,
        )

    return result


@router.get("/reports/history")
async def get_history(db: AsyncSession = Depends(get_db)):
    return await cache_service.get_history(db)
