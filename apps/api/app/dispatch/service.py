import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dispatch import hmac_util
from app.models import Call, Dispatch, DispatchStatus, Hospital, HospitalResponse, Severity, Trip
from app.notify.service import send_email, send_sms
from app.realtime.sio import emit_event
from app.redis_client import redis
from app.routing import service as routing_service

logger = logging.getLogger("resq_siren.dispatch")


async def _email_hospital_report(
    hospital: Hospital, *, dispatch: Dispatch, route: dict | None, patient_summary: str | None
) -> None:
    if not hospital.email:
        return
    eta_note = f"ETA ~{round(route['durationSeconds'] / 60)} min ({route['distanceMeters'] / 1000:.1f} km)" if route else "ETA unavailable"
    body = (
        f"resQ Siren dispatch report\n\n"
        f"Ambulance: {dispatch.ambulance_id}\n"
        f"Severity: {dispatch.severity.value}\n"
        f"{eta_note}\n\n"
        f"Patient summary:\n{patient_summary or '(none provided)'}\n\n"
        f"Dispatch ID: {dispatch.id}"
    )
    try:
        await send_email(hospital.email, f"[resQ Siren] Incoming {dispatch.severity.value} patient — {dispatch.ambulance_id}", body)
    except Exception:
        logger.exception("Hospital report email failed for dispatch %s", dispatch.id)


async def email_arrival_report(
    db: AsyncSession, *, dispatch: Dispatch, trip: Trip, call: Call | None, picked_up_at: datetime
) -> None:
    """Sent once, when the ambulance confirms patient pickup (POST
    /dispatch/{id}/arrived) — a fuller report than the advance alert
    _email_hospital_report sends at dispatch time: confirmed pickup time,
    response duration, and (if the ambulance has reported GPS since pickup)
    a freshly recomputed ETA to the hospital from its current position
    rather than the original pickup-point estimate.
    """
    hospital = await routing_service.get_hospital(db, dispatch.hospital_id)
    if hospital is None or not hospital.email:
        return

    response_minutes = round((picked_up_at - dispatch.created_at).total_seconds() / 60)

    route = trip.route
    raw_location = await redis.get(f"dispatch:{dispatch.id}:location")
    if raw_location:
        loc = json.loads(raw_location)
        try:
            route = await routing_service.get_route((loc["lat"], loc["lng"]), (hospital.lat, hospital.lng))
        except Exception:
            logger.exception("Route recompute for arrival report failed for dispatch %s", dispatch.id)

    eta_note = (
        f"{route['distanceMeters'] / 1000:.1f} km, ETA ~{round(route['durationSeconds'] / 60)} min to {hospital.name}"
        if route
        else f"Heading to {hospital.name} — ETA unavailable"
    )
    pickup_location = f"({call.origin_lat:.4f}, {call.origin_lng:.4f})" if call else "unknown"

    body = (
        f"resQ Siren — DETAILED PATIENT REPORT (patient picked up)\n\n"
        f"Dispatch ID: {dispatch.id}\n"
        f"Ambulance: {dispatch.ambulance_id}\n"
        f"Severity: {dispatch.severity.value}\n\n"
        f"Pickup confirmed: {picked_up_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"Response time (dispatch → pickup): {response_minutes} min\n"
        f"Pickup location: {pickup_location}\n\n"
        f"Patient summary:\n{call.patient_summary if call and call.patient_summary else '(none provided)'}\n\n"
        f"{eta_note}"
    )
    try:
        await send_email(
            hospital.email,
            f"[resQ Siren] DETAILED — {dispatch.severity.value} patient picked up ({dispatch.ambulance_id})",
            body,
        )
    except Exception:
        logger.exception("Arrival report email failed for dispatch %s", dispatch.id)


