from __future__ import annotations

from copy import deepcopy

from minimalizer_zerobase.evaluation.regression_transaction import (
    HARD_GATE_NAMES,
    build_regression_transaction,
)


SOURCE_SHA = "a" * 64
BASELINE_SHA = "b" * 64
CANDIDATE_SHA = "c" * 64


def _bundle():
    hard_rows = {
        "feature_survival": {"status": "AVAILABLE", "passed": True},
        "forbidden_face_detail": {"status": "AVAILABLE", "passed": True},
        "anatomy": {"status": "AVAILABLE", "passed": True},
        "topology": {"status": "AVAILABLE", "passed": True},
        "source_authority": {"status": "AVAILABLE", "passed": True},
        "phase14_machine": {"status": "AVAILABLE", "passed": True},
        "phase14_human_visual": {"status": "AVAILABLE", "passed": True},
        "determinism": {"status": "AVAILABLE", "passed": True},
    }
    case = {
        "case_id": "synthetic",
        "source": {"sha256": SOURCE_SHA},
        "provenance": {"production_candidate_sha256": CANDIDATE_SHA},
        "hard_evidence": deepcopy(hard_rows),
        "diagnostics": {
            "semantic_retention": {"status": "AVAILABLE", "value": 1.0},
            "adaptive_complexity": {"status": "AVAILABLE", "value": 1.0},
            "component_survival": {"status": "AVAILABLE", "value": 1.0},
            "primitive_economy": {"status": "AVAILABLE", "value": 1.0},
            "teacher_coverage": {"status": "UNAVAILABLE", "reason": "synthetic"},
            "teacher_primitive_disagreements": {
                "status": "UNAVAILABLE",
                "reason": "synthetic",
            },
        },
    }
    adoption = {
        "version": "sa10.12-v1",
        "case_id": "synthetic",
        "source_sha256": SOURCE_SHA,
        "baseline_artifact_sha256": BASELINE_SHA,
        "baseline_origin": "synthetic-reviewed",
        "baseline_artifact_id": "baseline-1",
        "review_status": "ADOPTED",
        "reviewer": "tester",
        "review_evidence": ["synthetic-review"],
        "adoption_transaction_id": "adopt-1",
        "immutable_record": True,
        "evaluation_baseline_allowed": True,
        "production_inference_allowed": False,
        "candidate_self_reference_forbidden": True,
    }
    visual = {
        "case_id": "synthetic",
        "binding": {
            "case_id": "synthetic",
            "source_sha256": SOURCE_SHA,
            "baseline_artifact_sha256": BASELINE_SHA,
            "candidate_artifact_sha256": CANDIDATE_SHA,
            "binding_passed": True,
            "evaluation_transaction_id": "tx-1",
            "same_transaction": False,
            "production_inference_allowed": False,
            "candidate_self_reference_forbidden": True,
        },
        "feature_survival": {"status": "AVAILABLE", "passed": True},
        "forbidden_face_detail": {"status": "AVAILABLE", "passed": True},
    }
    hard = {
        "case_id": "synthetic",
        "source": {"sha256": SOURCE_SHA},
        "production_candidate": {"sha256": CANDIDATE_SHA},
        "hard_evidence": {
            "anatomy": {"status": "AVAILABLE", "passed": True},
            "topology": {"status": "AVAILABLE", "passed": True},
            "source_authority": {"status": "AVAILABLE", "passed": True},
        },
        "actual_emission_support": {
            "diagnostic_only": True,
            "maps_to_sa10_component_survival": False,
            "maps_to_sa10_primitive_economy": False,
        },
    }
    phase14 = {
        "case_id": "synthetic",
        "source": {"sha256": SOURCE_SHA},
        "machine_pass": True,
        "human_visual_qa": {"passed": True},
        "determinism": {"passed": True},
        "pass": True,
    }
    semantic = {
        "case_id": "synthetic",
        "source": {"sha256": SOURCE_SHA},
        "candidate": {"sha256": CANDIDATE_SHA},
        "hard_gate_override_allowed": False,
        "production_output_changed": False,
        "semantic_retention": {
            "status": "AVAILABLE",
            "semantic_retention_score": 1.0,
            "authoritative": False,
            "can_override_hard_fail": False,
        },
    }
    guard = {
        "case_id": "synthetic",
        "production_candidate_sha256": CANDIDATE_SHA,
        "source_only": True,
        "generated_or_inpainted_pixel_count": 0,
        "face_raster_guard": {"changed_outside_face_pixels": 0},
    }
    return case, adoption, visual, hard, phase14, semantic, guard


