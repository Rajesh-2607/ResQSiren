"""
Demo scenario simulator - the "two ambulances converge on one junction" moment
from the README's demo plan. It exercises the exact same trust path as a real
ambulance (signed pings -> signal-command verification -> conflict-resolution
arbitration), just without needing real GPS hardware or a live dispatch
record in Postgres.
"""
import asyncio
import logging
import uuid

import httpx
from resq_shared.hmac_util import sign_payload
from resq_shared.severity import Severity

from .config import settings

logger = logging.getLogger("resq.conflict.demo")

PING_INTERVAL_SECONDS = 2.0


class ConvergingAmbulance:
    def __init__(self, ambulance_id: str, severity: Severity, initial_eta_seconds: float):
        self.dispatch_id = f"demo-{uuid.uuid4().hex[:8]}"
        self.ambulance_id = ambulance_id
        self.severity = severity
        self.eta_seconds = initial_eta_seconds


async def _send_ping(client: httpx.AsyncClient, junction_id: str, amb: ConvergingAmbulance) -> None:
    payload = {
        "dispatch_id": amb.dispatch_id,
        "ambulance_id": amb.ambulance_id,
        "junction_id": junction_id,
        "severity": amb.severity.value,
        "eta_seconds": amb.eta_seconds,
    }
    signature = sign_payload(payload, settings.dispatch_hmac_secret)
    try:
        resp = await client.post(
            f"{settings.signal_command_url}/signal/approaching",
            json={**payload, "signature": signature},
            timeout=5.0,
        )
        resp.raise_for_status()
    except httpx.HTTPError:
        logger.exception("demo ping failed for %s", amb.dispatch_id)


async def run_convergence(junction_id: str, ambulances: list[ConvergingAmbulance], duration_seconds: float = 20.0) -> None:
    ticks = max(1, int(duration_seconds / PING_INTERVAL_SECONDS))
    async with httpx.AsyncClient() as client:
        for _ in range(ticks):
            await asyncio.gather(*(_send_ping(client, junction_id, amb) for amb in ambulances))
            for amb in ambulances:
                amb.eta_seconds = max(0.0, amb.eta_seconds - PING_INTERVAL_SECONDS)
            await asyncio.sleep(PING_INTERVAL_SECONDS)
