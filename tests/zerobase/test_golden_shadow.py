from minimalizer_zerobase.golden_comparison.events import build_golden_evaluated_event
from minimalizer_zerobase.golden_comparison.shadow import deliver_shadow

def event():
    return build_golden_evaluated_event(
        {"case_id":"GC001","gate":"PASS","diagnostic_mean":0.8,"hard_failures":[]},
        run_id="run_shadow",
        occurred_at="2026-10-05T10:00:00+09:00",
    )

def test_shadow_success_reports_delivery():
    seen=[]
    result=deliver_shadow(event(),lambda item: seen.append(item["event_id"]))
    assert result.attempted is True
    assert result.delivered is True
    assert result.error is None
    assert result.state is None
    assert seen==[result.event_id]

def test_shadow_retains_hub_state_for_evidence():
    result=deliver_shadow(event(),lambda _: {"state":"STORED"})
    assert result.delivered is True
    assert result.state=="STORED"

def test_shadow_outage_never_raises_into_minimalizer():
    def outage(_):
        raise ConnectionError("event hub unavailable")
    result=deliver_shadow(event(),outage)
    assert result.attempted is True
    assert result.delivered is False
    assert result.error=="ConnectionError"
    assert result.state is None

def test_shadow_disabled_is_noop():
    result=deliver_shadow(event(),None)
    assert result.attempted is False
    assert result.delivered is False
    assert result.error is None
    assert result.state is None

def test_shadow_requires_event_identity():
    try:
        deliver_shadow({},lambda _: None)
    except ValueError as exc:
        assert "requires event_id" in str(exc)
    else:
        raise AssertionError("expected ValueError")