def _build(bundle):
    case, adoption, visual, hard, phase14, semantic, guard = bundle
    return build_regression_transaction(
        transaction_id="tx-1",
        case=case,
        adoption_record=adoption,
        actual_source_sha256=SOURCE_SHA,
        actual_candidate_sha256=CANDIDATE_SHA,
        visual_hard_gate=visual,
        hard_evidence=hard,
        phase14=phase14,
        semantic_retention=semantic,
        face_raster_guard=guard,
    )


def test_all_hard_evidence_passes_without_aggregate_score():
    report = _build(_bundle())
    assert report.pass_transaction is True
    payload = report.to_dict()
    assert [row["name"] for row in payload["hard_evidence"]] == list(HARD_GATE_NAMES)
    assert all(row["passed"] for row in payload["hard_evidence"])
    assert payload["boundary"]["aggregate_quality_score"] is False
    assert payload["boundary"]["diagnostics_can_override_hard_fail"] is False


def test_face_hard_fail_cannot_be_rescued_by_perfect_diagnostics():
    bundle = list(_bundle())
    bundle[0]["hard_evidence"]["forbidden_face_detail"]["passed"] = False
    bundle[2]["forbidden_face_detail"]["passed"] = False
    report = _build(tuple(bundle))
    assert report.diagnostics["semantic_retention"]["value"] == 1.0
    assert report.pass_transaction is False


def test_anatomy_hard_fail_cannot_be_rescued_by_perfect_diagnostics():
    bundle = list(_bundle())
    bundle[0]["hard_evidence"]["anatomy"]["passed"] = False
    bundle[3]["hard_evidence"]["anatomy"]["passed"] = False
    report = _build(tuple(bundle))
    assert report.diagnostics["semantic_retention"]["value"] == 1.0
    assert report.pass_transaction is False


def test_source_authority_fail_cannot_be_rescued_by_perfect_diagnostics():
    bundle = list(_bundle())
    bundle[0]["hard_evidence"]["source_authority"]["passed"] = False
    bundle[3]["hard_evidence"]["source_authority"]["passed"] = False
    report = _build(tuple(bundle))
    assert report.diagnostics["semantic_retention"]["value"] == 1.0
    assert report.pass_transaction is False


def test_cross_link_mismatch_fails_transaction():
    bundle = list(_bundle())
    bundle[6]["production_candidate_sha256"] = "d" * 64
    report = _build(tuple(bundle))
    assert report.evidence_links["candidate_matches_face_guard"] is False
    assert report.pass_transaction is False


def test_raden_style_emission_gap_remains_diagnostic_only():
    bundle = list(_bundle())
    bundle[3]["actual_emission_support"] = {
        "diagnostic_only": True,
        "emission_realization_ratio": 0.5,
        "maps_to_sa10_component_survival": False,
        "maps_to_sa10_primitive_economy": False,
    }
    report = _build(tuple(bundle))
    actual = report.diagnostics["actual_emission_support"]
    assert actual["diagnostic_only"] is True
    assert actual["emission_realization_ratio"] == 0.5
    assert actual["maps_to_sa10_component_survival"] is False
    assert actual["maps_to_sa10_primitive_economy"] is False
    assert report.pass_transaction is True
