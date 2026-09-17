from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.db import get_db
from app.models import Call
from app.schemas import CallCreate, CallOut

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("", response_model=CallOut)
async def create_call(
    body: CallCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("dispatcher", "admin")),
) -> CallOut:
    call = Call(
        location=body.location,
        origin_lat=body.originLat,
        origin_lng=body.originLng,
        hospital_id=body.hospitalId,
        severity=body.severity,
        notes=body.notes,
    )
    db.add(call)
    await db.commit()
    await db.refresh(call)
    return CallOut(
        id=call.id,
        location=call.location,
        originLat=call.origin_lat,
        originLng=call.origin_lng,
        hospitalId=call.hospital_id,
        severity=call.severity,
        notes=call.notes,
        createdAt=call.created_at,
    )
