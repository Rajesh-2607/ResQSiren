"""Redis-backed junction claims.

Each claim lives at junction:{junction_id}:claim:{dispatch_id} as a hash with
a TTL - if an ambulance's pings stop arriving (cleared the junction, lost
signal), the claim expires on its own without an explicit cleanup step.
"""
import time

from resq_shared.bus import EventBus
from resq_shared.severity import Severity

from .arbitration import Claim
from .config import settings


def _key(junction_id: str, dispatch_id: str) -> str:
    return f"junction:{junction_id}:claim:{dispatch_id}"


async def upsert_claim(
    bus: EventBus,
    junction_id: str,
    dispatch_id: str,
    ambulance_id: str,
    severity: Severity,
) -> None:
    key = _key(junction_id, dispatch_id)
    now = time.time()
    existing = await bus.redis.hgetall(key)
    first_seen = float(existing["first_seen_ts"]) if existing else now
    await bus.redis.hset(
        key,
        mapping={
            "ambulance_id": ambulance_id,
            "severity": severity.value,
            "first_seen_ts": first_seen,
            "last_seen_ts": now,
        },
    )
    await bus.redis.expire(key, settings.claim_ttl_seconds)


async def claims_for_junction(bus: EventBus, junction_id: str) -> list[Claim]:
    claims: list[Claim] = []
    now = time.time()
    async for key in bus.redis.scan_iter(match=f"junction:{junction_id}:claim:*"):
        data = await bus.redis.hgetall(key)
        if not data:
            continue
        claims.append(
            Claim(
                dispatch_id=key.split(":")[-1],
                ambulance_id=data["ambulance_id"],
                severity=Severity(data["severity"]),
                wait_seconds=now - float(data["first_seen_ts"]),
            )
        )
    return claims


async def clear_claim(bus: EventBus, junction_id: str, dispatch_id: str) -> None:
    await bus.redis.delete(_key(junction_id, dispatch_id))
