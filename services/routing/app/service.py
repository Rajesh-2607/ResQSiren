import math

import httpx
from resq_shared.seed import AMBULANCES, HOSPITALS, JUNCTIONS

from .config import settings

AVERAGE_SPEED_KMH = 40.0  # ambulance with corridor priority, urban traffic


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def eta_seconds_for(distance_km: float) -> float:
    return (distance_km / AVERAGE_SPEED_KMH) * 3600


async def compute_route(origin: dict, destination: dict) -> dict:
    """Try OSRM if configured, else fall back to a deterministic straight-line mock."""
    if settings.osrm_base_url:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                coords = f"{origin['lng']},{origin['lat']};{destination['lng']},{destination['lat']}"
                resp = await client.get(
                    f"{settings.osrm_base_url}/route/v1/driving/{coords}",
                    params={"overview": "full", "geometries": "geojson"},
                )
                resp.raise_for_status()
                data = resp.json()
                route = data["routes"][0]
                geometry = route["geometry"]["coordinates"]
                return {
                    "source": "osrm",
                    "distance_km": route["distance"] / 1000,
                    "eta_seconds": route["duration"],
                    "path": [{"lat": lat, "lng": lng} for lng, lat in geometry],
                }
        except (httpx.HTTPError, KeyError, IndexError):
            pass  # fall through to mock

    distance_km = haversine_km(origin["lat"], origin["lng"], destination["lat"], destination["lng"])
    return {
        "source": "mock-straight-line",
        "distance_km": round(distance_km, 3),
        "eta_seconds": round(eta_seconds_for(distance_km), 1),
        "path": [origin, destination],
    }


def nearest_ambulance(lat: float, lng: float) -> dict:
    best = min(AMBULANCES, key=lambda a: haversine_km(lat, lng, a["lat"], a["lng"]))
    return best


def nearest_hospital(lat: float, lng: float) -> dict:
    best = min(HOSPITALS, key=lambda h: haversine_km(lat, lng, h["lat"], h["lng"]))
    return best


def list_hospitals() -> list[dict]:
    return HOSPITALS


def list_ambulances() -> list[dict]:
    return AMBULANCES


def list_junctions() -> list[dict]:
    return JUNCTIONS
