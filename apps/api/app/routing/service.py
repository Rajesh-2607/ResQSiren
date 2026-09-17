import math

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Hospital

# Demo-only static ambulance fleet home-bases (lat, lng). A real deployment
# would pull live GPS positions instead of hardcoding a home base per unit.
AMBULANCES: dict[str, tuple[float, float]] = {
    "AMB-01": (13.0850, 80.2101),  # Anna Nagar
    "AMB-02": (13.0418, 80.2341),  # T Nagar
    "AMB-03": (12.9756, 80.2207),  # Velachery
    "AMB-04": (13.0067, 80.2570),  # Adyar
    "AMB-05": (13.0732, 80.2609),  # Egmore
}

# Seed rows for the `hospitals` table — inserted once on startup if the table
# is empty (see app/main.py). Spread across Chennai so the auto-reroute-on-
# decline flow has somewhere real to go for more than one hop.
#
# Hospital *names* here are fictional demo entities (not real hospitals), and
# `email` is deliberately the same real test inbox on every row — the point
# of this seed set is to let the dispatch-report email feature actually be
# verified end to end by its owner. Swap in real, distinct ER contacts only
# for an actual deployment, never for a demo — never reuse this pattern with
# a real hospital's name paired with an address that isn't that hospital's own.
HOSPITAL_SEED: list[dict] = [
    {
        "id": "apollo-emergency",
        "name": "Apollo Emergency Hospital",
        "lat": 13.0604,
        "lng": 80.2496,
        "email": "rajesh.28ad@licet.ac.in",
        "phone": "+91-9876543210",
        "address": "Greams Road, Chennai, Tamil Nadu",
        "available_beds": 24,
        "emergency_available": True,
    },
    {
        "id": "city-care-multispeciality",
        "name": "City Care Multispeciality Hospital",
        "lat": 13.0850,
        "lng": 80.2101,
        "email": "rajesh.28ad@licet.ac.in",
        "phone": "+91-9876543211",
        "address": "Anna Nagar, Chennai, Tamil Nadu",
        "available_beds": 18,
        "emergency_available": True,
    },
    {
        "id": "chennai-medical-centre",
        "name": "Chennai Medical Centre",
        "lat": 13.0418,
        "lng": 80.2341,
        "email": "rajesh.28ad@licet.ac.in",
        "phone": "+91-9876543212",
        "address": "T Nagar, Chennai, Tamil Nadu",
        "available_beds": 12,
        "emergency_available": True,
    },
    {
        "id": "green-valley",
        "name": "Green Valley Hospital",
        "lat": 12.9750,
        "lng": 80.2212,
        "email": "rajesh.28ad@licet.ac.in",
        "phone": "+91-9876543213",
        "address": "Velachery, Chennai, Tamil Nadu",
        "available_beds": 30,
        "emergency_available": True,
    },
    {
        "id": "metro-emergency-care",
        "name": "Metro Emergency Care",
        "lat": 13.0067,
        "lng": 80.2206,
        "email": "rajesh.28ad@licet.ac.in",
        "phone": "+91-9876543214",
        "address": "Guindy, Chennai, Tamil Nadu",
        "available_beds": 15,
        "emergency_available": True,
    },
]


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Straight-line distance in km — used only to pick *which* ambulance or
    hospital is closest. The real fastest-route distance/ETA still comes
    from get_route() below.
    """
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def nearest(
    point: tuple[float, float],
    candidates: dict[str, tuple[float, float]],
    exclude: frozenset[str] = frozenset(),
) -> str | None:
    """Returns the id of the closest candidate to `point`, or None if every
    candidate is excluded / the pool is empty.
    """
    pool = {cid: coords for cid, coords in candidates.items() if cid not in exclude}
    if not pool:
        return None
    return min(pool, key=lambda cid: haversine_km(point, pool[cid]))


async def list_hospitals(db: AsyncSession) -> dict[str, tuple[float, float]]:
    result = await db.execute(select(Hospital))
    return {h.id: (h.lat, h.lng) for h in result.scalars().all()}


async def list_emergency_hospitals(db: AsyncSession) -> dict[str, tuple[float, float]]:
    """Same as list_hospitals but only hospitals currently accepting
    emergencies — this is the candidate pool for auto-selection/reroute,
    while list_hospitals (unfiltered) stays the staff reference listing.
    """
    result = await db.execute(select(Hospital).where(Hospital.emergency_available.is_(True)))
    return {h.id: (h.lat, h.lng) for h in result.scalars().all()}


async def get_hospital(db: AsyncSession, hospital_id: str) -> Hospital | None:
    return await db.get(Hospital, hospital_id)


async def get_route(origin: tuple[float, float], destination: tuple[float, float]) -> dict:
    """Returns the fastest route from Mapbox Directions, falling back to OSRM
    (defaults to the public router.project-osrm.org demo server — no
    self-hosting required), falling back to a deterministic mock so the flow
    never crashes without a routing provider reachable.
    """
    if settings.mapbox_token:
        try:
            return await _mapbox_route(origin, destination)
        except httpx.HTTPError:
            pass
    if settings.osrm_base_url:
        try:
            return await _osrm_route(origin, destination)
        except httpx.HTTPError:
            pass
    return _mock_route(origin, destination)


def _normalize(source: str, payload: dict) -> dict:
    route = payload["routes"][0]
    return {
        "source": source,
        "distanceMeters": route["distance"],
        "durationSeconds": route["duration"],
        "geometry": route.get("geometry"),
    }


async def _mapbox_route(origin: tuple[float, float], destination: tuple[float, float]) -> dict:
    coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coords}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params={"access_token": settings.mapbox_token, "geometries": "geojson"})
        resp.raise_for_status()
        return _normalize("mapbox", resp.json())


async def _osrm_route(origin: tuple[float, float], destination: tuple[float, float]) -> dict:
    coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
    url = f"{settings.osrm_base_url}/route/v1/driving/{coords}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params={"overview": "full", "geometries": "geojson"})
        resp.raise_for_status()
        return _normalize("osrm", resp.json())


def _mock_route(origin: tuple[float, float], destination: tuple[float, float]) -> dict:
    return {
        "source": "mock",
        "distanceMeters": 5000,
        "durationSeconds": 600,
        "geometry": None,
    }
