import httpx
from resq_shared.events import Channels, DispatchCreatedEvent
from resq_shared.hmac_util import sign_payload
from resq_shared.seed import hospital_by_id
from resq_shared.severity import SYMPTOM_SEVERITY_MAP, DEFAULT_SEVERITY
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .bus import bus
from .config import settings
from .models import Call, Dispatch


async def create_call(db: AsyncSession, req) -> Call:
    severity = SYMPTOM_SEVERITY_MAP.get(req.symptom, DEFAULT_SEVERITY)
    call = Call(
        caller_name=req.caller_name,
        phone=req.phone,
        symptom=req.symptom,
        severity=severity.value,
        lat=req.location.lat,
        lng=req.location.lng,
        attendant_consent=req.attendant_consent,
    )
    db.add(call)
    await db.commit()
    await db.refresh(call)
    return call


async def get_call(db: AsyncSession, call_id: str) -> Call | None:
    return await db.get(Call, call_id)


async def list_calls(db: AsyncSession) -> list[Call]:
    result = await db.execute(select(Call).order_by(Call.created_at.desc()))
    return list(result.scalars().all())


async def _select_ambulance(origin: dict) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.routing_service_url}/nearest-ambulance",
            params={"lat": origin["lat"], "lng": origin["lng"]},
        )
        resp.raise_for_status()
        return resp.json()


async def _select_hospital(origin: dict, hospital_id: str | None) -> dict:
    if hospital_id:
        hospital = hospital_by_id(hospital_id)
        if hospital:
            return hospital
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.routing_service_url}/nearest-hospital",
            params={"lat": origin["lat"], "lng": origin["lng"]},
        )
        resp.raise_for_status()
        return resp.json()


async def _compute_route(origin: dict, destination: dict) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{settings.routing_service_url}/route",
            json={"origin": origin, "destination": destination},
        )
        resp.raise_for_status()
        return resp.json()


async def create_dispatch(db: AsyncSession, call: Call, hospital_id: str | None) -> Dispatch:
    origin = {"lat": call.lat, "lng": call.lng}
    ambulance = await _select_ambulance(origin)
    hospital = await _select_hospital(origin, hospital_id)
    destination = {"lat": hospital["lat"], "lng": hospital["lng"]}
    route = await _compute_route(origin, destination)

    dispatch = Dispatch(
        call_id=call.id,
        ambulance_id=ambulance["id"],
        hospital_id=hospital["id"],
        severity=call.severity,
        origin=origin,
        destination=destination,
        route=route,
        eta_seconds=route["eta_seconds"],
        status="EN_ROUTE",
    )
    # Sign the record the moment severity/route are fixed, before persisting -
    # this is what the signal-command service checks before trusting any
    # "ambulance approaching" ping that names this dispatch_id.
    signable = {
        "call_id": dispatch.call_id,
        "ambulance_id": dispatch.ambulance_id,
        "hospital_id": dispatch.hospital_id,
        "severity": dispatch.severity,
        "origin": origin,
        "destination": destination,
    }
    dispatch.signature = sign_payload(signable, settings.dispatch_hmac_secret)

    db.add(dispatch)
    await db.commit()
    await db.refresh(dispatch)

    await bus.publish(
        Channels.DISPATCH_CREATED,
        DispatchCreatedEvent(
            dispatch_id=dispatch.id,
            call_id=dispatch.call_id,
            severity=dispatch.severity,
            ambulance_id=dispatch.ambulance_id,
            hospital_id=dispatch.hospital_id,
            origin=origin,
            destination=destination,
            route=route,
            eta_seconds=dispatch.eta_seconds,
            signature=dispatch.signature,
        ),
    )
    return dispatch


async def get_dispatch(db: AsyncSession, dispatch_id: str) -> Dispatch | None:
    return await db.get(Dispatch, dispatch_id)


async def list_dispatches(db: AsyncSession) -> list[Dispatch]:
    result = await db.execute(select(Dispatch).order_by(Dispatch.created_at.desc()))
    return list(result.scalars().all())


async def report_approaching(dispatch: Dispatch, junction_id: str, eta_seconds: float) -> None:
    """Sign the ping server-side on the driver's behalf. The driver unit is
    authenticated to dispatch (its home backend), not to signal-command
    directly, so the HMAC secret never has to leave this service."""
    payload = {
        "dispatch_id": dispatch.id,
        "ambulance_id": dispatch.ambulance_id,
        "junction_id": junction_id,
        "severity": dispatch.severity,
        "eta_seconds": eta_seconds,
    }
    signature = sign_payload(payload, settings.dispatch_hmac_secret)
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{settings.signal_command_url}/signal/approaching",
            json={**payload, "signature": signature},
        )
        resp.raise_for_status()


async def mark_arrived(db: AsyncSession, dispatch: Dispatch) -> Dispatch:
    dispatch.status = "ARRIVED"
    await db.commit()
    await db.refresh(dispatch)
    return dispatch
