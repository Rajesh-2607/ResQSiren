import hashlib
import hmac
import json
from typing import Any, Mapping


def _canonical(payload: Mapping[str, Any]) -> bytes:
    """Deterministic JSON encoding so sign/verify agree regardless of key order."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sign_payload(payload: Mapping[str, Any], secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), _canonical(payload), hashlib.sha256)
    return digest.hexdigest()


def verify_payload(payload: Mapping[str, Any], signature: str, secret: str) -> bool:
    expected = sign_payload(payload, secret)
    return hmac.compare_digest(expected, signature)
