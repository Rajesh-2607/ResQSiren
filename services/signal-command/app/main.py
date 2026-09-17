from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from resq_shared.events import Channels
from pydantic import BaseModel
from resq_shared.severity import Severity

from . import itms_mock, service
from .bus import bus
from .config import settings
from .ws import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bus.connect()
    task = bus.run_subscriber(Channels.ARBITRATION_RESULT, service.on_arbitration_result)
    yield
    task.cancel()
    await bus.close()


app = FastAPI(title="resQ Siren - Signal Command Service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ApproachingRequest(BaseModel):
    dispatch_id: str
    ambulance_id: str
    junction_id: str
    severity: Severity
    eta_seconds: float
    signature: str


@app.get("/health")
async def health():
    return {"status": "ok", "service": "signal-command"}


@app.post("/signal/approaching")
async def approaching(req: ApproachingRequest):
    payload = req.model_dump(mode="json", exclude={"signature"})
    ok = await service.verify_and_publish_approaching(payload, req.signature)
    if not ok:
        raise HTTPException(status_code=401, detail="invalid or spoofed signature - ping rejected")
    return {"verified": True}


@app.get("/signal/log")
async def recent_log():
    return list(itms_mock.recent_commands)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # client doesn't need to send anything; just keep alive
    except WebSocketDisconnect:
        manager.disconnect(ws)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)
