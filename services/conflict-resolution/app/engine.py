import asyncio
import logging

from resq_shared.events import AmbulanceApproachingEvent, ArbitrationRankEntry, ArbitrationResultEvent, Channels
from resq_shared.seed import JUNCTIONS

from . import claims as claims_store
from .arbitration import rank_claims
from .bus import bus
from .config import settings
from .ws import manager

logger = logging.getLogger("resq.conflict.engine")

# junction_id -> whether it had claims on the previous tick, so we publish
# exactly one "cleared" event instead of spamming empty results every tick.
_had_claims: dict[str, bool] = {}


async def on_ambulance_approaching(data: dict) -> None:
    event = AmbulanceApproachingEvent(**data)
    await claims_store.upsert_claim(
        bus, event.junction_id, event.dispatch_id, event.ambulance_id, event.severity
    )


async def _tick_junction(junction_id: str) -> None:
    claims = await claims_store.claims_for_junction(bus, junction_id)

    if not claims:
        if _had_claims.get(junction_id):
            result = ArbitrationResultEvent(junction_id=junction_id, winner_dispatch_id=None, ranked=[])
            await bus.publish(Channels.ARBITRATION_RESULT, result)
            await manager.broadcast("arbitration.result", result.model_dump(mode="json"))
        _had_claims[junction_id] = False
        return

    _had_claims[junction_id] = True
    ranked = rank_claims(claims)
    result = ArbitrationResultEvent(
        junction_id=junction_id,
        winner_dispatch_id=ranked[0].dispatch_id,
        ranked=[
            ArbitrationRankEntry(
                dispatch_id=r.dispatch_id,
                ambulance_id=r.ambulance_id,
                severity=r.severity,
                score=r.score,
                wait_seconds=r.wait_seconds,
            )
            for r in ranked
        ],
    )
    await bus.publish(Channels.ARBITRATION_RESULT, result)
    await manager.broadcast("arbitration.result", result.model_dump(mode="json"))


async def tick_loop() -> None:
    while True:
        for junction in JUNCTIONS:
            try:
                await _tick_junction(junction["id"])
            except Exception:
                logger.exception("tick failed for junction %s", junction["id"])
        await asyncio.sleep(settings.tick_interval_seconds)
