"""Pure arbitration logic - no I/O, easy to unit test.

score = severity_weight * 100 + wait_seconds (see resq_shared.severity.score_for)

Red beats Yellow beats Green by default, regardless of arrival order, but a
lower-severity ambulance that has waited long enough eventually outranks a
fresh higher-severity claim. This prevents starvation.
"""
from dataclasses import dataclass

from resq_shared.severity import Severity, score_for


@dataclass
class Claim:
    dispatch_id: str
    ambulance_id: str
    severity: Severity
    wait_seconds: float


@dataclass
class RankedClaim:
    dispatch_id: str
    ambulance_id: str
    severity: Severity
    wait_seconds: float
    score: float


def rank_claims(claims: list[Claim]) -> list[RankedClaim]:
    ranked = [
        RankedClaim(
            dispatch_id=c.dispatch_id,
            ambulance_id=c.ambulance_id,
            severity=c.severity,
            wait_seconds=c.wait_seconds,
            score=score_for(c.severity, c.wait_seconds),
        )
        for c in claims
    ]
    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked


def winner_of(claims: list[Claim]) -> str | None:
    ranked = rank_claims(claims)
    return ranked[0].dispatch_id if ranked else None
