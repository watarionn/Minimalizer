from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

import numpy as np

from minimalizer_zerobase.analyzers.structured_mask_evidence import (
    MaskRelationKind,
    observe_mask_relations,
)

from .ir import AbstractionPlan, TopologyConstraint


PB6_DIAGNOSTIC_VERSION = "pb6-v1"
_ANATOMY_ROLES = {"head", "torso", "left_arm", "right_arm", "lower_body"}
_CONTEXT_ROLES = {"hair", "major_clothing", "accessory_or_held_object", "face"}


class AnatomyRelationCompatibility(str, Enum):
    SUPPORTING = "SUPPORTING"
    NEUTRAL = "NEUTRAL"
    POTENTIAL_CONFLICT = "POTENTIAL_CONFLICT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class AnatomyOcclusionRelationDiagnostic:
    role_a: str
    role_b: str
    source_relation: MaskRelationKind
    overlap_pixels: int
    boundary_contact_pixels: int
    front_role: str | None
    back_role: str | None
    direction_source: str
    matching_topology_constraints: tuple[str, ...]
    compatibility: AnatomyRelationCompatibility
    authority_state: str = "observer"
    production_authority: bool = False
    production_action: None = None

    def to_dict(self) -> dict:
        return {
            "role_a": self.role_a,
            "role_b": self.role_b,
            "source_relation": self.source_relation.value,
            "overlap_pixels": self.overlap_pixels,
            "boundary_contact_pixels": self.boundary_contact_pixels,
            "front_role": self.front_role,
            "back_role": self.back_role,
            "direction_source": self.direction_source,
            "matching_topology_constraints": list(self.matching_topology_constraints),
            "compatibility": self.compatibility.value,
            "authority_state": self.authority_state,
            "production_authority": False,
            "production_action": None,
        }


@dataclass(frozen=True)
class AnatomyOcclusionDiagnostic:
    relations: tuple[AnatomyOcclusionRelationDiagnostic, ...]
    production_authority_count: int = 0
    production_output_changed: bool = False
    version: str = PB6_DIAGNOSTIC_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "relations": [row.to_dict() for row in self.relations],
            "production_authority_count": 0,
            "production_output_changed": False,
        }


def _required_constraints(plan: AbstractionPlan) -> dict[frozenset[str], tuple[str, ...]]:
    rows: dict[frozenset[str], list[str]] = {}
    known = {part.id for part in plan.parts}
    for part in sorted(plan.parts, key=lambda item: item.id):
        for constraint in sorted(
            part.topology_constraints,
            key=lambda item: (item.relation, item.target_part_id, not item.required),
        ):
            if not constraint.required or constraint.target_part_id not in known:
                continue
            pair = frozenset((part.id, constraint.target_part_id))
            rows.setdefault(pair, []).append(
                f"{part.id}:{constraint.relation}:{constraint.target_part_id}"
            )
    return {key: tuple(sorted(values)) for key, values in rows.items()}


def _compatibility(
    *,
    role_a: str,
    role_b: str,
    relation: MaskRelationKind,
    constraints: tuple[str, ...],
) -> AnatomyRelationCompatibility:
    anatomy_pair = role_a in _ANATOMY_ROLES and role_b in _ANATOMY_ROLES
    if constraints:
        if relation in {MaskRelationKind.TOUCHING, MaskRelationKind.OVERLAP}:
            return AnatomyRelationCompatibility.SUPPORTING
        return AnatomyRelationCompatibility.POTENTIAL_CONFLICT
    if relation is MaskRelationKind.OVERLAP:
        return AnatomyRelationCompatibility.INSUFFICIENT_EVIDENCE
    if anatomy_pair:
        return AnatomyRelationCompatibility.NEUTRAL
    if role_a in _CONTEXT_ROLES or role_b in _CONTEXT_ROLES:
        return AnatomyRelationCompatibility.NEUTRAL
    return AnatomyRelationCompatibility.NEUTRAL


def build_anatomy_occlusion_diagnostic(
    *,
    plan: AbstractionPlan,
    role_masks: Mapping[str, np.ndarray],
    role_z_order: Mapping[str, int] | None = None,
) -> AnatomyOcclusionDiagnostic:
    """Compare PB2 source-mask observations with canonical topology.

    This function is deliberately observer-only. It never mutates the plan,
    creates anatomy, rewrites topology, changes z-order, or produces a
    production action.
    """
    constraints = _required_constraints(plan)
    observed = observe_mask_relations(role_masks, role_z_order=role_z_order)
    rows = []
    for relation in observed:
        pair_constraints = constraints.get(
            frozenset((relation.role_a, relation.role_b)),
            (),
        )
        rows.append(
            AnatomyOcclusionRelationDiagnostic(
                role_a=relation.role_a,
                role_b=relation.role_b,
                source_relation=relation.relation,
                overlap_pixels=relation.overlap_pixels,
                boundary_contact_pixels=relation.boundary_contact_pixels,
                front_role=relation.front_role,
                back_role=relation.back_role,
                direction_source=relation.direction_source,
                matching_topology_constraints=pair_constraints,
                compatibility=_compatibility(
                    role_a=relation.role_a,
                    role_b=relation.role_b,
                    relation=relation.relation,
                    constraints=pair_constraints,
                ),
            )
        )
    return AnatomyOcclusionDiagnostic(relations=tuple(rows))
