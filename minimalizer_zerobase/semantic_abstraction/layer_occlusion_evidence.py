from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import Mapping

import cv2
import numpy as np


LAYER_OCCLUSION_VERSION = "sa7.47-v1"


class LayerRelation(str, Enum):
    OVERLAP = "OVERLAP"
    TOUCHING = "TOUCHING"
    DISJOINT = "DISJOINT"


@dataclass(frozen=True)
class LayerRelationEvidence:
    role_a: str
    role_b: str
    relation: LayerRelation
    overlap_pixels: int
    overlap_ratio_a: float
    overlap_ratio_b: float
    boundary_contact_pixels: int
    front_role: str | None
    back_role: str | None
    direction_source: str
    authoritative: bool = False

    def to_dict(self) -> dict:
        return {
            "role_a": self.role_a,
            "role_b": self.role_b,
            "relation": self.relation.value,
            "overlap_pixels": self.overlap_pixels,
            "overlap_ratio_a": round(float(self.overlap_ratio_a), 6),
            "overlap_ratio_b": round(float(self.overlap_ratio_b), 6),
            "boundary_contact_pixels": self.boundary_contact_pixels,
            "front_role": self.front_role,
            "back_role": self.back_role,
            "direction_source": self.direction_source,
            "authoritative": False,
        }


@dataclass(frozen=True)
class LayerOcclusionReport:
    roles: tuple[str, ...]
    relations: tuple[LayerRelationEvidence, ...]
    z_order_observed: bool
    authoritative: bool = False
    production_output_changed: bool = False
    version: str = LAYER_OCCLUSION_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "roles": list(self.roles),
            "z_order_observed": self.z_order_observed,
            "relations": [row.to_dict() for row in self.relations],
            "authoritative": False,
            "production_output_changed": False,
        }


def _contact_pixels(a: np.ndarray, b: np.ndarray) -> int:
    kernel = np.ones((3, 3), np.uint8)
    da = cv2.dilate(a.astype(np.uint8), kernel) > 0
    db = cv2.dilate(b.astype(np.uint8), kernel) > 0
    return int(((da & b) | (db & a)).sum())


def _direction(
    role_a: str,
    role_b: str,
    relation: LayerRelation,
    z_order: Mapping[str, int] | None,
) -> tuple[str | None, str | None, str]:
    if relation is LayerRelation.DISJOINT:
        return None, None, "not_applicable"
    if z_order is None:
        return None, None, "unavailable"
    if role_a not in z_order or role_b not in z_order:
        return None, None, "partial_canonical_z_order"
    za = int(z_order[role_a])
    zb = int(z_order[role_b])
    if za == zb:
        return None, None, "ambiguous_equal_canonical_z_order"
    if za > zb:
        return role_a, role_b, "canonical_z_order_observation"
    return role_b, role_a, "canonical_z_order_observation"


def observe_layer_occlusion(
    role_masks: Mapping[str, np.ndarray],
    *,
    role_z_order: Mapping[str, int] | None = None,
) -> LayerOcclusionReport:
    """Describe source mask relations without changing layer authority.

    Direction is never inferred from overlap alone. When supplied, canonical
    z-order is observed and recorded as provenance rather than modified.
    """
    normalized = {
        role: np.asarray(mask).astype(bool)
        for role, mask in sorted(role_masks.items())
    }
    if not normalized:
        raise ValueError("role_masks must not be empty")

    shapes = {mask.shape for mask in normalized.values()}
    if len(shapes) != 1:
        raise ValueError("role mask shape mismatch")

    if role_z_order is not None:
        unknown = set(role_z_order) - set(normalized)
        if unknown:
            raise ValueError(
                "z-order references unknown roles: "
                + ", ".join(sorted(unknown))
            )

    relations: list[LayerRelationEvidence] = []
    for role_a, role_b in combinations(sorted(normalized), 2):
        a = normalized[role_a]
        b = normalized[role_b]
        area_a = int(a.sum())
        area_b = int(b.sum())
        overlap = int((a & b).sum())
        contact = _contact_pixels(a, b)

        if overlap > 0:
            relation = LayerRelation.OVERLAP
        elif contact > 0:
            relation = LayerRelation.TOUCHING
        else:
            relation = LayerRelation.DISJOINT

        front, back, direction_source = _direction(
            role_a,
            role_b,
            relation,
            role_z_order,
        )
        relations.append(
            LayerRelationEvidence(
                role_a=role_a,
                role_b=role_b,
                relation=relation,
                overlap_pixels=overlap,
                overlap_ratio_a=overlap / max(1, area_a),
                overlap_ratio_b=overlap / max(1, area_b),
                boundary_contact_pixels=contact,
                front_role=front,
                back_role=back,
                direction_source=direction_source,
            )
        )

    return LayerOcclusionReport(
        roles=tuple(sorted(normalized)),
        relations=tuple(relations),
        z_order_observed=role_z_order is not None,
    )
