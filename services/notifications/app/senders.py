"""
Mocked notification channels. Real Twilio/FCM/SMTP wiring is out of scope for
this pass (no credentials to stand them up) - every send is logged and kept
in the in-memory feed instead, so the event-driven flow is fully provable
without external accounts.
"""
import logging
from collections import deque

logger = logging.getLogger("resq.notify.senders")

feed: deque[dict] = deque(maxlen=100)


def _record(channel: str, subject: str, body: str, dispatch_id: str | None) -> dict:
    entry = {"channel": channel, "subject": subject, "body": body, "dispatch_id": dispatch_id}
    logger.info("[%s] %s - %s", channel, subject, body)
    feed.appendleft(entry)
    return entry


def notify_hospital(subject: str, body: str, dispatch_id: str | None) -> dict:
    return _record("hospital", subject, body, dispatch_id)


def notify_police(subject: str, body: str, dispatch_id: str | None) -> dict:
    return _record("police", subject, body, dispatch_id)


def notify_public(subject: str, body: str, dispatch_id: str | None) -> dict:
    return _record("public", subject, body, dispatch_id)
