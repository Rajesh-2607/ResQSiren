import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from resq_shared.events import Channels
from resq_shared.seed import JUNCTIONS
from resq_shared.severity import Severity

from . import claims as claims_store
from . import demo, engine
from .arbitration import rank_claims
from .bus import bus
from .config import settings
from .ws import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bus.connect()
    subscriber_task = bus.run_subscriber(
        Channels.AMBULANCE_APPROACHING_VERIFIED, engine.on_ambulance_approaching
    )
    tick_task = asyncio.create_task(engine.tick_loop())
    yield
    subscriber_task.cancel()
    tick_task.cancel()
    await bus.close()


app = FastAPI(title="resQ Siren - Conflict Resolution Engine", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "conflict-resolution"}


@app.get("/junctions")
async def junctions():
    return JUNCTIONS


@app.get("/junctions/{junction_id}/status")
async def junction_status(junction_id: str):
    claims = await claims_store.claims_for_junction(bus, junction_id)
    ranked = rank_claims(claims)
    return {"junction_id": junction_id, "ranked": [r.__dict__ for r in ranked]}


class DemoAmbulance(BaseModel):
    ambulance_id: str
    severity: Severity
    initial_eta_seconds: float = 20.0


class DemoConvergeRequest(BaseModel):
    junction_id: str
    ambulances: list[DemoAmbulance]
    duration_seconds: float = 20.0


@app.post("/demo/converge")
async def demo_converge(req: DemoConvergeRequest):
    """Kick off the 'two ambulances converge on one junction' demo scenario
    in the background and return immediately - the live map/log show it play out."""
    converging = [
        demo.ConvergingAmbulance(a.ambulance_id, a.severity, a.initial_eta_seconds) for a in req.ambulances
    ]
    asyncio.create_task(demo.run_convergence(req.junction_id, converging, req.duration_seconds))
    return {
        "junction_id": req.junction_id,
        "dispatch_ids": [a.dispatch_id for a in converging],
        "duration_seconds": req.duration_seconds,
    }


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)
