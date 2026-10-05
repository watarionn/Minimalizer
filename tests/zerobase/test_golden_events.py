from minimalizer_zerobase.golden_comparison.events import build_golden_evaluated_event

def report(score=0.80,case_id="GC001_IMG_1205",gate="PASS"):
    return {"schema_version":"1.0","case_id":case_id,"gate":gate,
      "hard_failures":[],"diagnostic_mean":score}

def test_build_event_from_real_report_shape():
    event=build_golden_evaluated_event(
      report(0.82),previous_report=report(0.79),run_id="run_42",
      occurred_at="2026-10-05T09:00:00+09:00",
      event_id="evt_test",correlation_id="corr_test")
    assert event["event_name"]=="minimalizer.golden.evaluated"
    assert event["payload"]["golden_id"]=="GC001_IMG_1205"
    assert event["payload"]["verdict"]=="improved"
    assert abs(event["payload"]["delta"]-0.03)<1e-9
    assert event["payload"]["gate"]=="PASS"

def test_first_evaluation_has_no_fake_delta():
    event=build_golden_evaluated_event(report(),run_id="run_first")
    assert event["payload"]["previous_score"] is None
    assert event["payload"]["delta"] is None
    assert event["payload"]["verdict"]=="evaluated"

def test_regression_is_reported():
    event=build_golden_evaluated_event(report(0.70),previous_report=report(0.80),run_id="run_regress")
    assert event["payload"]["verdict"]=="regressed"
    assert event["payload"]["delta"]<0

def test_cross_case_previous_report_is_rejected():
    try:
        build_golden_evaluated_event(report(),previous_report=report(case_id="other"),run_id="bad")
    except ValueError as exc:
        assert "case_id mismatch" in str(exc)
    else:
        raise AssertionError("expected ValueError")
