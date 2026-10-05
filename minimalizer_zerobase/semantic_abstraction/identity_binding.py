from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import cv2
import numpy as np

from .ir import AbstractionPlan, AbstractionPolicy, VisualRole
from .identity_structure_observer import IdentityStructureEvidence


@dataclass(frozen=True)
class RequiredIdentityBinding:
    binding_id: str
    parent_part_id: str
    semantic_role: str
    mask: np.ndarray
    min_primitives: int
    max_primitives: int
    confidence: float


_ROLE_GRAMMAR = {
    "hair": ("major_hair_front", 1, 3),
    "accessory_or_held_object": ("major_accessory", 1, 2),
    "major_clothing": ("major_clothing_identity", 1, 3),
}


def _components(mask: np.ndarray, *, min_ratio: float = .035) -> tuple[np.ndarray, ...]:
    binary = np.asarray(mask).astype(np.uint8)
    total = max(1, int(binary.sum()))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    rows = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area >= max(6, int(round(total * min_ratio))):
            rows.append((area, label))
    rows.sort(key=lambda item: (-item[0], item[1]))
    return tuple(labels == label for _, label in rows)


def bind_required_identity_features(
    plan: AbstractionPlan,
    masks: Mapping[str, np.ndarray],
) -> tuple[RequiredIdentityBinding, ...]:
    """Bind required semantic identity roles to source-authorized part masks.

    The binding layer does not infer identity from color and never uses Golden data.
    Only semantic parts already authorized by the plan can reserve primitives.
    """
    parts = {part.id: part for part in plan.parts}
    rows: list[RequiredIdentityBinding] = []
    for part_id in sorted(_ROLE_GRAMMAR):
        part = parts.get(part_id)
        if part is None or part.abstraction_policy is AbstractionPolicy.SUPPRESS:
            continue
        if part_id not in masks:
            continue
        authority = np.asarray(masks[part_id]).astype(bool)
        if not np.any(authority):
            continue
        role, default_min, default_max = _ROLE_GRAMMAR[part_id]
        minimum = max(default_min, part.geometry_constraints.min_primitives)
        maximum = part.geometry_constraints.max_primitives
        if maximum is None:
            maximum = default_max
        maximum = max(minimum, min(default_max, int(maximum)))
        if part.visual_role is VisualRole.IDENTITY_ACCENT:
            minimum = max(minimum, 1)
        components = _components(authority)
        if not components:
            components = (authority,)
        selected = components[:maximum]
        combined = np.zeros_like(authority)
        for component in selected:
            combined |= component
        rows.append(
            RequiredIdentityBinding(
                binding_id=f"required:{role}",
                parent_part_id=part_id,
                semantic_role=role,
                mask=combined,
                min_primitives=minimum,
                max_primitives=maximum,
                confidence=round(float(part.confidence), 6),
            )
        )
    return tuple(rows)


def required_identity_budget(bindings: tuple[RequiredIdentityBinding, ...]) -> int:
    return sum(binding.min_primitives for binding in bindings)


def bind_observed_identity_structures(
    plan: AbstractionPlan,
    parent_part_id: str,
    evidence: tuple[IdentityStructureEvidence, ...],
) -> tuple[RequiredIdentityBinding, ...]:
    """Promote observer proposals only when an authorized semantic parent permits it."""
    parts={part.id:part for part in plan.parts}
    parent=parts.get(parent_part_id)
    if parent is None or parent.abstraction_policy is AbstractionPolicy.SUPPRESS:
        return ()
    if parent.visual_role not in (VisualRole.SILHOUETTE, VisualRole.MAJOR_MASS, VisualRole.IDENTITY_ACCENT):
        return ()
    return tuple(
        RequiredIdentityBinding(
            binding_id=f"required:{parent_part_id}:observed:{index}",
            parent_part_id=parent_part_id,
            semantic_role="observed_identity_structure",
            mask=item.mask,
            min_primitives=1,
            max_primitives=1,
            confidence=item.confidence,
        )
        for index,item in enumerate(evidence)
        if item.confidence >= .55
    )
