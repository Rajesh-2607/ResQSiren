from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import service
from .config import settings

app = FastAPI(title="resQ Siren - Routing Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LatLng(BaseModel):
    lat: float
    lng: float


class RouteRequest(BaseModel):
    origin: LatLng
    destination: LatLng


@app.get("/health")
async def health():
    return {"status": "ok", "service": "routing"}


@app.post("/route")
async def route(req: RouteRequest):
    return await service.compute_route(req.origin.model_dump(), req.destination.model_dump())


@app.get("/nearest-ambulance")
async def nearest_ambulance(lat: float, lng: float):
    return service.nearest_ambulance(lat, lng)


@app.get("/nearest-hospital")
async def nearest_hospital(lat: float, lng: float):
    return service.nearest_hospital(lat, lng)


@app.get("/hospitals")
async def hospitals():
    return service.list_hospitals()


@app.get("/ambulances")
async def ambulances():
    return service.list_ambulances()


@app.get("/junctions")
async def junctions():
    return service.list_junctions()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)
