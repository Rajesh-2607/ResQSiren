import hashlib
import hmac
import uuid
from datetime import datetime

from app.config import settings
from app.models import Severity


def _canonical_payload(
    dispatch_id: uuid.UUID, ambulance_id: str, severity: Severity, hospital_id: str, created_at: datetime
) -> bytes:
    raw = f"{dispatch_id}|{ambulance_id}|{severity.value}|{hospital_id}|{created_at.isoformat()}"
    return raw.encode("utf-8")


def sign(dispatch_id: uuid.UUID, ambulance_id: str, severity: Severity, hospital_id: str, created_at: datetime) -> str:
    payload = _canonical_payload(dispatch_id, ambulance_id, severity, hospital_id, created_at)
    return hmac.new(settings.hmac_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify(
    dispatch_id: uuid.UUID,
    ambulance_id: str,
    severity: Severity,
    hospital_id: str,
    created_at: datetime,
    signature: str,
) -> bool:
    expected = sign(dispatch_id, ambulance_id, severity, hospital_id, created_at)
    return hmac.compare_digest(expected, signature)
