import pytest

from minimalizer_zerobase.refine.semantic import SemanticObservation
from minimalizer_zerobase.semantic_abstraction.semantic_retention_observer import (
    SemanticRetentionStatus,
    evaluate_semantic_retention,
)
from minimalizer_zerobase.golden_comparison.golden_gap import (
    DIMENSIONS,
    GoldenGapError,
    evaluate_golden_gap,
)


def _obs(global_feature, patches=()):
    return SemanticObservation(
        tuple(float(v) for v in global_feature),
        tuple(tuple(float(v) for v in patch) for patch in patches),
    )


def _survival(gate="PASS"):
    return {
        "case_id": "synthetic",
        "gate": gate,
        "hard_failures": [] if gate == "PASS" else [
            {"feature_id": "core", "reason": "required_feature_absent"}
        ],
    }


def _dims(value=0.8):
    return {name: value for name in DIMENSIONS}


def test_identical_semantics_report_full_retention():
    source = _obs((1, 0), ((1, 0), (0, 1)))
    report = evaluate_semantic_retention(
        observer="synthetic",
        source=source,
        candidate=source,
        simplicity_score=0.9,
    )

    assert report.status is SemanticRetentionStatus.AVAILABLE
    assert report.global_similarity == pytest.approx(1.0)
    assert report.patch_similarity == pytest.approx(1.0)
    assert report.semantic_retention_score == pytest.approx(1.0)
    assert report.fidelity_score == pytest.approx(1.0)
    assert report.simplicity_score == pytest.approx(0.9)
    assert report.authoritative is False
    assert report.can_override_hard_fail is False


def test_semantic_damage_reduces_retention():
    source = _obs((1, 0), ((1, 0), (0, 1)))
    candidate = _obs((0, 1), ((0, 1), (0, 1)))

    report = evaluate_semantic_retention(
        observer="synthetic",
        source=source,
        candidate=candidate,
    )

    assert report.status is SemanticRetentionStatus.AVAILABLE
    assert report.global_similarity < 0.6
    assert report.patch_similarity < 1.0
    assert report.semantic_retention_score < 0.8


def test_patch_mismatch_degrades_but_keeps_global_evidence():
    source = _obs((1, 0), ((1, 0),))
    candidate = _obs((1, 0))

    report = evaluate_semantic_retention(
        observer="synthetic",
        source=source,
        candidate=candidate,
    )

    assert report.status is SemanticRetentionStatus.DEGRADED
    assert report.global_similarity == pytest.approx(1.0)
    assert report.patch_similarity is None
    assert "patch_feature_availability_mismatch" in report.reasons


def test_missing_global_observation_is_unavailable_not_production_failure():
    report = evaluate_semantic_retention(
        observer="dinov3",
        source=None,
        candidate=None,
    )

    assert report.status is SemanticRetentionStatus.UNAVAILABLE
    assert report.semantic_retention_score is None
    assert report.authoritative is False
    assert report.can_override_hard_fail is False


def test_role_local_retention_is_reported_without_becoming_authority():
    source = _obs((1, 0))
    candidate = _obs((1, 0))
    report = evaluate_semantic_retention(
        observer="synthetic",
        source=source,
        candidate=candidate,
        source_roles={
            "hair": _obs((1, 0)),
            "major_clothing": _obs((0, 1)),
        },
        candidate_roles={
            "hair": _obs((0.8, 0.2)),
            "major_clothing": _obs((0, 1)),
        },
    )

    assert report.status is SemanticRetentionStatus.AVAILABLE
    assert set(report.role_similarity) == {"hair", "major_clothing"}
    assert report.role_similarity["major_clothing"] == pytest.approx(1.0)
    assert report.authoritative is False


def test_missing_role_observation_degrades_report():
    report = evaluate_semantic_retention(
        observer="synthetic",
        source=_obs((1, 0)),
        candidate=_obs((1, 0)),
        source_roles={"hair": _obs((1, 0))},
        candidate_roles={},
    )

    assert report.status is SemanticRetentionStatus.DEGRADED
    assert "role_observation_missing:hair" in report.reasons


def test_golden_gap_records_retention_without_rescuing_hard_fail():
    retention = evaluate_semantic_retention(
        observer="synthetic",
        source=_obs((1, 0)),
        candidate=_obs((1, 0)),
    )
    report = evaluate_golden_gap(
        case_id="synthetic",
        feature_survival_report=_survival("FAIL"),
        dimension_scores=_dims(1.0),
        semantic_retention_report=retention.to_dict(),
    )

    assert report["gate"] == "FAIL"
    assert report["semantic_retention"]["semantic_retention_score"] == pytest.approx(1.0)
    assert report["semantic_retention_is_authority"] is False
    assert report["semantic_retention_can_override_hard_fail"] is False


def test_golden_gap_rejects_authoritative_retention_payload():
    payload = evaluate_semantic_retention(
        observer="synthetic",
        source=_obs((1, 0)),
        candidate=_obs((1, 0)),
    ).to_dict()
    payload["authoritative"] = True

    with pytest.raises(GoldenGapError, match="non-authoritative"):
        evaluate_golden_gap(
            case_id="synthetic",
            feature_survival_report=_survival(),
            dimension_scores=_dims(),
            semantic_retention_report=payload,
        )


def test_invalid_simplicity_score_fails_closed():
    with pytest.raises(ValueError, match="simplicity_score"):
        evaluate_semantic_retention(
            observer="synthetic",
            source=_obs((1, 0)),
            candidate=_obs((1, 0)),
            simplicity_score=1.1,
        )
