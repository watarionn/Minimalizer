from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
import cv2

from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.structure.graph import build_structural_layout_graph

STRUCTURAL_REPAIR_VERSION = "sa10.24-v1"
ANATOMY_PARTS = ("head", "torso", "left_arm", "right_arm", "lower_body")
_OUTER_BOUNDARY_MIN_RECALL = 0.90


def _topology(mask: np.ndarray) -> tuple[int, int, int]:
    binary = np.asarray(mask, dtype=np.uint8)
    components, _, _, _ = cv2.connectedComponentsWithStats(binary, 8)
    padded = cv2.copyMakeBorder(binary, 1, 1, 1, 1, cv2.BORDER_CONSTANT)
    background, _, _, _ = cv2.connectedComponentsWithStats(1 - padded, 8)
    components = max(0, int(components) - 1)
    holes = max(0, int(background) - 1)
    return components, holes, components - holes


def _outer_boundary(mask: np.ndarray) -> np.ndarray:
    return cv2.morphologyEx(
        np.asarray(mask, dtype=np.uint8), cv2.MORPH_GRADIENT,
        np.ones((3, 3), np.uint8),
    ).astype(bool)


def _bbox_area(mask: np.ndarray) -> float | None:
    ys, xs = np.where(np.asarray(mask).astype(bool))
    if xs.size == 0:
        return None
    return float((int(xs.max()) - int(xs.min()) + 1) * (int(ys.max()) - int(ys.min()) + 1))


def _normalize_source_masks(
    source_part_masks: Mapping[str, np.ndarray],
    shape: tuple[int, int],
) -> dict[str, np.ndarray]:
    masks: dict[str, np.ndarray] = {}
    for name in PART_NAMES:
        raw = source_part_masks.get(name)
        if raw is None:
            masks[name] = np.zeros(shape, dtype=bool)
            continue
        mask = np.asarray(raw).astype(bool)
        if mask.shape != shape:
            raise ValueError(f"structural source mask shape mismatch: {name}")
        masks[name] = mask
    return masks


def _group_part_masks(
    groups: Sequence[Mapping[str, Any]],
    shape: tuple[int, int],
) -> dict[str, np.ndarray]:
    masks = {name: np.zeros(shape, dtype=bool) for name in PART_NAMES}
    for group in groups:
        part = str(group.get("part") or "")
        if part not in masks:
            continue
        mask = np.asarray(group.get("mask")).astype(bool)
        if mask.shape != shape:
            raise ValueError(f"structural group mask shape mismatch: {part}")
        masks[part] |= mask
    return masks


def _required_relation_keys(graph) -> set[tuple[str, str, str]]:
    return {
        (row.source_part, row.relation_kind, row.target_part)
        for row in graph.relations
        if row.confidence >= 0.5
        and (row.source_part in ANATOMY_PARTS or row.target_part in ANATOMY_PARTS)
    }


def _median_source_color(
    source_rgba: np.ndarray,
    mask: np.ndarray,
) -> tuple[int, int, int]:
    rgb = np.asarray(source_rgba)[..., :3].astype(np.uint8)
    pixels = rgb[mask]
    if pixels.size == 0:
        return (0, 0, 0)
    median = np.median(pixels, axis=0)
    return tuple(int(round(float(value))) for value in median)


def _repair_order(
    groups: Sequence[Mapping[str, Any]],
    *,
    part: str,
) -> int:
    same = [int(group["first_order"]) for group in groups if group.get("part") == part]
    if same:
        return min(same)
    orders = [int(group["first_order"]) for group in groups]
    if not orders:
        return 0
    if part == "head":
        return min(orders) - 1
    return max(orders) + 1


