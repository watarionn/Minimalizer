from __future__ import annotations

import pytest

from minimalizer_zerobase.golden_comparison.golden_gap import (
    DIMENSIONS,
    GoldenGapError,
    compare_golden_gap,
    evaluate_golden_gap,
)


def _survival(gate: str = "PASS") -> dict:
    return {
        "case_id": "synthetic",
        "gate": gate,
        "hard_failures": [] if gate == "PASS" else [{"feature_id": "core", "reason": "required_feature_absent"}],
    }


def _scores(value: float = 0.8) -> dict:
    return {name: value for name in DIMENSIONS}


def test_keeps_all_gap_dimensions_separate() -> None:
    report = evaluate_golden_gap(
        case_id="synthetic",
        feature_survival_report=_survival(),
        dimension_scores=_scores(),
    )
    assert tuple(report["dimensions"]) == DIMENSIONS
    assert report["diagnostic_mean"] == pytest.approx(0.8)


def test_hard_fail_cannot_be_rescued_by_perfect_gap_scores() -> None:
    report = evaluate_golden_gap(
        case_id="synthetic",
        feature_survival_report=_survival("FAIL"),
        dimension_scores=_scores(1.0),
        feature_local_evidence={"core": {"score": 1.0, "source": "dinov3"}},
    )
    assert report["gate"] == "FAIL"
    assert report["diagnostic_mean"] == 1.0
    assert report["diagnostic_mean_can_override_hard_fail"] is False
    assert report["feature_local_evidence_is_authority"] is False


def test_feature_local_dino_is_non_authoritative_evidence() -> None:
    report = evaluate_golden_gap(
        case_id="synthetic",
        feature_survival_report=_survival(),
        dimension_scores=_scores(),
        feature_local_evidence={"core": {"score": 0.99, "source": "dinov3"}},
    )
    assert report["feature_local_evidence"] == [{
        "feature_id": "core",
        "score": 0.99,
        "source": "dinov3",
        "authoritative": False,
    }]


@pytest.mark.parametrize("bad", [-0.1, 1.1, True, "1.0"])
def test_invalid_dimension_score_fails_closed(bad) -> None:
    scores = _scores()
    scores["geometry_abstraction"] = bad
    with pytest.raises(GoldenGapError):
        evaluate_golden_gap(
            case_id="synthetic",
            feature_survival_report=_survival(),
            dimension_scores=scores,
        )


def test_missing_or_unknown_dimension_fails_closed() -> None:
    missing = _scores()
    missing.pop("primitive_economy")
    with pytest.raises(GoldenGapError, match="missing"):
        evaluate_golden_gap(case_id="synthetic", feature_survival_report=_survival(), dimension_scores=missing)
    extra = _scores()
    extra["global_magic_score"] = 1.0
    with pytest.raises(GoldenGapError, match="unknown"):
        evaluate_golden_gap(case_id="synthetic", feature_survival_report=_survival(), dimension_scores=extra)


def test_case_mismatch_fails_closed() -> None:
    with pytest.raises(GoldenGapError, match="case_id"):
        evaluate_golden_gap(case_id="other", feature_survival_report=_survival(), dimension_scores=_scores())


def test_compare_reports_dimension_deltas_without_hiding_regressions() -> None:
    baseline = evaluate_golden_gap(
        case_id="synthetic", feature_survival_report=_survival(), dimension_scores=_scores(0.5)
    )
    scores = _scores(0.5)
    scores["geometry_abstraction"] = 0.8
    scores["palette_role_preservation"] = 0.4
    candidate = evaluate_golden_gap(
        case_id="synthetic", feature_survival_report=_survival(), dimension_scores=scores
    )
    comparison = compare_golden_gap(baseline, candidate)
    assert comparison["dimension_deltas"]["geometry_abstraction"] == pytest.approx(0.3)
    assert comparison["dimension_deltas"]["palette_role_preservation"] == pytest.approx(-0.1)
    assert "geometry_abstraction" in comparison["improvements"]
    assert "palette_role_preservation" in comparison["regressions"]


def test_failed_candidate_is_never_admissible_even_when_dimensions_improve() -> None:
    baseline = evaluate_golden_gap(
        case_id="synthetic", feature_survival_report=_survival(), dimension_scores=_scores(0.2)
    )
    candidate = evaluate_golden_gap(
        case_id="synthetic", feature_survival_report=_survival("FAIL"), dimension_scores=_scores(1.0)
    )
    comparison = compare_golden_gap(baseline, candidate)
    assert comparison["candidate_admissible"] is False
