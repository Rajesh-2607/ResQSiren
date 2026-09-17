"""
Mock ITMS (Intelligent Traffic Management System) adapter.

Stands in for real junction hardware. The interface (`preempt`/`release`) is
what a real RFID/GPS-geofence-triggered signal controller would implement -
swapping this module for a real one is the entire migration path.
"""
import logging
from collections import deque
from datetime import datetime, timezone

logger = logging.getLogger("resq.itms_mock")

# Small in-memory ring buffer so the dashboard / judges can see recent
# pre-emption commands without needing a database.
recent_commands: deque[dict] = deque(maxlen=50)


def preempt(junction_id: str, dispatch_id: str) -> str:
    message = f"signal pre-empted at junction {junction_id} for dispatch {dispatch_id}"
    logger.info(message)
    recent_commands.appendleft(
        {
            "junction_id": junction_id,
            "dispatch_id": dispatch_id,
            "action": "preempt",
            "message": message,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
    )
    return message


def release(junction_id: str, dispatch_id: str) -> str:
    message = f"signal released at junction {junction_id} (was held for dispatch {dispatch_id})"
    logger.info(message)
    recent_commands.appendleft(
        {
            "junction_id": junction_id,
            "dispatch_id": dispatch_id,
            "action": "release",
            "message": message,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
    )
    return message