def apply_structural_source_repair(
    groups: list[dict[str, Any]],
    *,
    source_rgba: np.ndarray,
    source_part_masks: Mapping[str, np.ndarray],
    shape: tuple[int, int],
    minimum_bbox_area_ratio: float = 0.35,
    maximum_bbox_area_ratio: float = 2.8,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not 0 < minimum_bbox_area_ratio <= 1:
        raise ValueError("minimum_bbox_area_ratio must be within (0, 1]")
    if maximum_bbox_area_ratio < 1:
        raise ValueError("maximum_bbox_area_ratio must be >= 1")
    image = np.asarray(source_rgba)
    if image.ndim != 3 or image.shape[:2] != shape or image.shape[2] not in {3, 4}:
        raise ValueError("structural source repair requires matching RGB/RGBA source")

    source_masks = _normalize_source_masks(source_part_masks, shape)
    current_masks = _group_part_masks(groups, shape)
    source_graph = build_structural_layout_graph(source_masks)
    current_graph = build_structural_layout_graph(current_masks)

    source_required = _required_relation_keys(source_graph)
    current_relations = {
        (row.source_part, row.relation_kind, row.target_part)
        for row in current_graph.relations
        if row.confidence >= 0.5
    }
    missing_relations = tuple(sorted(source_required - current_relations))

    # SA10.24: a high aggregate silhouette score can hide boundary erosion or
    # component/hole mutations inside a semantic owner.  Mark only the
    # source-owned parts implicated by the hard evidence for deterministic
    # source replay; do not relax the evaluator thresholds.
    source_union = np.logical_or.reduce(list(source_masks.values()))
    current_union = np.logical_or.reduce(list(current_masks.values()))
    source_edge = _outer_boundary(source_union)
    current_edge = _outer_boundary(current_union)
    boundary_recall = float(np.count_nonzero(source_edge & current_edge)) / max(
        int(source_edge.sum()), 1
    )
    topology_repair_parts: set[str] = set()
    for part in PART_NAMES:
        if part == "unknown" or not np.any(source_masks[part]):
            continue
        if _topology(source_masks[part]) != _topology(current_masks[part]):
            topology_repair_parts.add(part)
    if boundary_recall < _OUTER_BOUNDARY_MIN_RECALL:
        missing_edge = source_edge & ~current_union
        for part in PART_NAMES:
            if part != "unknown" and np.any(source_masks[part] & missing_edge):
                topology_repair_parts.add(part)

    reasons: dict[str, list[str]] = {}
    for part in ANATOMY_PARTS:
        source = source_masks[part]
        if not np.any(source):
            continue
        current = current_masks[part]
        if not np.any(current):
            reasons.setdefault(part, []).append("missing_structural_part")
            continue
        source_area = _bbox_area(source)
        current_area = _bbox_area(current)
        if source_area is None or current_area is None or source_area <= 0:
            continue
        ratio = current_area / source_area
        if ratio < minimum_bbox_area_ratio or ratio > maximum_bbox_area_ratio:
            reasons.setdefault(part, []).append(
                f"bbox_area_ratio={ratio:.6f}"
            )

    for source_part, relation, target_part in missing_relations:
        source_present = bool(np.any(current_masks.get(source_part, False)))
        target_present = bool(np.any(current_masks.get(target_part, False)))
        repair_parts: list[str] = []
        if (
            source_part in ANATOMY_PARTS
            and np.any(source_masks[source_part])
            and not source_present
        ):
            repair_parts.append(source_part)
        if (
            target_part in ANATOMY_PARTS
            and np.any(source_masks[target_part])
            and not target_present
        ):
            repair_parts.append(target_part)
        if source_present and target_present:
            if source_part in ANATOMY_PARTS and np.any(source_masks[source_part]):
                repair_parts.append(source_part)
            if target_part in ANATOMY_PARTS and np.any(source_masks[target_part]):
                repair_parts.append(target_part)
        for repair_part in sorted(set(repair_parts)):
            reasons.setdefault(repair_part, []).append(
                f"missing_required_topology:{source_part}:{relation}:{target_part}"
            )

    for part in sorted(topology_repair_parts):
        if _topology(source_masks[part]) != _topology(current_masks[part]):
            reasons.setdefault(part, []).append("source_topology_mismatch")
        elif boundary_recall < _OUTER_BOUNDARY_MIN_RECALL:
            reasons.setdefault(part, []).append(
                f"source_outer_boundary_recall={boundary_recall:.6f}"
            )

    repaired_parts = tuple(sorted(reasons))
    if not repaired_parts:
        return [dict(group) for group in groups], {
            "version": STRUCTURAL_REPAIR_VERSION,
            "applied": False,
            "repaired_parts": [],
            "reasons": {},
            "missing_required_relations_before": [
                ":".join(row) for row in missing_relations
            ],
            "source_graph_pass": bool(source_graph.to_dict()["validation"]["pass"]),
            "baseline_graph_pass": bool(current_graph.to_dict()["validation"]["pass"]),
            "source_outer_boundary_recall_before": boundary_recall,
            "minimum_outer_boundary_recall": _OUTER_BOUNDARY_MIN_RECALL,
        }

    output = [dict(group) for group in groups if group.get("part") not in repaired_parts]
    for part in repaired_parts:
        source_mask = source_masks[part].copy()
        existing = [group for group in groups if group.get("part") == part]
        if existing:
            dominant = max(
                existing,
                key=lambda group: int(np.count_nonzero(np.asarray(group["mask"]))),
            )
            color = tuple(int(value) for value in dominant["color"])
            source_ids = list(dict.fromkeys(
                str(value)
                for group in existing
                for value in group.get("source_ids", ())
            ))
            source_actions = {
                str(value)
                for group in existing
                for value in group.get("source_actions", ())
            }
        else:
            color = _median_source_color(image, source_mask)
            source_ids = []
            source_actions = set()
        output.append(
            {
                "part": part,
                "color": color,
                "mask": source_mask,
                "source_ids": source_ids,
                "source_actions": source_actions,
                "first_order": _repair_order(groups, part=part),
                "source_guided_kind": f"structural-source-repair-{part}",
                "source_evidence_refs": (f"phase04:part_masks/{part}.png",),
            }
        )

    output.sort(key=lambda item: (int(item["first_order"]), str(item["part"])))
    repaired_masks = _group_part_masks(output, shape)
    repaired_graph = build_structural_layout_graph(repaired_masks)
    repaired_relations = {
        (row.source_part, row.relation_kind, row.target_part)
        for row in repaired_graph.relations
        if row.confidence >= 0.5
    }
    missing_after = tuple(sorted(source_required - repaired_relations))
    return output, {
        "version": STRUCTURAL_REPAIR_VERSION,
        "applied": True,
        "repaired_parts": list(repaired_parts),
        "reasons": {
            part: sorted(set(values)) for part, values in sorted(reasons.items())
        },
        "missing_required_relations_before": [
            ":".join(row) for row in missing_relations
        ],
        "missing_required_relations_after": [
            ":".join(row) for row in missing_after
        ],
        "source_graph_pass": bool(source_graph.to_dict()["validation"]["pass"]),
        "baseline_graph_pass": bool(current_graph.to_dict()["validation"]["pass"]),
        "repaired_graph_pass": bool(repaired_graph.to_dict()["validation"]["pass"]),
        "source_outer_boundary_recall_before": boundary_recall,
        "minimum_outer_boundary_recall": _OUTER_BOUNDARY_MIN_RECALL,
    }
