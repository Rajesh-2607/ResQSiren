from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user, require_role
from app.db import get_db
from app.junctions import service
from app.schemas import PreemptRequest, PreemptResponse

router = APIRouter(prefix="/junctions", tags=["junctions"])


@router.post("/{junction_id}/preempt", response_model=PreemptResponse)
async def preempt_junction(
    junction_id: str,
    body: PreemptRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("dispatcher", "police", "admin")),
) -> PreemptResponse:
    result = await service.preempt(db, junction_id, body.dispatchId, body.etaSeconds)
    return PreemptResponse(**result)


@router.get("/{junction_id}")
async def get_junction_state(
    junction_id: str,
    _user=Depends(get_current_user),
):
    state = await service.get_state(junction_id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NO_ACTIVE_CLAIM")
    return state
