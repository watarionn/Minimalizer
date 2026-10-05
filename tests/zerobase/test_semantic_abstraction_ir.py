from __future__ import annotations

import pytest

from minimalizer_zerobase.semantic_abstraction.ir import (
    AbstractionPlan,
    AbstractionPolicy,
    GeometryConstraints,
    SemanticPart,
    StructuralRole,
    TopologyConstraint,
    VisualRole,
)


def _part(part_id: str, *, category: str = "unknown") -> SemanticPart:
    return SemanticPart(
        id=part_id,
        category=category,
        confidence=0.75,
        structural_role=StructuralRole.BODY,
        visual_role=VisualRole.MAJOR_MASS,
        abstraction_policy=AbstractionPolicy.SIMPLIFY,
        topology_constraints=(
            TopologyConstraint(relation="connected", target_part_id="torso"),
        ),
        geometry_constraints=GeometryConstraints(
            allowed_families=("polygon",),
            min_primitives=1,
            max_primitives=2,
        ),
        source_regions=("region-b", "region-a"),
        evidence_refs=("observer:z", "observer:a"),
    )


def test_roundtrip_is_deterministic() -> None:
    original = AbstractionPlan(parts=(_part("arm", category="arm"),))
    payload = original.to_dict()
    assert AbstractionPlan.from_dict(payload).to_dict() == payload


def test_serialization_is_part_reorder_invariant() -> None:
    first = AbstractionPlan(parts=(_part("z"), _part("a"))).to_dict()
    second = AbstractionPlan(parts=(_part("a"), _part("z"))).to_dict()
    assert first == second


def test_unknown_is_preserved_as_fail_safe() -> None:
    part = SemanticPart.from_dict({"id": "u1", "category": "unknown"})
    assert part.category == "unknown"
    assert part.structural_role is StructuralRole.UNKNOWN
    assert part.visual_role is VisualRole.UNKNOWN
    assert part.abstraction_policy is AbstractionPolicy.CONDITIONAL


def test_duplicate_ids_fail_closed() -> None:
    with pytest.raises(ValueError, match="unique"):
        AbstractionPlan(parts=(_part("same"), _part("same")))


def test_invalid_geometry_budget_fails_closed() -> None:
    with pytest.raises(ValueError, match="max_primitives"):
        GeometryConstraints(min_primitives=2, max_primitives=1)
