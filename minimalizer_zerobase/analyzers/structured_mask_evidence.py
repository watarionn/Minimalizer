from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import Mapping

import cv2
import numpy as np

from minimalizer_zerobase.analyzers.contracts import Evidence, Provenance
from minimalizer_zerobase.core.coordinates import CoordinateSpace


PB2_EVIDENCE_VERSION = "pb2-v1"


class EvidenceAuthorityState(str, Enum):
    OBSERVED = "observed"
    ADVISOR = "advisor"
    PROMOTED = "promoted"


@dataclass(frozen=True)
class EvidenceAuthorityTrace:
    state: EvidenceAuthorityState
    source_ref: str
    advisor_source: str | None = None
    promoted_by: str | None = None

    def __post_init__(self) -> None:
        if not self.source_ref:
            raise ValueError("source_ref is required")
        if self.state is EvidenceAuthorityState.OBSERVED:
            if self.advisor_source is not None or self.promoted_by is not None:
                raise ValueError("observed evidence cannot carry advisor/promotion provenance")
        elif self.state is EvidenceAuthorityState.ADVISOR:
            if not self.advisor_source or self.promoted_by is not None:
                raise ValueError("advisor evidence requires advisor_source and cannot be promoted")
        elif self.state is EvidenceAuthorityState.PROMOTED:
            if not self.promoted_by:
                raise ValueError("promoted evidence requires explicit promoted_by provenance")

    @property
    def production_authority(self) -> bool:
        return self.state is EvidenceAuthorityState.PROMOTED

    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "source_ref": self.source_ref,
            "advisor_source": self.advisor_source,
            "promoted_by": self.promoted_by,
            "production_authority": self.production_authority,
        }


@dataclass(frozen=True)
class MaskComponentObservation:
    role: str
    component_index: int
    pixel_count: int
    role_pixel_count: int
    bbox: tuple[int, int, int, int]
    centroid: tuple[float, float]

    @property
    def support_ratio(self) -> float:
        return self.pixel_count / max(1, self.role_pixel_count)


class MaskRelationKind(str, Enum):
    OVERLAP = "OVERLAP"
    TOUCHING = "TOUCHING"
    DISJOINT = "DISJOINT"


@dataclass(frozen=True)
class MaskRelationObservation:
    role_a: str
    role_b: str
    relation: MaskRelationKind
    overlap_pixels: int
    overlap_ratio_a: float
    overlap_ratio_b: float
    boundary_contact_pixels: int
    front_role: str | None
    back_role: str | None
    direction_source: str


@dataclass(frozen=True)
class PB2EvidenceExpansion:
    evidence: tuple[Evidence, ...]
    role_count: int
    component_count: int
    relation_count: int
    z_order_observed: bool
    production_output_changed: bool = False
    version: str = PB2_EVIDENCE_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "role_count": self.role_count,
            "component_count": self.component_count,
            "relation_count": self.relation_count,
            "z_order_observed": self.z_order_observed,
            "production_output_changed": False,
            "evidence": [item.to_dict() for item in self.evidence],
        }


def _normalized_masks(
    role_masks: Mapping[str, np.ndarray],
) -> dict[str, np.ndarray]:
    normalized = {
        role: np.asarray(mask).astype(bool)
        for role, mask in sorted(role_masks.items())
    }
    if not normalized:
        raise ValueError("role_masks must not be empty")
    shapes = {mask.shape for mask in normalized.values()}
    if len(shapes) != 1:
        raise ValueError("role mask shape mismatch")
    if any(mask.ndim != 2 for mask in normalized.values()):
        raise ValueError("role masks must be two-dimensional")
    return normalized


def observe_mask_components(
    role_masks: Mapping[str, np.ndarray],
) -> tuple[MaskComponentObservation, ...]:
    normalized = _normalized_masks(role_masks)
    rows: list[MaskComponentObservation] = []

    for role, mask in normalized.items():
        role_area = int(mask.sum())
        if role_area <= 0:
            continue

        count, labels, stats, centroids = cv2.connectedComponentsWithStats(
            mask.astype(np.uint8),
            8,
        )
        components: list[tuple[int, int, int, int, int, float, float, int]] = []
        for label in range(1, count):
            area = int(stats[label, cv2.CC_STAT_AREA])
            if area <= 0:
                continue
            x = int(stats[label, cv2.CC_STAT_LEFT])
            y = int(stats[label, cv2.CC_STAT_TOP])
            w = int(stats[label, cv2.CC_STAT_WIDTH])
            h = int(stats[label, cv2.CC_STAT_HEIGHT])
            cx, cy = (float(v) for v in centroids[label])
            components.append((area, y, x, w, h, cx, cy, label))

        components.sort(key=lambda item: (-item[0], item[1], item[2], item[3], item[4]))
        for index, (area, y, x, w, h, cx, cy, _) in enumerate(components):
            rows.append(
                MaskComponentObservation(
                    role=role,
                    component_index=index,
                    pixel_count=area,
                    role_pixel_count=role_area,
                    bbox=(x, y, w, h),
                    centroid=(cx, cy),
                )
            )

    return tuple(rows)


def _contact_pixels(a: np.ndarray, b: np.ndarray) -> int:
    kernel = np.ones((3, 3), np.uint8)
    da = cv2.dilate(a.astype(np.uint8), kernel) > 0
    db = cv2.dilate(b.astype(np.uint8), kernel) > 0
    return int(((da & b) | (db & a)).sum())


