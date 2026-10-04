from __future__ import annotations

import pytest

from minimalizer_zerobase.golden_comparison.guarded_diffmin import (
    GuardedDiffMinError,
    prepare_diffmin_refinement,
    validate_diffmin_result,
)


def _survival(gate: str = "PASS") -> dict:
    return {"case_id": "synthetic", "gate": gate, "hard_failures": []}


def _plan() -> dict:
    return {
        "case_id": "synthetic",
        "primitives": [
            {"feature_id": "core", "primitive_kind": "polygon", "ordinal": 0},
            {"feature_id": "core", "primitive_kind": "ellipse", "ordinal": 1},
        ],
    }


def test_diffmin_is_off_by_default() -> None:
    contract = prepare_diffmin_refinement(
        feature_survival_report=_survival(),
        geometry_plan=_plan(),
        baseline_renderer="svg",
        candidate_renderer="svg",
    )
    assert contract["status"] == "SKIPPED"
    assert contract["reason"] == "diffmin_default_off"


def test_diffmin_requires_pre_refinement_hard_gate_pass() -> None:
    with pytest.raises(GuardedDiffMinError, match="hard-gate-PASS"):
        prepare_diffmin_refinement(
            enabled=True,
            feature_survival_report=_survival("FAIL"),
            geometry_plan=_plan(),
            baseline_renderer="svg",
            candidate_renderer="svg",
        )


def test_diffmin_requires_same_renderer_baseline() -> None:
    with pytest.raises(GuardedDiffMinError, match="same renderer"):
        prepare_diffmin_refinement(
            enabled=True,
            feature_survival_report=_survival(),
            geometry_plan=_plan(),
            baseline_renderer="svg",
            candidate_renderer="raster",
        )


def test_diffmin_cannot_add_missing_semantic_part() -> None:
    requested = _plan()["primitives"] + [
        {"feature_id": "new_goggles", "primitive_kind": "ring", "ordinal": 0}
    ]
    with pytest.raises(GuardedDiffMinError, match="cannot change authored primitive"):
        prepare_diffmin_refinement(
            enabled=True,
            feature_survival_report=_survival(),
            geometry_plan=_plan(),
            baseline_renderer="svg",
            candidate_renderer="svg",
            requested_primitives=requested,
        )


def test_diffmin_cannot_delete_authored_primitive() -> None:
    with pytest.raises(GuardedDiffMinError, match="cannot change authored primitive"):
        prepare_diffmin_refinement(
            enabled=True,
            feature_survival_report=_survival(),
            geometry_plan=_plan(),
            baseline_renderer="svg",
            candidate_renderer="svg",
            requested_primitives=_plan()["primitives"][:1],
        )


def test_ready_contract_only_allows_existing_geometry_parameters() -> None:
    contract = prepare_diffmin_refinement(
        enabled=True,
        feature_survival_report=_survival(),
        geometry_plan=_plan(),
        baseline_renderer="svg",
        candidate_renderer="svg",
    )
    assert contract["status"] == "READY"
    assert contract["optimization_scope"] == "parameters_of_existing_authored_geometry_only"
    assert contract["may_create_semantic_parts"] is False
    assert contract["may_change_primitive_count"] is False


def test_post_refinement_hard_gate_must_still_pass() -> None:
    contract = prepare_diffmin_refinement(
        enabled=True,
        feature_survival_report=_survival(),
        geometry_plan=_plan(),
        baseline_renderer="svg",
        candidate_renderer="svg",
    )
    with pytest.raises(GuardedDiffMinError, match="post-refinement hard gate"):
        validate_diffmin_result(
            contract,
            resulting_primitives=_plan()["primitives"],
            post_feature_survival_report=_survival("FAIL"),
        )


def test_result_must_preserve_primitive_identity_and_count() -> None:
    contract = prepare_diffmin_refinement(
        enabled=True,
        feature_survival_report=_survival(),
        geometry_plan=_plan(),
        baseline_renderer="svg",
        candidate_renderer="svg",
    )
    changed = [
        {"feature_id": "core", "primitive_kind": "polygon", "ordinal": 0},
        {"feature_id": "core", "primitive_kind": "ring", "ordinal": 1},
    ]
    with pytest.raises(GuardedDiffMinError, match="changed authored primitive"):
        validate_diffmin_result(
            contract,
            resulting_primitives=changed,
            post_feature_survival_report=_survival(),
        )


def test_valid_refinement_contract_passes() -> None:
    contract = prepare_diffmin_refinement(
        enabled=True,
        feature_survival_report=_survival(),
        geometry_plan=_plan(),
        baseline_renderer="svg",
        candidate_renderer="svg",
    )
    report = validate_diffmin_result(
        contract,
        resulting_primitives=list(reversed(_plan()["primitives"])),
        post_feature_survival_report=_survival(),
    )
    assert report["status"] == "PASS"
    assert report["primitive_identity_preserved"] is True
