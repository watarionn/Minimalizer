from __future__ import annotations

import json
from pathlib import Path

import pytest

from minimalizer_zerobase.golden_comparison.feature_survival import (
    FeatureSurvivalError,
    evaluate_feature_survival,
)
from minimalizer_zerobase.golden_comparison.semantic_manifest import load_semantic_manifest

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "benchmarks" / "golden" / "cases" / "GC001_IMG_1205.semantic.json"


def _manifest() -> dict:
    return load_semantic_manifest(CASE)


def _passing_evidence() -> dict:
    manifest = _manifest()
    result = {}
    for feature in manifest["features"]:
        state = "absent" if feature["disposition"] == "forbidden" else "present"
        result[feature["id"]] = {"state": state, "source": "synthetic-test", "confidence": 1.0}
    return result


def test_gc001_required_and_forbidden_features_pass_when_satisfied() -> None:
    report = evaluate_feature_survival(_manifest(), _passing_evidence(), perceptual_score=0.1)
    assert report["gate"] == "PASS"
    assert report["hard_failures"] == []


@pytest.mark.parametrize("feature_id", ["orange_hair", "goggles", "green_necktie", "navy_white_uniform"])
def test_required_feature_absence_is_hard_fail(feature_id: str) -> None:
    evidence = _passing_evidence()
    evidence[feature_id]["state"] = "absent"
    report = evaluate_feature_survival(_manifest(), evidence, perceptual_score=1.0)
    assert report["gate"] == "FAIL"
    assert {"feature_id": feature_id, "reason": "required_feature_absent"} in report["hard_failures"]
    assert report["perceptual_score_can_override_hard_fail"] is False


def test_required_feature_unknown_is_fail_closed_even_with_perfect_perceptual_score() -> None:
    evidence = _passing_evidence()
    evidence["goggles"] = {"state": "unknown", "source": "observer-disagreement", "confidence": 0.99}
    report = evaluate_feature_survival(_manifest(), evidence, perceptual_score=1.0)
    assert report["gate"] == "FAIL"
    assert {"feature_id": "goggles", "reason": "required_feature_unknown"} in report["hard_failures"]


def test_missing_required_evidence_is_fail_closed() -> None:
    evidence = _passing_evidence()
    del evidence["green_necktie"]
    report = evaluate_feature_survival(_manifest(), evidence)
    assert report["gate"] == "FAIL"
    assert {"feature_id": "green_necktie", "reason": "required_feature_unknown"} in report["hard_failures"]


def test_forbidden_feature_presence_is_hard_fail() -> None:
    evidence = _passing_evidence()
    evidence["facial_details"]["state"] = "present"
    report = evaluate_feature_survival(_manifest(), evidence, perceptual_score=1.0)
    assert report["gate"] == "FAIL"
    assert {"feature_id": "facial_details", "reason": "forbidden_feature_present"} in report["hard_failures"]


def test_forbidden_feature_unknown_is_fail_closed() -> None:
    evidence = _passing_evidence()
    evidence["facial_details"]["state"] = "unknown"
    report = evaluate_feature_survival(_manifest(), evidence)
    assert report["gate"] == "FAIL"
    assert {"feature_id": "facial_details", "reason": "forbidden_feature_unknown"} in report["hard_failures"]


def test_optional_feature_does_not_hard_fail_when_absent_or_unknown() -> None:
    for state in ("absent", "unknown"):
        evidence = _passing_evidence()
        evidence["hair_ornament"]["state"] = state
        report = evaluate_feature_survival(_manifest(), evidence)
        assert report["gate"] == "PASS"


def test_unknown_evidence_feature_is_rejected() -> None:
    evidence = _passing_evidence()
    evidence["case_specific_hack"] = {"state": "present", "source": "test"}
    with pytest.raises(FeatureSurvivalError, match="unknown feature"):
        evaluate_feature_survival(_manifest(), evidence)


def test_report_is_deterministic_for_same_input() -> None:
    evidence = _passing_evidence()
    first = evaluate_feature_survival(_manifest(), evidence, perceptual_score=0.75)
    second = evaluate_feature_survival(_manifest(), evidence, perceptual_score=0.75)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_observer_confidence_is_recorded_but_not_semantic_authority() -> None:
    evidence = _passing_evidence()
    evidence["goggles"] = {"state": "present", "source": "observer", "confidence": 0.01}
    report = evaluate_feature_survival(_manifest(), evidence, perceptual_score=0.0)
    assert report["gate"] == "PASS"
    goggles = next(row for row in report["feature_evidence"] if row["feature_id"] == "goggles")
    assert goggles["confidence"] == 0.01
