import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db import get_db
from app.schemas import TripOut
from app.trips.service import get_trip_by_dispatch

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("/{dispatch_id}", response_model=TripOut)
async def get_trip(
    dispatch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
) -> TripOut:
    trip = await get_trip_by_dispatch(db, dispatch_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TRIP_NOT_FOUND")
    return TripOut(
        id=trip.id,
        dispatchId=trip.dispatch_id,
        junctionsCleared=trip.junctions_cleared,
        arbitrationsInvolved=trip.arbitrations_involved,
        declinedHospitalIds=trip.declined_hospital_ids,
        route=trip.route,
        startedAt=trip.started_at,
        pickedUpAt=trip.picked_up_at,
        completedAt=trip.completed_at,
    )
