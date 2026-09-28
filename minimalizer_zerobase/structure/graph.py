from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import cv2
import numpy as np

from minimalizer_zerobase.parts.decomposition import PART_NAMES

MAJOR_PARTS = (
    "head",
    "hair",
    "face",
    "torso",
    "left_arm",
    "right_arm",
    "lower_body",
    "major_clothing",
    "accessory_or_held_object",
)

OCCLUSION_KINDS = {"in_front_of", "behind"}


def _rounded(value: float) -> float:
    return round(float(value), 6)


@dataclass(frozen=True)
class PartAnchor:
    anchor_id: str
    part_id: str
    kind: str
    xy_pixel: tuple[float, float]
    xy_normalized: tuple[float, float]
    confidence: float
    evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "anchor_id": self.anchor_id,
            "part_id": self.part_id,
            "kind": self.kind,
            "xy_pixel": [_rounded(value) for value in self.xy_pixel],
            "xy_normalized": [_rounded(value) for value in self.xy_normalized],
            "confidence": _rounded(self.confidence),
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class PartRelation:
    relation_id: str
    source_part: str
    target_part: str
    relation_kind: str
    source_anchor_id: str
    target_anchor_id: str
    confidence: float
    evidence_refs: tuple[str, ...]
    measurements: dict[str, float | str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        measurements = {
            key: _rounded(value) if isinstance(value, float) else value
            for key, value in sorted(self.measurements.items())
        }
        return {
            "relation_id": self.relation_id,
            "source_part": self.source_part,
            "target_part": self.target_part,
            "relation_kind": self.relation_kind,
            "source_anchor_id": self.source_anchor_id,
            "target_anchor_id": self.target_anchor_id,
            "confidence": _rounded(self.confidence),
            "evidence_refs": list(self.evidence_refs),
            "measurements": measurements,
        }


@dataclass(frozen=True)
class StructuralLayoutGraph:
    width: int
    height: int
    present_parts: tuple[str, ...]
    anchors: tuple[PartAnchor, ...]
    relations: tuple[PartRelation, ...]

    def to_dict(self) -> dict:
        return {
            "schema_version": "1.0",
            "coordinate_space": {
                "pixel_width": self.width,
                "pixel_height": self.height,
                "normalized_origin": "top-left",
                "normalized_range": [0.0, 1.0],
            },
            "present_parts": list(self.present_parts),
            "anchors": [anchor.to_dict() for anchor in self.anchors],
            "relations": [relation.to_dict() for relation in self.relations],
            "validation": graph_validation(self),
        }


def _mask_ref(part_id: str) -> str:
    return f"phase04:part_masks/{part_id}.png"


def _normalize_masks(
    part_masks: Mapping[str, np.ndarray],
) -> tuple[dict[str, np.ndarray], tuple[int, int]]:
    missing = [name for name in PART_NAMES if name not in part_masks]
    if missing:
        raise ValueError(f"missing Phase 4 part masks: {missing}")
    shape: tuple[int, int] | None = None
    normalized: dict[str, np.ndarray] = {}
    for name in PART_NAMES:
        mask = np.asarray(part_masks[name])
        if mask.ndim != 2:
            raise ValueError(f"part mask {name!r} must be two-dimensional")
        if shape is None:
            shape = mask.shape
        if mask.shape != shape:
            raise ValueError("all Phase 4 part masks must share one shape")
        normalized[name] = mask.astype(bool, copy=True)
    assert shape is not None
    return normalized, shape


def _centroid(mask: np.ndarray) -> tuple[float, float]:
    ys, xs = np.where(mask)
    if xs.size == 0:
        raise ValueError("cannot compute an anchor for an empty mask")
    return float(np.mean(xs)), float(np.mean(ys))


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if xs.size == 0:
        raise ValueError("cannot compute a bbox for an empty mask")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _closest_points(
    source: np.ndarray,
    target: np.ndarray,
) -> tuple[tuple[float, float], tuple[float, float], float]:
    if not np.any(source) or not np.any(target):
        raise ValueError("closest points require two non-empty masks")
    distance = cv2.distanceTransform(
        (~target).astype(np.uint8),
        cv2.DIST_L2,
        5,
    )
    source_yx = np.argwhere(source)
    source_distances = distance[source]
    source_index = int(np.argmin(source_distances))
    sy, sx = [int(value) for value in source_yx[source_index]]
    radius = max(2, int(np.ceil(float(source_distances[source_index]))) + 2)
    y0, y1 = max(0, sy - radius), min(target.shape[0], sy + radius + 1)
    x0, x1 = max(0, sx - radius), min(target.shape[1], sx + radius + 1)
    target_yx = np.argwhere(target[y0:y1, x0:x1])
    if target_yx.size == 0:
        target_yx = np.argwhere(target)
        offset_y, offset_x = 0, 0
    else:
        offset_y, offset_x = y0, x0
    target_yx = target_yx + np.asarray([offset_y, offset_x])
    squared = (target_yx[:, 0] - sy) ** 2 + (target_yx[:, 1] - sx) ** 2
    target_index = int(np.argmin(squared))
    ty, tx = [int(value) for value in target_yx[target_index]]
    exact_distance = float(np.hypot(tx - sx, ty - sy))
    return (float(sx), float(sy)), (float(tx), float(ty)), exact_distance


def _overlap_ratio(source: np.ndarray, target: np.ndarray) -> float:
    denominator = max(int(np.count_nonzero(source)), 1)
    return float(np.count_nonzero(source & target)) / float(denominator)


def _face_surround_score(hair: np.ndarray, face: np.ndarray) -> float:
    if not np.any(hair) or not np.any(face):
        return 0.0
    x0, y0, x1, y1 = _bbox(face)
    width, height = max(x1 - x0, 1), max(y1 - y0, 1)
    pad_x = max(3, int(round(width * 0.24)))
    pad_y = max(3, int(round(height * 0.24)))
    regions = (
        hair[max(0, y0 - pad_y) : min(hair.shape[0], y0 + pad_y), max(0, x0 - pad_x) : min(hair.shape[1], x1 + pad_x)],
        hair[max(0, y0 - pad_y) : min(hair.shape[0], y1 + pad_y), max(0, x0 - pad_x) : min(hair.shape[1], x0 + pad_x)],
        hair[max(0, y0 - pad_y) : min(hair.shape[0], y1 + pad_y), max(0, x1 - pad_x) : min(hair.shape[1], x1 + pad_x)],
    )
    occupied = sum(bool(np.any(region)) for region in regions)
    proximity = cv2.dilate(
        face.astype(np.uint8),
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
    ).astype(bool)
    contact_ratio = float(np.count_nonzero(hair & proximity)) / max(
        float(np.count_nonzero(proximity & ~face)),
        1.0,
    )
    return min(1.0, occupied / 3.0 * 0.72 + min(contact_ratio, 1.0) * 0.28)


def _occlusion_edges(relations: tuple[PartRelation, ...]) -> dict[str, set[str]]:
    edges: dict[str, set[str]] = {}
    for relation in relations:
        if relation.relation_kind == "in_front_of":
            front, behind = relation.source_part, relation.target_part
        elif relation.relation_kind == "behind":
            front, behind = relation.target_part, relation.source_part
        else:
            continue
        edges.setdefault(front, set()).add(behind)
        edges.setdefault(behind, set())
    return edges


def _has_directed_cycle(edges: Mapping[str, set[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for target in sorted(edges.get(node, ())):
            if visit(target):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in sorted(edges))


def graph_validation(graph: StructuralLayoutGraph) -> dict:
    connected: dict[str, set[str]] = {part: set() for part in graph.present_parts}
    for relation in graph.relations:
        connected.setdefault(relation.source_part, set()).add(relation.target_part)
        connected.setdefault(relation.target_part, set()).add(relation.source_part)
    isolated = [
        part
        for part in MAJOR_PARTS
        if part in connected and not connected[part]
    ]
    missing_arm_attachments = [
        arm
        for arm in ("left_arm", "right_arm")
        if arm in connected
        and not any(
            relation.source_part == arm
            and relation.target_part == "torso"
            and relation.relation_kind == "attached_to"
            for relation in graph.relations
        )
    ]
    missing_accessory_attachment = (
        "accessory_or_held_object" in connected
        and not any(
            relation.source_part == "accessory_or_held_object"
            and relation.relation_kind == "attached_to"
            for relation in graph.relations
        )
    )
    occlusion_cycle = _has_directed_cycle(_occlusion_edges(graph.relations))
    return {
        "isolated_major_parts": isolated,
        "missing_arm_attachments": missing_arm_attachments,
        "missing_accessory_attachment": missing_accessory_attachment,
        "occlusion_cycle_count": 1 if occlusion_cycle else 0,
        "pass": (
            not isolated
            and not missing_arm_attachments
            and not missing_accessory_attachment
            and not occlusion_cycle
        ),
    }


def build_structural_layout_graph(
    part_masks: Mapping[str, np.ndarray],
    *,
    accessory_kind: str = "none",
    accessory_confidence: float = 0.0,
) -> StructuralLayoutGraph:
    masks, shape = _normalize_masks(part_masks)
    height, width = shape
    present_parts = tuple(
        name
        for name in PART_NAMES
        if name != "unknown" and bool(np.any(masks[name]))
    )
    if not present_parts:
        raise ValueError("Phase 5 requires at least one non-unknown Phase 4 part")

    anchors: list[PartAnchor] = []
    relations: list[PartRelation] = []
    anchor_ids: set[str] = set()

    def add_anchor(
        part_id: str,
        kind: str,
        xy: tuple[float, float],
        confidence: float,
        evidence_refs: tuple[str, ...],
    ) -> str:
        anchor_id = f"anchor:{part_id}:{kind}"
        suffix = 2
        while anchor_id in anchor_ids:
            anchor_id = f"anchor:{part_id}:{kind}:{suffix}"
            suffix += 1
        anchor_ids.add(anchor_id)
        anchors.append(
            PartAnchor(
                anchor_id=anchor_id,
                part_id=part_id,
                kind=kind,
                xy_pixel=xy,
                xy_normalized=(
                    xy[0] / max(float(width - 1), 1.0),
                    xy[1] / max(float(height - 1), 1.0),
                ),
                confidence=max(0.0, min(1.0, confidence)),
                evidence_refs=evidence_refs,
            )
        )
        return anchor_id

    center_anchors = {
        part: add_anchor(
            part,
            "centroid",
            _centroid(masks[part]),
            1.0,
            (_mask_ref(part), "derived:mask-centroid"),
        )
        for part in present_parts
    }

    def add_relation(
        source: str,
        target: str,
        kind: str,
        confidence: float,
        evidence_refs: tuple[str, ...],
        *,
        source_anchor_id: str | None = None,
        target_anchor_id: str | None = None,
        measurements: dict[str, float | str] | None = None,
    ) -> None:
        if source not in present_parts or target not in present_parts:
            return
        relations.append(
            PartRelation(
                relation_id=f"relation:{source}:{kind}:{target}",
                source_part=source,
                target_part=target,
                relation_kind=kind,
                source_anchor_id=source_anchor_id or center_anchors[source],
                target_anchor_id=target_anchor_id or center_anchors[target],
                confidence=max(0.0, min(1.0, confidence)),
                evidence_refs=evidence_refs,
                measurements=measurements or {},
            )
        )

    def add_attachment(
        source: str,
        target: str,
        *,
        threshold_px: float,
        evidence_refs: tuple[str, ...] = (),
        confidence_scale: float = 1.0,
        allow_extended_gap: bool = False,
    ) -> float | None:
        if source not in present_parts or target not in present_parts:
            return None
        source_xy, target_xy, distance = _closest_points(masks[source], masks[target])
        limit = threshold_px * (2.0 if allow_extended_gap else 1.0)
        if distance > limit:
            return None
        source_anchor = add_anchor(
            source,
            f"attachment-to-{target}",
            source_xy,
            confidence_scale,
            (_mask_ref(source), _mask_ref(target), "derived:nearest-boundary-pair"),
        )
        target_anchor = add_anchor(
            target,
            f"attachment-from-{source}",
            target_xy,
            confidence_scale,
            (_mask_ref(source), _mask_ref(target), "derived:nearest-boundary-pair"),
        )
        distance_confidence = max(0.35, 1.0 - distance / max(limit * 1.5, 1.0))
        confidence = min(distance_confidence, confidence_scale)
        add_relation(
            source,
            target,
            "attached_to",
            confidence,
            (_mask_ref(source), _mask_ref(target), *evidence_refs),
            source_anchor_id=source_anchor,
            target_anchor_id=target_anchor,
            measurements={
                "boundary_distance_px": distance,
                "attachment_limit_px": limit,
            },
        )
        return distance

    base_attachment_threshold = max(6.0, min(width, height) * 0.06)

    if "head" in present_parts and "torso" in present_parts:
        head_center = _centroid(masks["head"])
        torso_center = _centroid(masks["torso"])
        vertical_gap = torso_center[1] - head_center[1]
        add_relation(
            "head",
            "torso",
            "above",
            min(1.0, max(0.0, vertical_gap / max(height * 0.22, 1.0))),
            (_mask_ref("head"), _mask_ref("torso"), "derived:mask-centroids"),
            measurements={"centroid_vertical_gap_px": vertical_gap},
        )

    if "face" in present_parts and "head" in present_parts:
        face_inside = _overlap_ratio(masks["face"], masks["head"])
        if face_inside >= 0.45:
            add_relation(
                "face",
                "head",
                "inside",
                face_inside,
                (_mask_ref("face"), _mask_ref("head"), "derived:mask-overlap"),
                measurements={"source_overlap_ratio": face_inside},
            )

    if "hair" in present_parts and "head" in present_parts:
        hair_head_overlap = _overlap_ratio(masks["hair"], masks["head"])
        if hair_head_overlap > 0.0:
            add_relation(
                "hair",
                "head",
                "overlaps",
                hair_head_overlap,
                (_mask_ref("hair"), _mask_ref("head"), "derived:mask-overlap"),
                measurements={"source_overlap_ratio": hair_head_overlap},
            )

    if "hair" in present_parts and "face" in present_parts:
        surround_score = _face_surround_score(masks["hair"], masks["face"])
        if surround_score >= 0.45:
            add_relation(
                "hair",
                "face",
                "surrounds",
                surround_score,
                (_mask_ref("hair"), _mask_ref("face"), "derived:face-neighborhood"),
                measurements={"surround_score": surround_score},
            )
            add_relation(
                "hair",
                "face",
                "behind",
                min(0.82, surround_score * 0.82),
                (
                    _mask_ref("hair"),
                    _mask_ref("face"),
                    "phase04:display-priority/face-over-hair",
                ),
                measurements={"surround_score": surround_score},
            )

    add_attachment(
        "neck",
        "face",
        threshold_px=base_attachment_threshold,
    )
    add_attachment(
        "neck",
        "torso",
        threshold_px=base_attachment_threshold,
    )
    for arm in ("left_arm", "right_arm"):
        add_attachment(
            arm,
            "torso",
            threshold_px=base_attachment_threshold,
        )
        if arm in present_parts and "torso" in present_parts:
            arm_x = _centroid(masks[arm])[0]
            torso_x = _centroid(masks["torso"])[0]
            kind = "left_of" if arm_x < torso_x else "right_of"
            add_relation(
                arm,
                "torso",
                kind,
                min(1.0, abs(arm_x - torso_x) / max(width * 0.20, 1.0)),
                (_mask_ref(arm), _mask_ref("torso"), "derived:mask-centroids"),
                measurements={"centroid_horizontal_gap_px": abs(arm_x - torso_x)},
            )
    add_attachment(
        "lower_body",
        "torso",
        threshold_px=base_attachment_threshold,
    )
    clothing_distance = add_attachment(
        "major_clothing",
        "torso",
        threshold_px=base_attachment_threshold,
    )
    if clothing_distance is not None and clothing_distance <= base_attachment_threshold:
        add_relation(
            "major_clothing",
            "torso",
            "in_front_of",
            0.86,
            (
                _mask_ref("major_clothing"),
                _mask_ref("torso"),
                "phase04:display-priority/major-clothing-over-torso",
            ),
            measurements={"boundary_distance_px": clothing_distance},
        )

    accessory = "accessory_or_held_object"
    if accessory in present_parts:
        if accessory_kind == "vivid-accent" and "torso" in present_parts:
            target = "torso"
            extended = False
        else:
            if accessory_kind == "held-linear":
                candidates = [
                    part
                    for part in ("left_arm", "right_arm")
                    if part in present_parts
                ]
            else:
                candidates = []
            if not candidates:
                candidates = [
                    part
                    for part in ("left_arm", "right_arm", "torso", "head")
                    if part in present_parts
                ]
            if not candidates:
                target = "hair" if "hair" in present_parts else present_parts[0]
            else:
                target = min(
                    candidates,
                    key=lambda part: _closest_points(masks[accessory], masks[part])[2],
                )
            extended = accessory_kind == "held-linear"
        accessory_distance = add_attachment(
            accessory,
            target,
            threshold_px=max(base_attachment_threshold, min(width, height) * 0.10),
            evidence_refs=(
                "phase04:metrics/accessory_kind",
                "phase04:metrics/accessory_score",
            ),
            confidence_scale=max(0.45, min(1.0, accessory_confidence)),
            allow_extended_gap=extended,
        )
        if accessory_distance is not None:
            add_relation(
                accessory,
                target,
                "in_front_of",
                max(0.45, min(0.90, accessory_confidence)),
                (
                    _mask_ref(accessory),
                    _mask_ref(target),
                    "phase04:display-priority/accessory-over-parts",
                ),
                measurements={
                    "boundary_distance_px": accessory_distance,
                    "accessory_kind": accessory_kind,
                },
            )

    relations.sort(key=lambda item: item.relation_id)
    anchors.sort(key=lambda item: item.anchor_id)
    graph = StructuralLayoutGraph(
        width=width,
        height=height,
        present_parts=present_parts,
        anchors=tuple(anchors),
        relations=tuple(relations),
    )
    return graph
