"""SA10.33 deterministic part/export/render/full-scene observers.

Research gate only: no geometry generation, no scene mutation, no promotion.
"""
from __future__ import annotations

import cv2
import numpy as np

from minimalizer_zerobase.evaluation.material_topology import (
    canonical_material_mask, mask_topology, tiny_component_area_threshold,
)

WATCH_OWNERS = ("face", "hair", "left_arm", "right_arm")


def _shape_check(first: np.ndarray, second: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(first)
    b = np.asarray(second)
    if a.ndim != 2 or b.shape != a.shape:
        raise ValueError("observer requires same-size 2D masks")
    return a.astype(bool), b.astype(bool)


def mask_fidelity(reference: np.ndarray, observed: np.ndarray) -> dict:
    source, candidate = _shape_check(reference, observed)
    reference_count = int(np.count_nonzero(source))
    observed_count = int(np.count_nonzero(candidate))
    common = int(np.count_nonzero(source & candidate))
    union = int(np.count_nonzero(source | candidate))
    source_top = mask_topology(source)
    observed_top = mask_topology(candidate)
    return {
        "reference_pixels": reference_count,
        "observed_pixels": observed_count,
        "intersection_pixels": common,
        "missing_pixels": int(np.count_nonzero(source & ~candidate)),
        "excess_pixels": int(np.count_nonzero(candidate & ~source)),
        "xor_pixels": int(np.count_nonzero(source ^ candidate)),
        "iou": float(common / union) if union else 1.0,
        "reference_topology": source_top,
        "observed_topology": observed_top,
        "topology_pass": source_top == observed_top,
        "exact": bool(np.array_equal(source, candidate)),
    }


def component_loss_evidence(reference: np.ndarray, candidate: np.ndarray, *, cutoff: int) -> dict:
    a, b = _shape_check(reference, candidate)
    if cutoff < 1:
        raise ValueError("component cutoff must be positive")
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        a.astype(np.uint8), connectivity=8
    )
    record: list[dict] = []
    for index in range(1, count):
        component = labels == index
        pixels = int(stats[index, cv2.CC_STAT_AREA])
        covered = int(np.count_nonzero(component & b))
        if covered == pixels:
            continue
        x, y, w, h = (int(stats[index, axis]) for axis in (
            cv2.CC_STAT_LEFT, cv2.CC_STAT_TOP, cv2.CC_STAT_WIDTH, cv2.CC_STAT_HEIGHT
        ))
        record.append({
            "area": pixels, "overlap_pixels": covered,
            "lost_pixels": pixels - covered,
            "missing_whole_island": covered == 0,
            "below_canonical_threshold": pixels < cutoff,
            "bbox_xywh": [x, y, w, h],
        })
    record.sort(key=lambda x: (-x["lost_pixels"], x["bbox_xywh"]))
    fully_missing = [x for x in record if x["missing_whole_island"]]
    return {
        "source_component_count": count - 1,
        "damaged_components": record,
        "fully_missing_component_count": len(fully_missing),
        "fully_missing_pixels": sum(x["area"] for x in fully_missing),
        "fully_missing_below_threshold_count": sum(x["below_canonical_threshold"] for x in fully_missing),
        "fully_missing_below_threshold_pixels": sum(x["area"] for x in fully_missing if x["below_canonical_threshold"]),
    }


def owner_fidelity(source: np.ndarray, render: np.ndarray, export: np.ndarray) -> dict:
    a, b = _shape_check(source, render)
    _, c = _shape_check(source, export)
    cutoff = tiny_component_area_threshold(int(a.sum()))
    cleaned_source = canonical_material_mask(a, tiny_component_area_threshold=cutoff)
    cleaned_render = canonical_material_mask(b, tiny_component_area_threshold=cutoff)
    cleaned_export = canonical_material_mask(c, tiny_component_area_threshold=cutoff)
    return {
        "canonical_cutoff_pixels": cutoff,
        "source_to_render": mask_fidelity(a, b),
        "source_to_export": mask_fidelity(a, c),
        "render_to_export": mask_fidelity(b, c),
        "diagnostic_canonical_source_to_render": mask_fidelity(cleaned_source, cleaned_render),
        "diagnostic_canonical_source_to_export": mask_fidelity(cleaned_source, cleaned_export),
        "lost_source_components_in_render": component_loss_evidence(a, b, cutoff=cutoff),
        "lost_source_components_in_export": component_loss_evidence(a, c, cutoff=cutoff),
        "export_consistency_pass": bool(np.array_equal(b, c)),
        "raw_source_topology_pass": mask_topology(a) == mask_topology(b) == mask_topology(c),
    }


def zorder_visibility(primitives: list[dict], primitive_masks: dict[str, np.ndarray]) -> dict:
    """Count visible owner pixels before deterministic face raster guard.

    Uses actual source-replayed masks. This never predicts the source's z-order.
    """
    if not primitives:
        raise ValueError("z-order primitive list must be nonempty")
    if not all(p.get("primitive_id") in primitive_masks for p in primitives):
        raise ValueError("missing primitive masks for z-order")
    shape = next(iter(primitive_masks.values())).shape
    if len(shape) != 2:
        raise ValueError("primitive masks must be 2D")
    covered = np.zeros(shape, dtype=bool)
    by_owner: dict[str, dict] = {}
    for primitive in reversed(primitives):
        if primitive.get("structural_support_only"):
            continue
        ident = primitive["primitive_id"]
        owner = primitive.get("semantic_part_id") or primitive.get("composition_part")
        if not isinstance(owner, str):
            raise ValueError("primitive owner missing")
        mask = np.asarray(primitive_masks[ident]).astype(bool)
        if mask.shape != shape:
            raise ValueError("primitive mask canvas mismatch")
        visible = mask & ~covered
        entry = by_owner.setdefault(owner, {"raw_pixels": 0, "visible_pixels": 0, "occluded_pixels": 0})
        entry["raw_pixels"] += int(np.count_nonzero(mask))
        entry["visible_pixels"] += int(np.count_nonzero(visible))
        entry["occluded_pixels"] += int(np.count_nonzero(mask & covered))
        covered |= mask
    return {
        "pre_face_guard_owner_visibility": dict(sorted(by_owner.items())),
        "uncovered_canvas_pixels": int(np.count_nonzero(~covered)),
        "painted_union_pixels": int(np.count_nonzero(covered)),
        "face_guard_is_post_zorder": True,
    }
