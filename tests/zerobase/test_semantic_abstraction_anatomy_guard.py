from __future__ import annotations

from dataclasses import replace

from minimalizer_zerobase.semantic_abstraction.anatomy_guard import (
    anatomy_integrity_gate,
    anatomy_safe_or_fallback,
)
from minimalizer_zerobase.semantic_abstraction.ir import (
    AbstractionPlan,
    AbstractionPolicy,
    SemanticPart,
    TopologyConstraint,
)


def _baseline() -> AbstractionPlan:
    return AbstractionPlan(
        parts=(
            SemanticPart(id="head", category="head", bbox=(0.4, 0.1, 0.6, 0.25)),
            SemanticPart(id="torso", category="torso", bbox=(0.3, 0.25, 0.7, 0.65)),
            SemanticPart(
                id="left_arm",
                category="arm",
                bbox=(0.18, 0.3, 0.32, 0.68),
                topology_constraints=(
                    TopologyConstraint("attached_to", "torso", True),
                ),
            ),
            SemanticPart(
                id="right_arm",
                category="arm",
                bbox=(0.68, 0.3, 0.82, 0.68),
                topology_constraints=(
                    TopologyConstraint("attached_to", "torso", True),
                ),
            ),
        )
    )


def test_safe_candidate_passes() -> None:
    baseline = _baseline()
    candidate = AbstractionPlan(
        parts=tuple(replace(part, abstraction_policy=AbstractionPolicy.SIMPLIFY) for part in baseline.parts)
    )
    assert anatomy_integrity_gate(baseline, candidate).passed is True
    assert anatomy_safe_or_fallback(baseline, candidate) == candidate


def test_missing_arm_fails_and_falls_back() -> None:
    baseline = _baseline()
    candidate = AbstractionPlan(parts=tuple(part for part in baseline.parts if part.id != "left_arm"))
    result = anatomy_integrity_gate(baseline, candidate)
    assert result.passed is False
    assert result.missing_parts == ("left_arm",)
    assert anatomy_safe_or_fallback(baseline, candidate) == baseline


def test_dropped_required_attachment_fails() -> None:
    baseline = _baseline()
    candidate = AbstractionPlan(
        parts=tuple(
            replace(part, topology_constraints=())
            if part.id == "left_arm"
            else part
            for part in baseline.parts
        )
    )
    result = anatomy_integrity_gate(baseline, candidate)
    assert result.passed is False
    assert "left_arm:attached_to:torso" in result.missing_topology


def test_extreme_limb_bbox_change_fails() -> None:
    baseline = _baseline()
    candidate = AbstractionPlan(
        parts=tuple(
            replace(part, bbox=(0.20, 0.30, 0.22, 0.36))
            if part.id == "left_arm"
            else part
            for part in baseline.parts
        )
    )
    result = anatomy_integrity_gate(baseline, candidate)
    assert result.passed is False
    assert result.extreme_bbox_change == ("left_arm",)


def test_suppressed_limb_fails() -> None:
    baseline = _baseline()
    candidate = AbstractionPlan(
        parts=tuple(
            replace(part, abstraction_policy=AbstractionPolicy.SUPPRESS)
            if part.id == "right_arm"
            else part
            for part in baseline.parts
        )
    )
    result = anatomy_integrity_gate(baseline, candidate)
    assert result.passed is False
    assert result.suppressed_parts == ("right_arm",)
