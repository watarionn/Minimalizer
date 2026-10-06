from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from minimalizer_zerobase.analyzers.structured_mask_evidence import (
    MaskRelationKind as LayerRelation,
    observe_mask_relations,
)


LAYER_OCCLUSION_VERSION = "sa7.47-v1"


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


def observe_layer_occlusion(
    role_masks: Mapping[str, np.ndarray],
    *,
    role_z_order: Mapping[str, int] | None = None,
) -> LayerOcclusionReport:
    """Describe source mask relations without changing layer authority.

    SA7.47 now consumes the generic PB2/SA2 mask-relation observer so the
    evidence primitive lives at the lower analyzer boundary rather than being
    rediscovered inside semantic abstraction.
    """
    normalized_roles = tuple(sorted(role_masks))
    observations = observe_mask_relations(
        role_masks,
        role_z_order=role_z_order,
    )
    relations = tuple(
        LayerRelationEvidence(
            role_a=row.role_a,
            role_b=row.role_b,
            relation=row.relation,
            overlap_pixels=row.overlap_pixels,
            overlap_ratio_a=row.overlap_ratio_a,
            overlap_ratio_b=row.overlap_ratio_b,
            boundary_contact_pixels=row.boundary_contact_pixels,
            front_role=row.front_role,
            back_role=row.back_role,
            direction_source=row.direction_source,
        )
        for row in observations
    )
    return LayerOcclusionReport(
        roles=normalized_roles,
        relations=relations,
        z_order_observed=role_z_order is not None,
    )
