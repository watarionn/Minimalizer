from __future__ import annotations

from dataclasses import replace

from .ir import (
    AbstractionPlan,
    AbstractionPolicy,
    SemanticPart,
    StructuralRole,
    VisualRole,
)


def semantic_importance(part: SemanticPart) -> float:
    if part.category == "face" and part.visual_role is VisualRole.INTERNAL_DETAIL:
        return 0.0
    score = 0.0
    if part.visual_role is VisualRole.SILHOUETTE:
        score += 0.45
    elif part.visual_role is VisualRole.IDENTITY_ACCENT:
        score += 0.40
    elif part.visual_role is VisualRole.MAJOR_MASS:
        score += 0.30
    elif part.visual_role is VisualRole.INTERNAL_DETAIL:
        score += 0.05

    if part.structural_role in {StructuralRole.ROOT, StructuralRole.BODY, StructuralRole.CONNECTOR}:
        score += 0.30
    elif part.structural_role is StructuralRole.ATTACHED:
        score += 0.15

    if any(item.required for item in part.topology_constraints):
        score += 0.15

    score += min(max(part.confidence, 0.0), 1.0) * 0.10
    return round(min(score, 1.0), 6)


def decide_policy(part: SemanticPart, importance: float) -> AbstractionPolicy:
    if part.category == "face" and part.visual_role is VisualRole.INTERNAL_DETAIL:
        return AbstractionPolicy.SUPPRESS
    if part.visual_role is VisualRole.IDENTITY_ACCENT:
        return AbstractionPolicy.PRESERVE
    if part.structural_role in {StructuralRole.BODY, StructuralRole.CONNECTOR}:
        return AbstractionPolicy.SIMPLIFY
    if part.category == "unknown" or part.structural_role is StructuralRole.UNKNOWN:
        return AbstractionPolicy.CONDITIONAL
    if importance >= 0.70:
        return AbstractionPolicy.PRESERVE
    if importance >= 0.25:
        return AbstractionPolicy.SIMPLIFY
    return AbstractionPolicy.CONDITIONAL


def apply_importance_policy(plan: AbstractionPlan) -> AbstractionPlan:
    decided: list[SemanticPart] = []
    for part in plan.parts:
        importance = semantic_importance(part)
        decided.append(
            replace(
                part,
                importance=importance,
                abstraction_policy=decide_policy(part, importance),
            )
        )
    return AbstractionPlan(parts=tuple(decided), schema_version=plan.schema_version)
