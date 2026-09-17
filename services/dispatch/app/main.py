from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from resq_shared.db import ensure_schema_and_tables
from sqlalchemy.ext.asyncio import AsyncSession

from . import service
from .bus import bus
from .config import settings
from .db import engine, get_db
from .models import SCHEMA, Base
from .schemas import ApproachingRequest, CallCreateRequest, CallResponse, DispatchCreateRequest, DispatchResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_schema_and_tables(engine, SCHEMA, Base)
    await bus.connect()
    yield
    await bus.close()


app = FastAPI(title="resQ Siren - Dispatch Service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "dispatch"}


@app.post("/calls", response_model=CallResponse)
async def create_call(req: CallCreateRequest, db: AsyncSession = Depends(get_db)):
    call = await service.create_call(db, req)
    return CallResponse(
        id=call.id,
        caller_name=call.caller_name,
        phone=call.phone,
        symptom=call.symptom,
        severity=call.severity,
        location={"lat": call.lat, "lng": call.lng},
        attendant_consent=call.attendant_consent,
    )


@app.get("/calls", response_model=list[CallResponse])
async def list_calls(db: AsyncSession = Depends(get_db)):
    calls = await service.list_calls(db)
    return [
        CallResponse(
            id=c.id,
            caller_name=c.caller_name,
            phone=c.phone,
            symptom=c.symptom,
            severity=c.severity,
            location={"lat": c.lat, "lng": c.lng},
            attendant_consent=c.attendant_consent,
        )
        for c in calls
    ]


@app.post("/dispatch", response_model=DispatchResponse)
async def create_dispatch(req: DispatchCreateRequest, db: AsyncSession = Depends(get_db)):
    call = await service.get_call(db, req.call_id)
    if not call:
        raise HTTPException(status_code=404, detail="call not found")
    dispatch = await service.create_dispatch(db, call, req.hospital_id)
    return _to_response(dispatch)


@app.get("/dispatch/{dispatch_id}", response_model=DispatchResponse)
async def get_dispatch(dispatch_id: str, db: AsyncSession = Depends(get_db)):
    dispatch = await service.get_dispatch(db, dispatch_id)
    if not dispatch:
        raise HTTPException(status_code=404, detail="dispatch not found")
    return _to_response(dispatch)


@app.get("/dispatch", response_model=list[DispatchResponse])
async def list_dispatches(db: AsyncSession = Depends(get_db)):
    dispatches = await service.list_dispatches(db)
    return [_to_response(d) for d in dispatches]


@app.post("/dispatch/{dispatch_id}/approaching")
async def report_approaching(dispatch_id: str, req: ApproachingRequest, db: AsyncSession = Depends(get_db)):
    dispatch = await service.get_dispatch(db, dispatch_id)
    if not dispatch:
        raise HTTPException(status_code=404, detail="dispatch not found")
    await service.report_approaching(dispatch, req.junction_id, req.eta_seconds)
    return {"ok": True}


@app.post("/dispatch/{dispatch_id}/arrived", response_model=DispatchResponse)
async def mark_arrived(dispatch_id: str, db: AsyncSession = Depends(get_db)):
    dispatch = await service.get_dispatch(db, dispatch_id)
    if not dispatch:
        raise HTTPException(status_code=404, detail="dispatch not found")
    dispatch = await service.mark_arrived(db, dispatch)
    return _to_response(dispatch)


def _to_response(dispatch) -> DispatchResponse:
    return DispatchResponse(
        id=dispatch.id,
        call_id=dispatch.call_id,
        ambulance_id=dispatch.ambulance_id,
        hospital_id=dispatch.hospital_id,
        severity=dispatch.severity,
        origin=dispatch.origin,
        destination=dispatch.destination,
        route=dispatch.route,
        eta_seconds=dispatch.eta_seconds,
        status=dispatch.status,
        signature=dispatch.signature,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)
