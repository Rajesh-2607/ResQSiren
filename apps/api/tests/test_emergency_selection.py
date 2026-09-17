from app.emergency.service import SYMPTOM_TO_SEVERITY
from app.models import Severity
from app.routing.service import haversine_km, nearest

ANNA_NAGAR = (13.0850, 80.2101)
T_NAGAR = (13.0418, 80.2341)
VELACHERY = (12.9756, 80.2207)


def test_haversine_zero_distance_for_same_point():
    assert haversine_km(ANNA_NAGAR, ANNA_NAGAR) == 0.0


def test_haversine_known_pair_is_positive_and_symmetric():
    d1 = haversine_km(ANNA_NAGAR, T_NAGAR)
    d2 = haversine_km(T_NAGAR, ANNA_NAGAR)
    assert d1 > 0
    assert d1 == d2


def test_nearest_picks_closest_candidate():
    candidates = {"a": ANNA_NAGAR, "t": T_NAGAR, "v": VELACHERY}
    assert nearest(ANNA_NAGAR, candidates) == "a"


def test_nearest_respects_exclude_set():
    candidates = {"a": ANNA_NAGAR, "t": T_NAGAR, "v": VELACHERY}
    assert nearest(ANNA_NAGAR, candidates, exclude=frozenset({"a"})) == "t"


def test_nearest_returns_none_when_pool_exhausted():
    candidates = {"a": ANNA_NAGAR}
    assert nearest(ANNA_NAGAR, candidates, exclude=frozenset({"a"})) is None


def test_nearest_returns_none_for_empty_candidates():
    assert nearest(ANNA_NAGAR, {}) is None


def test_symptom_to_severity_mapping_is_complete_and_correct():
    assert SYMPTOM_TO_SEVERITY["CARDIAC_OR_UNCONSCIOUS"] == Severity.RED
    assert SYMPTOM_TO_SEVERITY["SEVERE_BLEEDING_OR_FRACTURE"] == Severity.AMBER
    assert SYMPTOM_TO_SEVERITY["STABLE_NON_URGENT"] == Severity.GREEN
    assert len(SYMPTOM_TO_SEVERITY) == 3