def _direction(
    role_a: str,
    role_b: str,
    relation: MaskRelationKind,
    role_z_order: Mapping[str, int] | None,
) -> tuple[str | None, str | None, str]:
    if relation is MaskRelationKind.DISJOINT:
        return None, None, "not_applicable"
    if role_z_order is None:
        return None, None, "unavailable"
    if role_a not in role_z_order or role_b not in role_z_order:
        return None, None, "partial_canonical_z_order"

    za = int(role_z_order[role_a])
    zb = int(role_z_order[role_b])
    if za == zb:
        return None, None, "ambiguous_equal_canonical_z_order"
    if za > zb:
        return role_a, role_b, "canonical_z_order_observation"
    return role_b, role_a, "canonical_z_order_observation"


def observe_mask_relations(
    role_masks: Mapping[str, np.ndarray],
    *,
    role_z_order: Mapping[str, int] | None = None,
) -> tuple[MaskRelationObservation, ...]:
    normalized = _normalized_masks(role_masks)
    if role_z_order is not None:
        unknown = set(role_z_order) - set(normalized)
        if unknown:
            raise ValueError(
                "z-order references unknown roles: "
                + ", ".join(sorted(unknown))
            )

    rows: list[MaskRelationObservation] = []
    for role_a, role_b in combinations(sorted(normalized), 2):
        a = normalized[role_a]
        b = normalized[role_b]
        area_a = int(a.sum())
        area_b = int(b.sum())
        overlap = int((a & b).sum())
        contact = _contact_pixels(a, b)

        if overlap > 0:
            relation = MaskRelationKind.OVERLAP
        elif contact > 0:
            relation = MaskRelationKind.TOUCHING
        else:
            relation = MaskRelationKind.DISJOINT

        front, back, direction_source = _direction(
            role_a,
            role_b,
            relation,
            role_z_order,
        )
        rows.append(
            MaskRelationObservation(
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

    return tuple(rows)


def _source_ref(role: str, source_refs: Mapping[str, str] | None) -> str:
    if source_refs is not None and role in source_refs:
        value = str(source_refs[role])
        if not value:
            raise ValueError(f"empty source_ref for role: {role}")
        return value
    return f"source-mask:{role}"


def build_pb2_structured_evidence(
    *,
    role_masks: Mapping[str, np.ndarray],
    coordinate_space: CoordinateSpace,
    role_z_order: Mapping[str, int] | None = None,
    source_refs: Mapping[str, str] | None = None,
) -> PB2EvidenceExpansion:
    normalized = _normalized_masks(role_masks)
    shape = next(iter(normalized.values())).shape
    if coordinate_space.width != shape[1] or coordinate_space.height != shape[0]:
        raise ValueError("coordinate space must match role mask dimensions")

    provenance = Provenance(
        "PB2StructuredMaskEvidenceAdapter",
        PB2_EVIDENCE_VERSION,
    )
    records: list[Evidence] = []

    components = observe_mask_components(normalized)
    for component in components:
        source_ref = _source_ref(component.role, source_refs)
        authority = EvidenceAuthorityTrace(
            EvidenceAuthorityState.OBSERVED,
            source_ref,
        )
        records.append(
            Evidence(
                evidence_id=(
                    f"pb2:{component.role}:component:"
                    f"{component.component_index:03d}"
                ),
                evidence_type="region_component",
                coordinate_space=coordinate_space,
                provenance=provenance,
                semantic_label=component.role,
                geometry={
                    # Intentionally not named "bbox": PB2 observer evidence
                    # must fail closed if accidentally sent to EvidenceFusion.
                    "component_bbox": list(component.bbox),
                    "centroid": [
                        float(component.centroid[0]),
                        float(component.centroid[1]),
                    ],
                    "pixel_count": component.pixel_count,
                    "role_pixel_count": component.role_pixel_count,
                    "support_ratio": round(component.support_ratio, 12),
                    "component_index": component.component_index,
                },
                normalization={
                    "pb2_version": PB2_EVIDENCE_VERSION,
                    "ordering": "role_then_area_desc_y_x",
                    "evidence_scope": "observer_only",
                    "authority": authority.to_dict(),
                },
            )
        )

    relations = observe_mask_relations(
        normalized,
        role_z_order=role_z_order,
    )
    for relation in relations:
        ref_a = _source_ref(relation.role_a, source_refs)
        ref_b = _source_ref(relation.role_b, source_refs)
        authority = EvidenceAuthorityTrace(
            EvidenceAuthorityState.OBSERVED,
            f"{ref_a}|{ref_b}",
        )
        records.append(
            Evidence(
                evidence_id=f"pb2:relation:{relation.role_a}:{relation.role_b}",
                evidence_type="layer_relation",
                coordinate_space=coordinate_space,
                provenance=provenance,
                geometry={
                    "roles": [relation.role_a, relation.role_b],
                    "relation": relation.relation.value,
                    "overlap_pixels": relation.overlap_pixels,
                    "overlap_ratio_a": round(
                        float(relation.overlap_ratio_a),
                        12,
                    ),
                    "overlap_ratio_b": round(
                        float(relation.overlap_ratio_b),
                        12,
                    ),
                    "boundary_contact_pixels": relation.boundary_contact_pixels,
                    "front_role": relation.front_role,
                    "back_role": relation.back_role,
                },
                normalization={
                    "pb2_version": PB2_EVIDENCE_VERSION,
                    "ordering": "role_pair_ascending",
                    "evidence_scope": "observer_only",
                    "direction_source": relation.direction_source,
                    "source_refs": [ref_a, ref_b],
                    "authority": authority.to_dict(),
                },
            )
        )

    ordered = tuple(sorted(records, key=lambda item: item.evidence_id))
    return PB2EvidenceExpansion(
        evidence=ordered,
        role_count=len(normalized),
        component_count=len(components),
        relation_count=len(relations),
        z_order_observed=role_z_order is not None,
    )
