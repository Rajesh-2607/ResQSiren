from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from resq_shared.events import Channels

from . import senders, service
from .bus import bus
from .config import settings
from .ws import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bus.connect()
    t1 = bus.run_subscriber(Channels.DISPATCH_CREATED, service.on_dispatch_created)
    t2 = bus.run_subscriber(Channels.ARBITRATION_RESULT, service.on_arbitration_result)
    yield
    t1.cancel()
    t2.cancel()
    await bus.close()


app = FastAPI(title="resQ Siren - Notifications Service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "notifications"}


@app.get("/notifications")
async def list_notifications():
    return list(senders.feed)


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
