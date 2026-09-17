from enum import Enum


class Severity(str, Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


# Higher weight wins arbitration. Used as: score = SEVERITY_WEIGHT[severity] * 100 - wait_seconds
SEVERITY_WEIGHT: dict[Severity, int] = {
    Severity.RED: 3,
    Severity.YELLOW: 2,
    Severity.GREEN: 1,
}

# Rule-based symptom -> severity triage, shared by dispatch call-intake.
SYMPTOM_SEVERITY_MAP: dict[str, Severity] = {
    "cardiac_arrest": Severity.RED,
    "not_breathing": Severity.RED,
    "severe_bleeding": Severity.RED,
    "unconscious": Severity.RED,
    "stroke_symptoms": Severity.RED,
    "chest_pain": Severity.YELLOW,
    "breathing_difficulty": Severity.YELLOW,
    "fracture": Severity.YELLOW,
    "high_fever": Severity.YELLOW,
    "stable_transfer": Severity.GREEN,
    "routine_checkup": Severity.GREEN,
    "minor_injury": Severity.GREEN,
}

DEFAULT_SEVERITY = Severity.YELLOW


def score_for(severity: Severity, wait_seconds: float) -> float:
    """score = severity_weight * 100 + wait_seconds.

    Waiting *raises* score (not lowers it) - that's what makes this
    anti-starvation: a GREEN claim overtakes a fresh RED (delta 200) once it
    has waited 200s, and overtakes a fresh YELLOW (delta 100) after 100s.
    A formula that subtracted wait_seconds would do the opposite of the
    stated goal, so this is `+`, not the naive reading of the spec.
    """
    return SEVERITY_WEIGHT[severity] * 100 + wait_seconds
