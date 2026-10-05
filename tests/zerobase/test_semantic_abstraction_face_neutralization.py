from __future__ import annotations

from minimalizer_zerobase.semantic_abstraction.face_neutralization import (
    face_neutralization_gate,
    neutralize_face_policy,
)
from minimalizer_zerobase.semantic_abstraction.ir import (
    AbstractionPlan,
    AbstractionPolicy,
    SemanticPart,
    VisualRole,
)


def test_face_surface_is_kept_but_simplified() -> None:
    result = neutralize_face_policy(
        AbstractionPlan(parts=(SemanticPart(id="face", category="face"),))
    )
    face = result.parts[0]
    assert face.abstraction_policy is AbstractionPolicy.SIMPLIFY
    assert face.visual_role is VisualRole.MAJOR_MASS
    assert face.importance >= 0.7


def test_facial_feature_is_suppressed() -> None:
    result = neutralize_face_policy(
        AbstractionPlan(
            parts=(
                SemanticPart(
                    id="eye-like-1",
                    category="facial_feature",
                    abstraction_policy=AbstractionPolicy.PRESERVE,
                ),
            )
        )
    )
    feature = result.parts[0]
    assert feature.abstraction_policy is AbstractionPolicy.SUPPRESS
    assert feature.importance == 0.0


def test_gate_requires_face_surface() -> None:
    assert face_neutralization_gate(AbstractionPlan(parts=()))["pass"] is False


def test_gate_rejects_unsuppressed_eye_like_feature() -> None:
    plan = AbstractionPlan(
        parts=(
            SemanticPart(id="face", category="face", abstraction_policy=AbstractionPolicy.SIMPLIFY),
            SemanticPart(
                id="eye-like-1",
                category="facial_feature",
                abstraction_policy=AbstractionPolicy.PRESERVE,
            ),
        )
    )
    gate = face_neutralization_gate(plan)
    assert gate["pass"] is False
    assert gate["unsuppressed_facial_features"] == ["eye-like-1"]


def test_neutralized_plan_passes_policy_gate() -> None:
    plan = neutralize_face_policy(
        AbstractionPlan(
            parts=(
                SemanticPart(id="face", category="face"),
                SemanticPart(id="eye-like-1", category="facial_feature"),
            )
        )
    )
    assert face_neutralization_gate(plan)["pass"] is True
