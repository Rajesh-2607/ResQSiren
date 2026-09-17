import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_role
from app.db import get_db
from app.dispatch import service as dispatch_service
from app.models import Call, Dispatch, DispatchStatus, HospitalResponse, Trip
from app.realtime.sio import emit_event
from app.redis_client import redis
from app.schemas import DispatchCreate, DispatchOut, HospitalResponseRequest, LocationOut, LocationUpdate

router = APIRouter(prefix="/dispatch", tags=["dispatch"])

LOCATION_TTL_SECONDS = 30


def _location_key(dispatch_id: uuid.UUID) -> str:
    return f"dispatch:{dispatch_id}:location"


@router.post("", response_model=DispatchOut)
async def create_dispatch(
    body: DispatchCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("dispatcher", "admin")),
) -> DispatchOut:
    origin: tuple[float | None, float | None] = (body.originLat, body.originLng)
    if body.callId is not None and (origin[0] is None or origin[1] is None):
        call = await db.get(Call, body.callId)
        if call is not None:
            origin = (call.origin_lat, call.origin_lng)

    dispatch, route = await dispatch_service.create_dispatch(
        db,
        ambulance_id=body.ambulanceId,
        severity=body.severity,
        hospital_id=body.hospitalId,
        call_id=body.callId,
        origin=origin,
        notify_phone=body.notifyPhone,
    )

    return DispatchOut(
        id=dispatch.id,
        ambulanceId=dispatch.ambulance_id,
        severity=dispatch.severity,
        hospitalId=dispatch.hospital_id,
        status=dispatch.status.value,
        hospitalResponse=dispatch.hospital_response.value,
        createdAt=dispatch.created_at,
        route=route,
    )


@router.post("/{dispatch_id}/complete")
async def complete_dispatch(
    dispatch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("hospital", "dispatcher", "admin")),
) -> dict:
    dispatch = await db.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UNKNOWN_DISPATCH")

    dispatch.status = DispatchStatus.COMPLETED
    result = await db.execute(select(Trip).where(Trip.dispatch_id == dispatch_id))
    trip = result.scalar_one_or_none()
    if trip is not None:
        trip.completed_at = datetime.now(timezone.utc)
    await db.commit()

    await emit_event("dispatch:completed", {"id": str(dispatch_id)})
    return {"id": str(dispatch_id), "status": "COMPLETED"}


@router.post("/{dispatch_id}/respond")
async def respond_to_dispatch(
    dispatch_id: uuid.UUID,
    body: HospitalResponseRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("hospital", "admin")),
) -> dict:
    dispatch = await db.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UNKNOWN_DISPATCH")

    if body.decision == "ACCEPT":
        dispatch.hospital_response = HospitalResponse.ACCEPTED
        await db.commit()
        await emit_event(
            "hospital:responded",
            {"id": str(dispatch_id), "decision": "ACCEPT", "hospitalId": dispatch.hospital_id},
        )
        return {"id": str(dispatch_id), "hospitalResponse": "ACCEPTED", "hospitalId": dispatch.hospital_id}

    declining_hospital_id = dispatch.hospital_id
    dispatch.hospital_response = HospitalResponse.DECLINED
    await db.commit()
    await emit_event(
        "hospital:responded",
        {"id": str(dispatch_id), "decision": "DECLINE", "hospitalId": declining_hospital_id},
    )

    try:
        result = await dispatch_service.reroute_hospital(db, dispatch)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="NO_HOSPITAL_AVAILABLE")

    return {"id": str(dispatch_id), "hospitalResponse": "DECLINED", **result}


@router.post("/{dispatch_id}/arrived")
async def mark_arrived(
    dispatch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Public — the driver-tracker page has no account, same as /location.
    Marks patient pickup and sends the hospital a detailed report (fuller
    than the advance alert sent at dispatch time). Idempotent — calling it
    again after pickup is already recorded just returns the existing time.
    """
    dispatch = await db.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UNKNOWN_DISPATCH")

    result = await db.execute(select(Trip).where(Trip.dispatch_id == dispatch_id))
    trip = result.scalar_one_or_none()
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TRIP_NOT_FOUND")

    if trip.picked_up_at is None:
        trip.picked_up_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(trip)

        call = await db.get(Call, dispatch.call_id) if dispatch.call_id is not None else None
        await dispatch_service.email_arrival_report(db, dispatch=dispatch, trip=trip, call=call, picked_up_at=trip.picked_up_at)

        await emit_event("dispatch:arrived", {"id": str(dispatch_id), "pickedUpAt": trip.picked_up_at.isoformat()})

    return {"id": str(dispatch_id), "pickedUpAt": trip.picked_up_at.isoformat()}


@router.post("/{dispatch_id}/location")
async def post_location(
    dispatch_id: uuid.UUID,
    body: LocationUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Public — the driver-tracker page has no account. Called frequently
    from a real browser GPS feed, so this stays intentionally lightweight
    (no auth, no heavy validation) and just relays to Redis + Socket.IO.
    """
    dispatch = await db.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UNKNOWN_DISPATCH")

    payload = {"lat": body.lat, "lng": body.lng, "updatedAt": datetime.now(timezone.utc).isoformat()}
    await redis.set(_location_key(dispatch_id), json.dumps(payload), ex=LOCATION_TTL_SECONDS)

    await emit_event("location:update", {"dispatchId": str(dispatch_id), **payload})
    return {"ok": True}


@router.get("/{dispatch_id}/location", response_model=LocationOut)
async def get_location(dispatch_id: uuid.UUID) -> LocationOut:
    raw = await redis.get(_location_key(dispatch_id))
    if raw is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NO_LOCATION")
    return LocationOut(**json.loads(raw))
