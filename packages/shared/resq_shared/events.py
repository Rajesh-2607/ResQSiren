"""
Event contracts for the resQ Siren event bus (Redis pub/sub).

Design principle: services publish facts that happened; they don't call each
other to ask "what should I do". A junction doesn't ask a service what to do -
it subscribes to a stream of signed "ambulance approaching" events.
"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from .severity import Severity


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Channels:
    DISPATCH_CREATED = "events:dispatch.created"
    AMBULANCE_APPROACHING_VERIFIED = "events:ambulance.approaching.verified"
    ARBITRATION_RESULT = "events:arbitration.result"
    SIGNAL_PREEMPTION = "events:signal.preemption"
    NOTIFICATION_SENT = "events:notification.sent"


class DispatchCreatedEvent(BaseModel):
    dispatch_id: str
    call_id: str
    severity: Severity
    ambulance_id: str
    hospital_id: str
    origin: dict
    destination: dict
    route: Optional[dict] = None
    eta_seconds: Optional[float] = None
    signature: str
    created_at: datetime = Field(default_factory=utcnow)


class AmbulanceApproachingEvent(BaseModel):
    """Published by signal-command only after HMAC verification passes."""

    dispatch_id: str
    ambulance_id: str
    junction_id: str
    severity: Severity
    eta_seconds: float
    ts: datetime = Field(default_factory=utcnow)


class ArbitrationRankEntry(BaseModel):
    dispatch_id: str
    ambulance_id: str
    severity: Severity
    score: float
    wait_seconds: float


class ArbitrationResultEvent(BaseModel):
    junction_id: str
    winner_dispatch_id: Optional[str]
    ranked: list[ArbitrationRankEntry]
    ts: datetime = Field(default_factory=utcnow)


class SignalPreemptionEvent(BaseModel):
    junction_id: str
    dispatch_id: str
    action: str  # "preempt" | "release"
    message: str
    ts: datetime = Field(default_factory=utcnow)


class NotificationSentEvent(BaseModel):
    channel: str  # "hospital" | "police" | "public"
    dispatch_id: Optional[str]
    subject: str
    body: str
    ts: datetime = Field(default_factory=utcnow)
