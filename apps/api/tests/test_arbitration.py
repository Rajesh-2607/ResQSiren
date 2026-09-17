from app.junctions.arbitration import Claim, arbitrate


def test_no_holder_incoming_wins():
    incoming = Claim(dispatch_id="a", severity="RED", eta_seconds=20)
    result = arbitrate(incoming, None)
    assert result.winner is incoming
    assert result.loser is None
    assert result.reason == "NO_CONTENTION"


def test_higher_severity_wins():
    red = Claim(dispatch_id="red", severity="RED", eta_seconds=30)
    amber = Claim(dispatch_id="amber", severity="AMBER", eta_seconds=5)
    result = arbitrate(red, amber)
    assert result.winner is red
    assert result.loser is amber
    assert result.reason == "HIGHER_SEVERITY"


def test_lower_severity_incoming_loses_to_existing_holder():
    amber = Claim(dispatch_id="amber", severity="AMBER", eta_seconds=5)
    red_holder = Claim(dispatch_id="red", severity="RED", eta_seconds=30)
    result = arbitrate(amber, red_holder)
    assert result.winner is red_holder
    assert result.loser is amber
    assert result.reason == "HIGHER_SEVERITY"


def test_same_severity_lower_eta_wins():
    faster = Claim(dispatch_id="fast", severity="RED", eta_seconds=10)
    slower = Claim(dispatch_id="slow", severity="RED", eta_seconds=25)
    result = arbitrate(faster, slower)
    assert result.winner is faster
    assert result.loser is slower
    assert result.reason == "LOWER_ETA"


def test_same_severity_same_eta_incumbent_keeps_junction():
    holder = Claim(dispatch_id="holder", severity="GREEN", eta_seconds=15)
    incoming = Claim(dispatch_id="incoming", severity="GREEN", eta_seconds=15)
    result = arbitrate(incoming, holder)
    assert result.winner is holder
    assert result.loser is incoming
    assert result.reason == "INCUMBENT_TIEBREAK"
