from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.dispatch import service as dispatch_service
from app.emergency.summary_service import generate_patient_summary
from app.models import Call, Dispatch, Severity
from app.routing import service as routing_service

SYMPTOM_TO_SEVERITY: dict[str, Severity] = {
    "CARDIAC_OR_UNCONSCIOUS": Severity.RED,
    "SEVERE_BLEEDING_OR_FRACTURE": Severity.AMBER,
    "STABLE_NON_URGENT": Severity.GREEN,
}

SYMPTOM_LABELS: dict[str, str] = {
    "CARDIAC_OR_UNCONSCIOUS": "Chest pain / unconscious / severe trauma",
    "SEVERE_BLEEDING_OR_FRACTURE": "Serious injury / heavy bleeding / fracture",
    "STABLE_NON_URGENT": "Stable / non-urgent transport",
}


class NoAmbulanceAvailable(Exception):
    pass


class NoHospitalAvailable(Exception):
    pass


async def create_emergency(
    db: AsyncSession, *, symptom: str, lat: float, lng: float, notes: str | None
) -> tuple[Call, Dispatch, dict | None]:
    severity = SYMPTOM_TO_SEVERITY[symptom]
    origin = (lat, lng)

    available = await dispatch_service.available_ambulance_ids(db)
    ambulance_id = routing_service.nearest(
        origin,
        {aid: coords for aid, coords in routing_service.AMBULANCES.items() if aid in available},
    )
    if ambulance_id is None:
        raise NoAmbulanceAvailable()

    hospitals = await routing_service.list_emergency_hospitals(db)
    hospital_id = routing_service.nearest(origin, hospitals)
    if hospital_id is None:
        raise NoHospitalAvailable()

    reported_at = datetime.now(timezone.utc)
    summary = await generate_patient_summary(
        symptom_label=SYMPTOM_LABELS[symptom],
        severity=severity.value,
        location=f"({lat:.4f}, {lng:.4f})",
        notes=notes,
        reported_at=reported_at,
    )

    call = Call(
        location="caller-reported location",
        origin_lat=lat,
        origin_lng=lng,
        hospital_id=hospital_id,
        severity=severity,
        notes=notes,
        patient_summary=summary,
    )
    db.add(call)
    await db.flush()

    dispatch, route = await dispatch_service.create_dispatch(
        db,
        ambulance_id=ambulance_id,
        severity=severity,
        hospital_id=hospital_id,
        call_id=call.id,
        origin=origin,
        notify_phone=None,
        patient_summary=summary,
    )

    return call, dispatch, route