async def create_dispatch(
    db: AsyncSession,
    *,
    ambulance_id: str,
    severity: Severity,
    hospital_id: str,
    call_id: uuid.UUID | None,
    origin: tuple[float | None, float | None],
    notify_phone: str | None = None,
    patient_summary: str | None = None,
) -> tuple[Dispatch, dict | None]:
    """Creates and HMAC-signs a Dispatch, computes its route, persists the
    Trip row, emits dispatch:created, and optionally fires an SMS alert.
    Shared by the staff-triggered POST /dispatch endpoint and the public
    POST /emergency auto-dispatch flow — exactly one place a dispatch gets
    created and signed.
    """
    hospital = await routing_service.get_hospital(db, hospital_id)

    route: dict | None = None
    if origin[0] is not None and origin[1] is not None and hospital is not None:
        route = await routing_service.get_route(origin, (hospital.lat, hospital.lng))  # type: ignore[arg-type]

    dispatch = Dispatch(
        call_id=call_id,
        ambulance_id=ambulance_id,
        severity=severity,
        hospital_id=hospital_id,
        status=DispatchStatus.ACTIVE,
        hospital_response=HospitalResponse.PENDING,
        hmac_signature="",
    )
    db.add(dispatch)
    await db.flush()  # assigns id + server-side created_at

    dispatch.hmac_signature = hmac_util.sign(
        dispatch.id, dispatch.ambulance_id, dispatch.severity, dispatch.hospital_id, dispatch.created_at
    )

    db.add(
        Trip(
            dispatch_id=dispatch.id,
            junctions_cleared=[],
            arbitrations_involved=[],
            declined_hospital_ids=[],
            route=route,
        )
    )

    await db.commit()
    await db.refresh(dispatch)

    if notify_phone:
        eta_note = f", ETA {round(route['durationSeconds'] / 60)} min" if route else ""
        try:
            await send_sms(
                notify_phone,
                f"resQ Siren: {dispatch.ambulance_id} dispatched, severity {dispatch.severity.value}"
                f" to {dispatch.hospital_id}{eta_note}.",
            )
        except Exception:
            logger.exception("SMS notify failed for dispatch %s", dispatch.id)

    if hospital is not None:
        await _email_hospital_report(hospital, dispatch=dispatch, route=route, patient_summary=patient_summary)

    await emit_event(
        "dispatch:created",
        {
            "id": str(dispatch.id),
            "ambulanceId": dispatch.ambulance_id,
            "severity": dispatch.severity.value,
            "hospitalId": dispatch.hospital_id,
            "route": route,
            "patientSummary": patient_summary,
        },
    )

    return dispatch, route


async def available_ambulance_ids(db: AsyncSession) -> set[str]:
    result = await db.execute(select(Dispatch.ambulance_id).where(Dispatch.status == DispatchStatus.ACTIVE))
    busy = {row[0] for row in result.all()}
    return set(routing_service.AMBULANCES.keys()) - busy


async def reroute_hospital(db: AsyncSession, dispatch: Dispatch) -> dict:
    """Picks the next-nearest hospital (excluding every hospital already
    declined for this dispatch's trip), recomputes the route, and emits
    dispatch:rerouted. Raises ValueError if the hospital pool is exhausted.
    """
    result = await db.execute(select(Trip).where(Trip.dispatch_id == dispatch.id))
    trip = result.scalar_one()

    declined = set(trip.declined_hospital_ids) | {dispatch.hospital_id}
    trip.declined_hospital_ids = sorted(declined)

    hospitals = await routing_service.list_emergency_hospitals(db)
    origin = hospitals.get(dispatch.hospital_id)  # fallback anchor if we have no better origin
    call = await db.get(Call, dispatch.call_id) if dispatch.call_id is not None else None
    if call is not None:
        origin = (call.origin_lat, call.origin_lng)

    next_id = routing_service.nearest(origin, hospitals, exclude=frozenset(declined)) if origin else None
    if next_id is None:
        raise ValueError("NO_HOSPITAL_AVAILABLE")

    new_hospital = hospitals[next_id]
    route = await routing_service.get_route(origin, new_hospital) if origin else None  # type: ignore[arg-type]

    dispatch.hospital_id = next_id
    dispatch.hospital_response = HospitalResponse.PENDING
    trip.route = route

    await db.commit()
    await db.refresh(dispatch)

    new_hospital_row = await routing_service.get_hospital(db, next_id)
    if new_hospital_row is not None:
        await _email_hospital_report(
            new_hospital_row,
            dispatch=dispatch,
            route=route,
            patient_summary=call.patient_summary if call is not None else None,
        )

    await emit_event(
        "dispatch:rerouted",
        {
            "id": str(dispatch.id),
            "ambulanceId": dispatch.ambulance_id,
            "severity": dispatch.severity.value,
            "hospitalId": dispatch.hospital_id,
            "route": route,
            "patientSummary": call.patient_summary if call is not None else None,
        },
    )
    return {"hospitalId": dispatch.hospital_id, "route": route}
