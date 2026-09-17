from resq_shared.events import (
    AmbulanceApproachingEvent,
    ArbitrationResultEvent,
    Channels,
    SignalPreemptionEvent,
)
from resq_shared.hmac_util import verify_payload

from . import itms_mock
from .bus import bus
from .config import settings
from .ws import manager


async def verify_and_publish_approaching(payload: dict, signature: str) -> bool:
    """Reject unsigned or spoofed 'approaching' pings outright.

    Only holders of the shared dispatch HMAC secret (dispatch service, and by
    extension trusted driver units) can produce a signature that passes here.
    """
    if not verify_payload(payload, signature, settings.dispatch_hmac_secret):
        return False

    event = AmbulanceApproachingEvent(**payload)
    await bus.publish(Channels.AMBULANCE_APPROACHING_VERIFIED, event)
    await manager.broadcast("ambulance.approaching", event.model_dump(mode="json"))
    return True


_last_preempted: dict[str, str] = {}  # junction_id -> dispatch_id currently holding it


async def on_arbitration_result(data: dict) -> None:
    """Subscribed to conflict-resolution's decisions; this is the only thing
    allowed to actually command the (mock) traffic signal.

    Edge-triggered: conflict-resolution re-publishes the ranking every tick
    even when the winner hasn't changed, but a real signal only needs one
    preempt command per hold - re-issuing it every second would just spam
    the log with identical lines.
    """
    result = ArbitrationResultEvent(**data)
    if not result.winner_dispatch_id:
        _last_preempted.pop(result.junction_id, None)
        return
    if _last_preempted.get(result.junction_id) == result.winner_dispatch_id:
        return
    _last_preempted[result.junction_id] = result.winner_dispatch_id

    message = itms_mock.preempt(result.junction_id, result.winner_dispatch_id)
    preemption = SignalPreemptionEvent(
        junction_id=result.junction_id,
        dispatch_id=result.winner_dispatch_id,
        action="preempt",
        message=message,
    )
    await bus.publish(Channels.SIGNAL_PREEMPTION, preemption)
    await manager.broadcast("signal.preemption", preemption.model_dump(mode="json"))
