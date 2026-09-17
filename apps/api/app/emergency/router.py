import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.emergency import service as emergency_service
from app.models import Dispatch
from app.schemas import EmergencyRequest, EmergencyResponseOut, EmergencyStatusOut
from app.trips.service import get_trip_by_dispatch

router = APIRouter(prefix="/emergency", tags=["emergency"])


@router.post("", response_model=EmergencyResponseOut)
async def report_emergency(
    body: EmergencyRequest,
    db: AsyncSession = Depends(get_db),
) -> EmergencyResponseOut:
    """Public — no login. 'I tell ResQ what happened and where I am.'"""
    try:
        call, dispatch, route = await emergency_service.create_emergency(
            db, symptom=body.symptom, lat=body.lat, lng=body.lng, notes=body.notes
        )
    except emergency_service.NoAmbulanceAvailable:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="NO_AMBULANCE_AVAILABLE")
    except emergency_service.NoHospitalAvailable:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="NO_HOSPITAL_AVAILABLE")

    return EmergencyResponseOut(
        callId=call.id,
        dispatchId=dispatch.id,
        ambulanceId=dispatch.ambulance_id,
        hospitalId=dispatch.hospital_id,
        severity=dispatch.severity,
        route=route,
        patientSummary=call.patient_summary,
    )


@router.get("/{dispatch_id}", response_model=EmergencyStatusOut)
async def emergency_status(dispatch_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> EmergencyStatusOut:
    """Public — lets the caller's browser poll/refresh status without a login."""
    dispatch = await db.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UNKNOWN_DISPATCH")
    trip = await get_trip_by_dispatch(db, dispatch_id)

    return EmergencyStatusOut(
        dispatchId=dispatch.id,
        ambulanceId=dispatch.ambulance_id,
        hospitalId=dispatch.hospital_id,
        severity=dispatch.severity,
        status=dispatch.status.value,
        hospitalResponse=dispatch.hospital_response.value,
        route=trip.route if trip else None,
    )
