import json
from unittest.mock import patch

import pytest

from minimalizer_zerobase.golden_comparison.golden_gap import DIMENSIONS
from minimalizer_zerobase.golden_comparison.runtime import (
    evaluate_golden_and_shadow,
    evaluate_golden_runtime,
    retry_golden_shadow,
)


def _survival(case_id="case_runtime", gate="PASS"):
    return {"case_id":case_id,"gate":gate,"hard_failures":[]}


def _scores(value=0.8):
    return {name:value for name in DIMENSIONS}


class Response:
    def __init__(self, event_id, state="STORED"):
        self.status=200
        self.event_id=event_id
        self.state=state
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,n):
        return json.dumps({"event_id":self.event_id,"state":self.state}).encode()


def test_real_runtime_callsite_evaluates_then_delivers():
    env={
        "RINKA_EVENT_HUB_URL":"https://hub.example",
        "RINKA_EVENT_HUB_TOKEN":"test-token",
    }
    with patch("minimalizer_zerobase.golden_comparison.event_hub_client.urlopen") as call:
        call.side_effect=lambda req,timeout: Response(json.loads(req.data)["event_id"])
        result=evaluate_golden_runtime(
            case_id="case_runtime",
            feature_survival_report=_survival(),
            dimension_scores=_scores(0.82),
            run_id="run_runtime",
            environ=env,
            occurred_at="2026-10-05T03:00:00+00:00",
        )
    assert result.report["gate"]=="PASS"
    assert result.event["event_name"]=="minimalizer.golden.evaluated"
    assert result.event["payload"]["score"]==pytest.approx(0.82)
    assert result.delivery.delivered is True
    assert result.integration_error is None


def test_event_hub_outage_cannot_fail_native_evaluation():
    def outage(_):
        raise ConnectionError("hub unavailable")
    result=evaluate_golden_and_shadow(
        case_id="case_runtime",
        feature_survival_report=_survival(),
        dimension_scores=_scores(),
        run_id="run_outage",
        send=outage,
        occurred_at="2026-10-05T03:01:00+00:00",
    )
    assert result.report["gate"]=="PASS"
    assert result.event is not None
    assert result.delivery.delivered is False
    assert result.delivery.error=="ConnectionError"


def test_event_construction_problem_is_fail_open_after_report_exists():
    result=evaluate_golden_and_shadow(
        case_id="case_runtime",
        feature_survival_report=_survival(),
        dimension_scores=_scores(),
        run_id="run_bad_previous",
        previous_report={"case_id":"different","gate":"PASS","diagnostic_mean":0.7},
    )
    assert result.report["gate"]=="PASS"
    assert result.event is None
    assert result.delivery is None
    assert result.integration_error=="ValueError"


def test_retry_reuses_exact_frozen_envelope_without_rebuild():
    first_seen=[]
    def first_outage(event):
        first_seen.append(json.dumps(event,sort_keys=True,separators=(",",":")))
        raise TimeoutError("first delivery failed")
    result=evaluate_golden_and_shadow(
        case_id="case_runtime",
        feature_survival_report=_survival(),
        dimension_scores=_scores(),
        run_id="run_retry",
        send=first_outage,
        occurred_at="2026-10-05T03:02:00+00:00",
    )
    event_object=result.event
    second_seen=[]
    retry=retry_golden_shadow(
        result,
        lambda event: second_seen.append(json.dumps(event,sort_keys=True,separators=(",",":"))),
    )
    assert retry.delivered is True
    assert result.event is event_object
    assert second_seen==first_seen


def test_missing_environment_disables_shadow_without_affecting_evaluation():
    result=evaluate_golden_runtime(
        case_id="case_runtime",
        feature_survival_report=_survival(),
        dimension_scores=_scores(),
        run_id="run_disabled",
        environ={},
    )
    assert result.report["gate"]=="PASS"
    assert result.delivery.attempted is False
    assert result.delivery.delivered is False


def test_partial_environment_is_contained_by_fail_open_boundary():
    result=evaluate_golden_runtime(
        case_id="case_runtime",
        feature_survival_report=_survival(),
        dimension_scores=_scores(),
        run_id="run_partial_env",
        environ={"RINKA_EVENT_HUB_URL":"https://hub.example"},
    )
    assert result.report["gate"]=="PASS"
    assert result.delivery.attempted is True
    assert result.delivery.delivered is False
    assert result.delivery.error=="ValueError"
