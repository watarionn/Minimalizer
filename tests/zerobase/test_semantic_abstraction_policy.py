from __future__ import annotations

from minimalizer_zerobase.semantic_abstraction.ir import (
    AbstractionPlan,
    AbstractionPolicy,
    SemanticPart,
    StructuralRole,
    TopologyConstraint,
    VisualRole,
)
from minimalizer_zerobase.semantic_abstraction.policy import apply_importance_policy


def test_face_internal_detail_is_suppressed() -> None:
    plan = apply_importance_policy(
        AbstractionPlan(
            parts=(
                SemanticPart(
                    id="face",
                    category="face",
                    confidence=1.0,
                    structural_role=StructuralRole.BODY,
                    visual_role=VisualRole.INTERNAL_DETAIL,
                ),
            )
        )
    )
    assert plan.parts[0].importance == 0.0
    assert plan.parts[0].abstraction_policy is AbstractionPolicy.SUPPRESS


def test_identity_accent_is_preserved_even_when_compact() -> None:
    part = SemanticPart(
        id="accent",
        category="accessory",
        confidence=0.4,
        structural_role=StructuralRole.ATTACHED,
        visual_role=VisualRole.IDENTITY_ACCENT,
    )
    result = apply_importance_policy(AbstractionPlan(parts=(part,))).parts[0]
    assert result.abstraction_policy is AbstractionPolicy.PRESERVE


def test_body_connector_is_simplified_not_deleted() -> None:
    part = SemanticPart(
        id="arm",
        category="arm",
        confidence=0.2,
        structural_role=StructuralRole.CONNECTOR,
        visual_role=VisualRole.MAJOR_MASS,
        topology_constraints=(TopologyConstraint("connected_to", "torso"),),
    )
    result = apply_importance_policy(AbstractionPlan(parts=(part,))).parts[0]
    assert result.importance >= 0.7
    assert result.abstraction_policy is AbstractionPolicy.SIMPLIFY


def test_unknown_remains_conditional() -> None:
    part = SemanticPart(id="u", category="unknown")
    result = apply_importance_policy(AbstractionPlan(parts=(part,))).parts[0]
    assert result.abstraction_policy is AbstractionPolicy.CONDITIONAL


def test_policy_is_reorder_invariant() -> None:
    a = SemanticPart(id="a", category="hair", visual_role=VisualRole.IDENTITY_ACCENT)
    b = SemanticPart(id="b", category="torso", structural_role=StructuralRole.BODY)
    left = apply_importance_policy(AbstractionPlan(parts=(a, b))).to_dict()
    right = apply_importance_policy(AbstractionPlan(parts=(b, a))).to_dict()
    assert left == right
