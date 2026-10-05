from __future__ import annotations

from dataclasses import replace

from .ir import AbstractionPlan, AbstractionPolicy, SemanticPart, VisualRole


def neutralize_face_policy(plan: AbstractionPlan) -> AbstractionPlan:
    """Preserve the outer face surface while suppressing only internal facial features.

    This stage is policy-only. It does not render, invent, or inpaint pixels.
    """
    result: list[SemanticPart] = []
    for part in plan.parts:
        if part.category == "face":
            result.append(
                replace(
                    part,
                    visual_role=VisualRole.MAJOR_MASS,
                    abstraction_policy=AbstractionPolicy.SIMPLIFY,
                    importance=max(part.importance, 0.7),
                )
            )
            continue
        if part.category == "facial_feature":
            result.append(
                replace(
                    part,
                    visual_role=VisualRole.INTERNAL_DETAIL,
                    abstraction_policy=AbstractionPolicy.SUPPRESS,
                    importance=0.0,
                )
            )
            continue
        result.append(part)
    return AbstractionPlan(parts=tuple(result), schema_version=plan.schema_version)


def face_neutralization_gate(plan: AbstractionPlan) -> dict[str, object]:
    forbidden = sorted(
        part.id
        for part in plan.parts
        if part.category == "facial_feature"
        and part.abstraction_policy is not AbstractionPolicy.SUPPRESS
    )
    face_surfaces = [
        part for part in plan.parts
        if part.category == "face"
        and part.abstraction_policy in {AbstractionPolicy.PRESERVE, AbstractionPolicy.SIMPLIFY}
    ]
    return {
        "pass": bool(face_surfaces) and not forbidden,
        "face_surface_count": len(face_surfaces),
        "unsuppressed_facial_features": forbidden,
    }
