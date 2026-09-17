from resq_shared.events import Channels, NotificationSentEvent
from resq_shared.seed import hospital_by_id

from . import senders
from .bus import bus
from .ws import manager


async def _emit(entry: dict) -> None:
    event = NotificationSentEvent(
        channel=entry["channel"],
        dispatch_id=entry["dispatch_id"],
        subject=entry["subject"],
        body=entry["body"],
    )
    await bus.publish(Channels.NOTIFICATION_SENT, event)
    await manager.broadcast("notification.sent", event.model_dump(mode="json"))


async def on_dispatch_created(data: dict) -> None:
    hospital = hospital_by_id(data["hospital_id"]) or {"name": data["hospital_id"]}
    entry = senders.notify_hospital(
        subject=f"Incoming {data['severity']} case",
        body=f"Ambulance {data['ambulance_id']} en route to {hospital['name']}, ETA {data.get('eta_seconds', '?')}s",
        dispatch_id=data["dispatch_id"],
    )
    await _emit(entry)


_last_notified: dict[str, str] = {}  # junction_id -> dispatch_id last notified about


async def on_arbitration_result(data: dict) -> None:
    junction_id = data["junction_id"]
    winner = data.get("winner_dispatch_id")
    if not winner:
        _last_notified.pop(junction_id, None)
        return
    if _last_notified.get(junction_id) == winner:
        return  # same ambulance still holding the junction - don't re-alert every tick
    _last_notified[junction_id] = winner
    contested = len(data.get("ranked", [])) > 1
    entry = senders.notify_police(
        subject=f"Junction {data['junction_id']} pre-emption",
        body=(
            f"Dispatch {winner} granted priority"
            + (f" over {len(data['ranked']) - 1} other claim(s)" if contested else "")
        ),
        dispatch_id=winner,
    )
    await _emit(entry)

    if contested:
        entry = senders.notify_public(
            subject=f"Traffic advisory - {data['junction_id']}",
            body="Emergency vehicle corridor active; expect brief signal hold.",
            dispatch_id=winner,
        )
        await _emit(entry)
