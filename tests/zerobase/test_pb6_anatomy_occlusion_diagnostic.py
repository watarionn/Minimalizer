from __future__ import annotations

from dataclasses import replace

import numpy as np

from minimalizer_zerobase.semantic_abstraction.anatomy_guard import anatomy_integrity_gate
from minimalizer_zerobase.semantic_abstraction.anatomy_occlusion_diagnostic import (
    AnatomyRelationCompatibility,
    build_anatomy_occlusion_diagnostic,
)
from minimalizer_zerobase.semantic_abstraction.ir import (
    AbstractionPlan,
    AbstractionPolicy,
    SemanticPart,
    TopologyConstraint,
)


def _plan() -> AbstractionPlan:
    return AbstractionPlan(parts=(
        SemanticPart(id="head", category="head", bbox=(0.3, 0.0, 0.7, 0.3)),
        SemanticPart(id="torso", category="torso", bbox=(0.3, 0.3, 0.7, 0.8)),
        SemanticPart(id="left_arm", category="arm", bbox=(0.1, 0.3, 0.3, 0.8),
                     topology_constraints=(TopologyConstraint("attached_to", "torso", True),)),
        SemanticPart(id="right_arm", category="arm", bbox=(0.7, 0.3, 0.9, 0.8),
                     topology_constraints=(TopologyConstraint("attached_to", "torso", True),)),
        SemanticPart(id="lower_body", category="leg", bbox=(0.3, 0.8, 0.7, 1.0)),
        SemanticPart(id="hair", category="hair"),
    ))


def _mask(y0: int, y1: int, x0: int, x1: int) -> np.ndarray:
    value = np.zeros((12, 12), dtype=np.uint8)
    value[y0:y1, x0:x1] = 1
    return value


def _relation(report, a: str, b: str):
    return next(row for row in report.relations if {row.role_a, row.role_b} == {a, b})


def test_required_attachment_touch_is_supporting_without_mutating_plan() -> None:
    plan = _plan()
    before = plan.to_dict()
    report = build_anatomy_occlusion_diagnostic(
        plan=plan,
        role_masks={"left_arm": _mask(3, 8, 1, 3), "torso": _mask(3, 8, 4, 8)},
    )
    row = _relation(report, "left_arm", "torso")
    assert row.compatibility is AnatomyRelationCompatibility.SUPPORTING
    assert row.production_authority is False
    assert row.production_action is None
    assert plan.to_dict() == before


def test_required_attachment_disjoint_is_diagnostic_conflict_only() -> None:
    plan = _plan()
    report = build_anatomy_occlusion_diagnostic(
        plan=plan,
        role_masks={"left_arm": _mask(3, 8, 0, 2), "torso": _mask(3, 8, 7, 10)},
    )
    row = _relation(report, "left_arm", "torso")
    assert row.compatibility is AnatomyRelationCompatibility.POTENTIAL_CONFLICT
    assert report.production_authority_count == 0
    assert report.production_output_changed is False


def test_overlap_without_topology_never_invents_direction() -> None:
    report = build_anatomy_occlusion_diagnostic(
        plan=_plan(),
        role_masks={"hair": _mask(0, 5, 3, 8), "head": _mask(1, 6, 4, 9)},
    )
    row = _relation(report, "hair", "head")
    assert row.compatibility is AnatomyRelationCompatibility.INSUFFICIENT_EVIDENCE
    assert row.front_role is None
    assert row.back_role is None
    assert row.direction_source == "unavailable"


def test_canonical_z_order_is_observed_but_not_changed() -> None:
    z_order = {"hair": 9, "head": 4}
    before = dict(z_order)
    report = build_anatomy_occlusion_diagnostic(
        plan=_plan(),
        role_masks={"hair": _mask(0, 5, 3, 8), "head": _mask(1, 6, 4, 9)},
        role_z_order=z_order,
    )
    row = _relation(report, "hair", "head")
    assert row.front_role == "hair"
    assert row.back_role == "head"
    assert row.direction_source == "canonical_z_order_observation"
    assert z_order == before


def test_anatomy_guard_pass_remains_independent_of_diagnostic() -> None:
    plan = _plan()
    report = build_anatomy_occlusion_diagnostic(
        plan=plan,
        role_masks={"left_arm": _mask(3, 8, 1, 3), "torso": _mask(3, 8, 4, 8)},
    )
    assert _relation(report, "left_arm", "torso").compatibility is AnatomyRelationCompatibility.SUPPORTING
    assert anatomy_integrity_gate(plan, plan).passed is True


def test_observer_support_cannot_rescue_guard_failure_or_missing_topology() -> None:
    baseline = _plan()
    candidate = AbstractionPlan(parts=tuple(
        replace(part, topology_constraints=()) if part.id == "left_arm" else part
        for part in baseline.parts
    ))
    report = build_anatomy_occlusion_diagnostic(
        plan=baseline,
        role_masks={"left_arm": _mask(3, 8, 1, 3), "torso": _mask(3, 8, 4, 8)},
    )
    assert _relation(report, "left_arm", "torso").compatibility is AnatomyRelationCompatibility.SUPPORTING
    result = anatomy_integrity_gate(baseline, candidate)
    assert result.passed is False
    assert "left_arm:attached_to:torso" in result.missing_topology


def test_observer_cannot_create_or_rescue_missing_anatomy_part() -> None:
    baseline = _plan()
    candidate = AbstractionPlan(parts=tuple(p for p in baseline.parts if p.id != "right_arm"))
    build_anatomy_occlusion_diagnostic(
        plan=baseline,
        role_masks={"right_arm": _mask(3, 8, 8, 10), "torso": _mask(3, 8, 4, 7)},
    )
    result = anatomy_integrity_gate(baseline, candidate)
    assert result.passed is False
    assert result.missing_parts == ("right_arm",)


def test_mapping_order_is_deterministic_and_inputs_are_not_mutated() -> None:
    plan = _plan()
    masks_a = {"torso": _mask(3, 8, 4, 8), "left_arm": _mask(3, 8, 1, 3), "hair": _mask(0, 3, 4, 7)}
    masks_b = dict(reversed(list(masks_a.items())))
    snapshots = {key: value.copy() for key, value in masks_a.items()}
    first = build_anatomy_occlusion_diagnostic(plan=plan, role_masks=masks_a).to_dict()
    second = build_anatomy_occlusion_diagnostic(plan=plan, role_masks=masks_b).to_dict()
    assert first == second
    for key, value in snapshots.items():
        assert np.array_equal(masks_a[key], value)


def test_suppressed_anatomy_still_fails_despite_diagnostic() -> None:
    baseline = _plan()
    candidate = AbstractionPlan(parts=tuple(
        replace(part, abstraction_policy=AbstractionPolicy.SUPPRESS)
        if part.id == "left_arm" else part
        for part in baseline.parts
    ))
    build_anatomy_occlusion_diagnostic(
        plan=baseline,
        role_masks={"left_arm": _mask(3, 8, 1, 3), "torso": _mask(3, 8, 4, 8)},
    )
    result = anatomy_integrity_gate(baseline, candidate)
    assert result.passed is False
    assert result.suppressed_parts == ("left_arm",)
