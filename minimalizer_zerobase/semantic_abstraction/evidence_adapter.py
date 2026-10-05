from __future__ import annotations

from typing import Mapping

import numpy as np

from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.structure.graph import StructuralLayoutGraph

from .ir import (
    AbstractionPlan,
    AbstractionPolicy,
    GeometryConstraints,
    SemanticPart,
    StructuralRole,
    TopologyConstraint,
    VisualRole,
)


_BODY_PARTS = {"head", "neck", "torso", "left_arm", "right_arm", "lower_body"}
_IDENTITY_PARTS = {"hair", "major_clothing", "accessory_or_held_object"}


def _bbox_normalized(mask: np.ndarray) -> tuple[float, float, float, float] | None:
    ys, xs = np.where(np.asarray(mask).astype(bool))
    if xs.size == 0:
        return None
    height, width = mask.shape
    return (
        float(xs.min()) / width,
        float(ys.min()) / height,
        float(xs.max() + 1) / width,
        float(ys.max() + 1) / height,
    )


def _roles(part_id: str) -> tuple[StructuralRole, VisualRole, AbstractionPolicy]:
    if part_id == "unknown":
        return StructuralRole.UNKNOWN, VisualRole.UNKNOWN, AbstractionPolicy.CONDITIONAL
    if part_id == "face":
        return StructuralRole.BODY, VisualRole.INTERNAL_DETAIL, AbstractionPolicy.SUPPRESS
    if part_id in _BODY_PARTS:
        return StructuralRole.BODY, VisualRole.SILHOUETTE, AbstractionPolicy.SIMPLIFY
    if part_id in _IDENTITY_PARTS:
        return StructuralRole.ATTACHED, VisualRole.IDENTITY_ACCENT, AbstractionPolicy.PRESERVE
    return StructuralRole.ATTACHED, VisualRole.MAJOR_MASS, AbstractionPolicy.CONDITIONAL


def _constraints(
    part_id: str,
    graph: StructuralLayoutGraph,
) -> tuple[TopologyConstraint, ...]:
    items: list[TopologyConstraint] = []
    for relation in graph.relations:
        if relation.source_part == part_id:
            items.append(
                TopologyConstraint(
                    relation=relation.relation_kind,
                    target_part_id=relation.target_part,
                    required=relation.confidence >= 0.5,
                )
            )
        elif relation.target_part == part_id:
            items.append(
                TopologyConstraint(
                    relation=f"inverse:{relation.relation_kind}",
                    target_part_id=relation.source_part,
                    required=relation.confidence >= 0.5,
                )
            )
    return tuple(sorted(items, key=lambda item: (item.relation, item.target_part_id)))


def build_semantic_abstraction_evidence(
    *,
    part_masks: Mapping[str, np.ndarray],
    graph: StructuralLayoutGraph,
) -> AbstractionPlan:
    missing = [name for name in PART_NAMES if name not in part_masks]
    if missing:
        raise ValueError(f"missing Phase 4 part masks: {missing}")

    parts: list[SemanticPart] = []
    for part_id in PART_NAMES:
        mask = np.asarray(part_masks[part_id])
        if mask.ndim != 2:
            raise ValueError(f"part mask {part_id!r} must be two-dimensional")
        bbox = _bbox_normalized(mask)
        if bbox is None:
            continue

        structural_role, visual_role, policy = _roles(part_id)
        parts.append(
            SemanticPart(
                id=part_id,
                category=part_id,
                mask_ref=f"phase04:part_masks/{part_id}.png",
                bbox=bbox,
                confidence=0.0 if part_id == "unknown" else 1.0,
                structural_role=structural_role,
                visual_role=visual_role,
                abstraction_policy=policy,
                topology_constraints=_constraints(part_id, graph),
                geometry_constraints=GeometryConstraints(),
                evidence_refs=(
                    f"phase04:part_masks/{part_id}.png",
                    "phase05:structural_layout_graph.json",
                ),
            )
        )
    return AbstractionPlan(parts=tuple(parts))
