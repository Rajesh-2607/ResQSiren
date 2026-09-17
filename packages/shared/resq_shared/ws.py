import json
import logging

from fastapi import WebSocket

logger = logging.getLogger("resq.ws")


class ConnectionManager:
    """Minimal fan-out broadcaster for a service's live dashboard feed."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)

    async def broadcast(self, event_type: str, payload: dict) -> None:
        if not self._connections:
            return
        message = json.dumps({"type": event_type, "payload": payload}, default=str)
        dead = set()
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        self._connections -= dead
