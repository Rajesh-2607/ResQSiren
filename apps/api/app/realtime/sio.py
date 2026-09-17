import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


async def emit_event(event: str, data: dict) -> None:
    await sio.emit(event, data)
