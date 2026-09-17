import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Trip


async def get_trip_by_dispatch(db: AsyncSession, dispatch_id: uuid.UUID) -> Trip | None:
    result = await db.execute(select(Trip).where(Trip.dispatch_id == dispatch_id))
    return result.scalar_one_or_none()


async def append_junction_cleared(db: AsyncSession, dispatch_id: uuid.UUID, junction_id: str) -> None:
    trip = await get_trip_by_dispatch(db, dispatch_id)
    if trip is None:
        return
    trip.junctions_cleared = [*trip.junctions_cleared, {"junctionId": junction_id, "clearedAt": _now_iso()}]
    await db.commit()


async def append_arbitration(
    db: AsyncSession,
    dispatch_id: uuid.UUID,
    junction_id: str,
    reason: str,
    competitor_dispatch_id: str | None,
) -> None:
    trip = await get_trip_by_dispatch(db, dispatch_id)
    if trip is None:
        return
    entry = {
        "junctionId": junction_id,
        "reason": reason,
        "competitorDispatchId": competitor_dispatch_id,
        "decidedAt": _now_iso(),
    }
    trip.arbitrations_involved = [*trip.arbitrations_involved, entry]
    await db.commit()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
