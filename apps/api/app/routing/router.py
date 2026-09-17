from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db import get_db
from app.routing import service as routing_service
from app.routing.service import get_route

router = APIRouter(prefix="/routing", tags=["routing"])


@router.get("/hospitals")
async def list_hospitals(
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
) -> dict:
    hospitals = await routing_service.list_hospitals(db)
    return {hid: {"lat": lat, "lng": lng} for hid, (lat, lng) in hospitals.items()}


@router.get("/route")
async def route(
    originLat: float,
    originLng: float,
    destLat: float,
    destLng: float,
    _user=Depends(get_current_user),
) -> dict:
    return await get_route((originLat, originLng), (destLat, destLng))
