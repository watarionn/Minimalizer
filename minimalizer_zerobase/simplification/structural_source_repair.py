from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
import cv2
from minimalizer_zerobase.evaluation.material_topology import (
    canonical_material_mask,
    mask_topology,
)

from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.structure.graph import build_structural_layout_graph

# Keep the artifact schema identifier stable for SA10.24 consumers; SA10.25
# changes the authority semantics without changing the serialized contract.
STRUCTURAL_REPAIR_VERSION = "sa10.25-v1"
_OUTER_BOUNDARY_MIN_RECALL = 0.90


_canonical_material_mask = canonical_material_mask


def _topology(mask: np.ndarray) -> tuple[int, int, int]:
    evidence = mask_topology(mask)
    return (
        evidence["components"],
        evidence["holes"],
        evidence["euler_characteristic"],
    )




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
        and row.source_part != "unknown"
        and row.target_part != "unknown"
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
    owner_parts = {
        str(group.get("part") or "")
        for group in groups
        if str(group.get("part") or "") in PART_NAMES
    }
    unreplayable_parts = tuple(sorted(
        part for part in PART_NAMES
        if part == "unknown"
        and np.any(source_masks[part])
        and part not in owner_parts
    ))
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
        # Unknown has no semantic authority by itself.  It may be replayed
        # only when Phase 12 actually emitted an owner group for it.
        if not np.any(source_masks[part]) or (
            part == "unknown" and part not in owner_parts
        ):
            continue
        if _topology(_canonical_material_mask(source_masks[part])) != _topology(
            _canonical_material_mask(current_masks[part])
        ):
            topology_repair_parts.add(part)
    if boundary_recall < _OUTER_BOUNDARY_MIN_RECALL:
        missing_edge = source_edge & ~current_union
        for part in PART_NAMES:
            if np.any(source_masks[part] & missing_edge) and (
                part != "unknown" or part in owner_parts
            ):
                topology_repair_parts.add(part)

    reasons: dict[str, list[str]] = {}
    for part in PART_NAMES:
        source = source_masks[part]
        if not np.any(source) or (part == "unknown" and part not in owner_parts):
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
        if np.any(source_masks[source_part]) and source_part != "unknown" and not source_present:
            repair_parts.append(source_part)
        if (
            np.any(source_masks[target_part])
            and target_part != "unknown"
            and not target_present
        ):
            repair_parts.append(target_part)
        if source_present and target_present:
            if source_part != "unknown" and np.any(source_masks[source_part]):
                repair_parts.append(source_part)
            if target_part != "unknown" and np.any(source_masks[target_part]):
                repair_parts.append(target_part)
        for repair_part in sorted(set(repair_parts)):
            reasons.setdefault(repair_part, []).append(
                f"missing_required_topology:{source_part}:{relation}:{target_part}"
            )

    for part in sorted(topology_repair_parts):
        if _topology(_canonical_material_mask(source_masks[part])) != _topology(
            _canonical_material_mask(current_masks[part])
        ):
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
            "unreplayable_parts": list(unreplayable_parts),
        }

    output = [dict(group) for group in groups if group.get("part") not in repaired_parts]
    for part in repaired_parts:
        source_mask = _canonical_material_mask(source_masks[part])
        existing = [group for group in groups if group.get("part") == part]
        if existing:
            # The repaired extent is owned by the immutable Phase 4 source
            # mask.  Do not spread a surviving Phase 11 fragment's palette
            # color over that extent; it can turn a topology repair into a
            # major-color-mass failure.  Source median is deterministic and
            # keeps color evidence tied to the same owner as the mask.
            color = _median_source_color(image, source_masks[part])
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
        "unreplayable_parts": list(unreplayable_parts),
    }
