import hashlib
import json
import logging
from datetime import datetime, timedelta
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import LocationCache

logger = logging.getLogger(__name__)
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", 24))


def make_hash(lat: float, lon: float, radius: float) -> str:
    key = f"{round(lat, 4)}:{round(lon, 4)}:{radius}"
    return hashlib.sha256(key.encode()).hexdigest()


async def get_cached(db: AsyncSession, query_hash: str) -> dict | None:
    stmt = select(LocationCache).where(LocationCache.query_hash == query_hash)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()
    if entry and entry.expires_at > datetime.utcnow():
        return json.loads(entry.result_json)
    return None


async def set_cache(db: AsyncSession, query_hash: str, lat: float, lon: float,
                    address: str, district: str, state: str, data: dict):
    stmt = select(LocationCache).where(LocationCache.query_hash == query_hash)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        existing.result_json = json.dumps(data, default=str)
        existing.expires_at = datetime.utcnow() + timedelta(hours=CACHE_TTL_HOURS)
    else:
        entry = LocationCache(
            query_hash=query_hash,
            lat=lat,
            lon=lon,
            address=address,
            district=district,
            state=state,
            result_json=json.dumps(data, default=str),
            expires_at=datetime.utcnow() + timedelta(hours=CACHE_TTL_HOURS),
        )
        db.add(entry)
    try:
        await db.commit()
    except Exception as e:
        logger.warning(f"Cache write error: {e}")
        await db.rollback()


async def get_history(db: AsyncSession, limit: int = 20) -> list:
    stmt = (
        select(LocationCache)
        .order_by(LocationCache.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()
    return [
        {
            "query_hash": e.query_hash,
            "lat": e.lat,
            "lon": e.lon,
            "address": e.address,
            "district": e.district,
            "state": e.state,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]
