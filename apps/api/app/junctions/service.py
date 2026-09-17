import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dispatch import hmac_util
from app.junctions.arbitration import Claim, arbitrate
from app.models import Dispatch
from app.realtime.sio import emit_event
from app.redis_client import redis
from app.trips.service import append_arbitration

ARBITRATION_WINDOW_SECONDS = 5


def _redis_key(junction_id: str) -> str:
    return f"junction:{junction_id}:active"


async def preempt(db: AsyncSession, junction_id: str, dispatch_id: uuid.UUID, eta_seconds: int) -> dict:
    dispatch = await db.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UNKNOWN_DISPATCH")

    if not hmac_util.verify(
        dispatch.id,
        dispatch.ambulance_id,
        dispatch.severity,
        dispatch.hospital_id,
        dispatch.created_at,
        dispatch.hmac_signature,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SIGNATURE_INVALID")

    incoming = Claim(dispatch_id=str(dispatch.id), severity=dispatch.severity.value, eta_seconds=eta_seconds)

    raw_holder = await redis.get(_redis_key(junction_id))
    holder_claim: Claim | None = None
    if raw_holder:
        holder_data = json.loads(raw_holder)
        if holder_data["dispatchId"] != str(dispatch.id):
            holder_claim = Claim(
                dispatch_id=holder_data["dispatchId"],
                severity=holder_data["severity"],
                eta_seconds=holder_data["etaSeconds"],
            )

    result = arbitrate(incoming, holder_claim)

    await redis.set(
        _redis_key(junction_id),
        json.dumps(
            {
                "dispatchId": result.winner.dispatch_id,
                "severity": result.winner.severity,
                "etaSeconds": result.winner.eta_seconds,
                "requestedAt": datetime.now(timezone.utc).isoformat(),
            }
        ),
        ex=ARBITRATION_WINDOW_SECONDS,
    )

    if result.loser is not None:
        loser_dispatch_id = uuid.UUID(result.loser.dispatch_id)
        winner_dispatch_id = uuid.UUID(result.winner.dispatch_id)
        await append_arbitration(db, winner_dispatch_id, junction_id, result.reason, result.loser.dispatch_id)
        await append_arbitration(db, loser_dispatch_id, junction_id, result.reason, result.winner.dispatch_id)

    await emit_event(
        "junction:state",
        {"junctionId": junction_id, "activeDispatchId": result.winner.dispatch_id},
    )
    await emit_event(
        "arbitration:decided",
        {
            "junctionId": junction_id,
            "winnerDispatchId": result.winner.dispatch_id,
            "loserDispatchId": result.loser.dispatch_id if result.loser else None,
            "reason": result.reason,
        },
    )

    return {
        "junctionId": junction_id,
        "winnerDispatchId": uuid.UUID(result.winner.dispatch_id),
        "reason": result.reason,
    }


async def get_state(junction_id: str) -> dict | None:
    raw = await redis.get(_redis_key(junction_id))
    if raw is None:
        return None
    return json.loads(raw)
