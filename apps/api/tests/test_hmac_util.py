import uuid
from datetime import datetime, timezone

from app.dispatch import hmac_util
from app.models import Severity


def _fixed_args():
    return dict(
        dispatch_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        ambulance_id="AMB-01",
        severity=Severity.RED,
        hospital_id="apollo-vanagaram",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_verify_accepts_valid_signature():
    args = _fixed_args()
    signature = hmac_util.sign(**args)
    assert hmac_util.verify(**args, signature=signature) is True


def test_verify_rejects_tampered_ambulance_id():
    args = _fixed_args()
    signature = hmac_util.sign(**args)
    tampered = {**args, "ambulance_id": "AMB-99"}
    assert hmac_util.verify(**tampered, signature=signature) is False


def test_verify_rejects_forged_signature():
    args = _fixed_args()
    assert hmac_util.verify(**args, signature="not-a-real-signature") is False


def test_sign_is_deterministic():
    args = _fixed_args()
    assert hmac_util.sign(**args) == hmac_util.sign(**args)
