import socketio
from fastapi import FastAPI
from sqlalchemy import select

from app.auth.router import router as auth_router
from app.calls.router import router as calls_router
from app.db import Base, SessionLocal, engine
from app.dispatch.router import router as dispatch_router
from app.emergency.router import router as emergency_router
from app.junctions.router import router as junctions_router
from app.models import Hospital
from app.realtime.sio import sio
from app.routing.router import router as routing_router
from app.routing.service import HOSPITAL_SEED
from app.trips.router import router as trips_router

fastapi_app = FastAPI(title="resQ Siren API")

fastapi_app.include_router(auth_router)
fastapi_app.include_router(calls_router)
fastapi_app.include_router(dispatch_router)
fastapi_app.include_router(junctions_router)
fastapi_app.include_router(trips_router)
fastapi_app.include_router(routing_router)
fastapi_app.include_router(emergency_router)


@fastapi_app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        existing = (await db.execute(select(Hospital.id))).first()
        if existing is None:
            db.add_all([Hospital(**row) for row in HOSPITAL_SEED])
            await db.commit()


@fastapi_app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
