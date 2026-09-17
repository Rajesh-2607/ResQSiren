from dataclasses import dataclass

_SEVERITY_RANK = {"RED": 3, "AMBER": 2, "GREEN": 1}


@dataclass
class Claim:
    dispatch_id: str
    severity: str  # "RED" | "AMBER" | "GREEN"
    eta_seconds: int


@dataclass
class ArbitrationResult:
    winner: Claim
    loser: Claim | None
    reason: str


def arbitrate(incoming: Claim, holder: Claim | None) -> ArbitrationResult:
    """Decide which claim holds the junction.

    No existing holder -> incoming wins outright.
    Otherwise compare severity first (higher wins), then ETA as a tiebreak
    (lower/sooner-arriving wins).
    """
    if holder is None:
        return ArbitrationResult(winner=incoming, loser=None, reason="NO_CONTENTION")

    incoming_rank = _SEVERITY_RANK[incoming.severity]
    holder_rank = _SEVERITY_RANK[holder.severity]

    if incoming_rank > holder_rank:
        return ArbitrationResult(winner=incoming, loser=holder, reason="HIGHER_SEVERITY")
    if incoming_rank < holder_rank:
        return ArbitrationResult(winner=holder, loser=incoming, reason="HIGHER_SEVERITY")

    if incoming.eta_seconds < holder.eta_seconds:
        return ArbitrationResult(winner=incoming, loser=holder, reason="LOWER_ETA")
    if incoming.eta_seconds > holder.eta_seconds:
        return ArbitrationResult(winner=holder, loser=incoming, reason="LOWER_ETA")

    return ArbitrationResult(winner=holder, loser=incoming, reason="INCUMBENT_TIEBREAK")
