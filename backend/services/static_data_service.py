import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import Airport, RailwayStation, CensusData, CrimeData, MsmeData
from utils.haversine import haversine

logger = logging.getLogger(__name__)


async def get_nearest_airports(db: AsyncSession, lat: float, lon: float, limit: int = 3) -> list:
    stmt = select(Airport).where(Airport.is_operational == True)
    result = await db.execute(stmt)
    airports = result.scalars().all()

    with_dist = []
    for a in airports:
        if a.latitude and a.longitude:
            dist = haversine(lat, lon, a.latitude, a.longitude)
            with_dist.append({
                "name": a.name,
                "city": a.city,
                "iata_code": a.iata_code,
                "state": a.state,
                "distance_km": round(dist, 2),
            })

    with_dist.sort(key=lambda x: x["distance_km"])
    return with_dist[:limit]


async def get_nearest_railway(db: AsyncSession, lat: float, lon: float, limit: int = 5) -> list:
    stmt = select(RailwayStation).where(
        RailwayStation.latitude.is_not(None),
        RailwayStation.longitude.is_not(None),
    )
    result = await db.execute(stmt)
    stations = result.scalars().all()

    with_dist = []
    for s in stations:
        if s.latitude and s.longitude:
            dist = haversine(lat, lon, s.latitude, s.longitude)
            with_dist.append({
                "station_name": s.station_name,
                "station_code": s.station_code,
                "state": s.state,
                "distance_km": round(dist, 2),
            })

    with_dist.sort(key=lambda x: x["distance_km"])
    return with_dist[:limit]


async def get_demographics(db: AsyncSession, district: str, state: str) -> dict | None:
    stmt = select(CensusData).where(
        func.lower(CensusData.state) == func.lower(state),
        func.lower(CensusData.district).contains(func.lower(district[:6])),
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()

    if not row:
        # Fuzzy fallback — match on state only, pick first
        stmt2 = select(CensusData).where(
            func.lower(CensusData.state) == func.lower(state)
        ).limit(1)
        result2 = await db.execute(stmt2)
        row = result2.scalar_one_or_none()

    if not row:
        return None

    urban_pct = None
    if row.total_population and row.urban_population:
        urban_pct = round(row.urban_population / row.total_population * 100, 1)

    return {
        "district": row.district,
        "state": row.state,
        "total_population": row.total_population,
        "urban_population": row.urban_population,
        "rural_population": row.rural_population,
        "literacy_rate": row.literacy_rate,
        "sex_ratio": row.sex_ratio,
        "workers_total": row.workers_total,
        "urban_pct": urban_pct,
    }


async def get_crime(db: AsyncSession, district: str, state: str) -> dict | None:
    stmt = (
        select(CrimeData)
        .where(
            func.lower(CrimeData.state) == func.lower(state),
            func.lower(CrimeData.district).contains(func.lower(district[:6])),
        )
        .order_by(CrimeData.year.desc())
        .limit(5)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        stmt2 = (
            select(CrimeData)
            .where(func.lower(CrimeData.state) == func.lower(state))
            .order_by(CrimeData.year.desc())
            .limit(3)
        )
        result2 = await db.execute(stmt2)
        rows = result2.scalars().all()

    if not rows:
        return None

    records = [
        {
            "year": r.year,
            "total_ipc_crimes": r.total_ipc_crimes,
            "crimes_per_lakh": r.crimes_per_lakh,
            "property_crimes": r.property_crimes,
            "economic_offences": r.economic_offences,
        }
        for r in rows
    ]

    latest = rows[0]
    return {
        "district": latest.district,
        "state": latest.state,
        "records": records,
        "latest_crimes_per_lakh": latest.crimes_per_lakh,
    }


async def get_msme_sectors(db: AsyncSession, district: str, state: str, limit: int = 10) -> list:
    stmt = (
        select(MsmeData)
        .where(
            func.lower(MsmeData.state) == func.lower(state),
            func.lower(MsmeData.district).contains(func.lower(district[:6])),
        )
        .order_by(MsmeData.enterprise_count.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        stmt2 = (
            select(MsmeData)
            .where(func.lower(MsmeData.state) == func.lower(state))
            .order_by(MsmeData.enterprise_count.desc())
            .limit(limit)
        )
        result2 = await db.execute(stmt2)
        rows = result2.scalars().all()

    return [
        {
            "sector_name": r.sector_name or "Other",
            "nic_code": r.nic_code,
            "enterprise_count": r.enterprise_count or 0,
            "micro_count": r.micro_count,
            "small_count": r.small_count,
        }
        for r in rows
    ]
