import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.arbitration import Claim, rank_claims, winner_of
from resq_shared.severity import Severity


def test_red_beats_yellow_at_equal_wait():
    claims = [
        Claim("d1", "amb-1", Severity.YELLOW, wait_seconds=0),
        Claim("d2", "amb-2", Severity.RED, wait_seconds=0),
    ]
    assert winner_of(claims) == "d2"


def test_green_eventually_outranks_a_fresh_yellow_claim():
    # RED score = 300 + wait; YELLOW score = 200 + wait; GREEN score = 100 + wait
    # GREEN needs to wait > 100s to overtake a fresh (wait=0) YELLOW (200 vs 100).
    claims = [
        Claim("fresh-yellow", "amb-1", Severity.YELLOW, wait_seconds=0),
        Claim("old-green", "amb-2", Severity.GREEN, wait_seconds=150),
    ]
    assert winner_of(claims) == "old-green"


def test_fresh_red_beats_green_that_has_only_waited_a_little():
    # GREEN needs to wait > 200s to overtake a fresh RED (300 vs 100); 20s isn't enough.
    claims = [
        Claim("fresh-red", "amb-1", Severity.RED, wait_seconds=0),
        Claim("old-green", "amb-2", Severity.GREEN, wait_seconds=20),
    ]
    assert winner_of(claims) == "fresh-red"


def test_rank_claims_orders_descending_by_score():
    claims = [
        Claim("d-green", "amb-1", Severity.GREEN, wait_seconds=0),
        Claim("d-red", "amb-2", Severity.RED, wait_seconds=0),
        Claim("d-yellow", "amb-3", Severity.YELLOW, wait_seconds=0),
    ]
    ranked = rank_claims(claims)
    assert [r.dispatch_id for r in ranked] == ["d-red", "d-yellow", "d-green"]


def test_no_claims_has_no_winner():
    assert winner_of([]) is None
