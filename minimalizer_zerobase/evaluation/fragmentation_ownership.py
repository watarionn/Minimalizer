from __future__ import annotations

from typing import Any, Mapping, Sequence

import cv2
import numpy as np

from minimalizer_zerobase.composition.semantic import (
    rasterize_primitive_candidate,
)


def _coordinate(payload: Mapping[str, Any]) -> tuple[int, int]:
    space = payload.get("coordinate_space")
    if not isinstance(space, Mapping):
        raise ValueError("fragmentation ownership requires coordinate_space")
    width = int(space.get("pixel_width", 0))
    height = int(space.get("pixel_height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("fragmentation ownership requires positive dimensions")
    return width, height


def _selected_candidate(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    selected_name = payload.get("selected_name")
    candidates = payload.get("candidates")
    if not isinstance(selected_name, str) or not isinstance(candidates, Sequence):
        raise ValueError("fragmentation ownership requires a selected candidate")
    for item in candidates:
        if isinstance(item, Mapping) and item.get("name") == selected_name:
            return item
    raise ValueError("fragmentation ownership cannot resolve selected candidate")


def _component_rows(mask: np.ndarray) -> list[dict[str, Any]]:
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8), connectivity=8
    )
    rows: list[dict[str, Any]] = []
    for label in range(1, count):
        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        width = int(stats[label, cv2.CC_STAT_WIDTH])
        height = int(stats[label, cv2.CC_STAT_HEIGHT])
        rows.append(
            {
                "area": int(stats[label, cv2.CC_STAT_AREA]),
                "bbox_xywh": [x, y, width, height],
                "centroid_xy": [
                    round(float(centroids[label, 0]), 6),
                    round(float(centroids[label, 1]), 6),
                ],
                "mask": labels == label,
            }
        )
    return rows


def _mass_mask(
    mass: Mapping[str, Any], *, width: int, height: int
) -> np.ndarray:
    mask = np.zeros((height, width), dtype=bool)
    runs = mass.get("pixel_runs")
    if not isinstance(runs, Sequence):
        return mask
    for run in runs:
        if not isinstance(run, Sequence) or len(run) != 3:
            raise ValueError("invalid Phase 7 mass pixel run")
        y, x0, x1 = (int(value) for value in run)
        if y < 0 or y >= height or x0 < 0 or x1 > width or x0 >= x1:
            raise ValueError("out-of-bounds Phase 7 mass pixel run")
        mask[y, x0:x1] = True
    return mask


def build_fragmentation_ownership_report(
    *,
    phase7_payload: Mapping[str, Any],
    phase8_payload: Mapping[str, Any],
    phase9_payload: Mapping[str, Any],
    phase11_payload: Mapping[str, Any],
    phase12_payload: Mapping[str, Any],
    subject_area: int,
    tiny_component_area_ratio: float = 0.00015,
) -> dict[str, Any]:
    """Trace every selected Phase 12 component back to its semantic owner.

    The report uses the same per-primitive, 8-connected definition as Phase 14.
    It is diagnostic only: it neither changes the evaluation threshold nor
    grants calibration or rendering authority.
    """

    width, height = _coordinate(phase12_payload)
    if _coordinate(phase11_payload) != (width, height):
        raise ValueError("Phase 11/12 coordinate mismatch")
    threshold = max(8, int(round(subject_area * tiny_component_area_ratio)))

    decisions = {
        str(item["mass_id"]): item
        for item in phase8_payload.get("decisions", [])
        if isinstance(item, Mapping) and item.get("mass_id") is not None
    }
    assignments = {
        str(item["mass_id"]): item
        for item in phase9_payload.get("assignments", [])
        if isinstance(item, Mapping) and item.get("mass_id") is not None
    }
    masses = {
        str(item["mass_id"]): item
        for item in phase7_payload.get("masses", [])
        if isinstance(item, Mapping) and item.get("mass_id") is not None
    }
    phase11_primitives = {
        str(item["primitive_id"]): item
        for item in phase11_payload.get("primitives_back_to_front", [])
        if isinstance(item, Mapping) and item.get("primitive_id") is not None
    }
    phase11_masks = {
        primitive_id: rasterize_primitive_candidate(
            primitive, width=width, height=height
        )
        for primitive_id, primitive in phase11_primitives.items()
    }
    phase7_masks = {
        mass_id: _mass_mask(mass, width=width, height=height)
        for mass_id, mass in masses.items()
    }

    selected = _selected_candidate(phase12_payload)
    primitives = selected.get("primitives")
    if not isinstance(primitives, Sequence):
        raise ValueError("selected Phase 12 candidate requires primitives")

    component_rows: list[dict[str, Any]] = []
    tiny_count = 0
    for primitive in primitives:
        if not isinstance(primitive, Mapping):
            continue
        primitive_id = str(primitive.get("primitive_id", ""))
        mask = rasterize_primitive_candidate(
            primitive, width=width, height=height
        )
        source_ids_value = primitive.get("source_primitive_ids")
        if isinstance(source_ids_value, Sequence) and not isinstance(
            source_ids_value, (str, bytes)
        ):
            source_ids = [str(value) for value in source_ids_value]
        elif primitive_id in phase11_primitives:
            source_ids = [primitive_id]
        else:
            source_ids = []

        source_primitives = [
            phase11_primitives[source_id]
            for source_id in source_ids
            if source_id in phase11_primitives
        ]
        mass_ids = sorted(
            {
                str(item["mass_id"])
                for item in source_primitives
                if item.get("mass_id") is not None
            }
        )
        actions = sorted(
            {
                str(decisions[mass_id].get("action"))
                for mass_id in mass_ids
                if mass_id in decisions
            }
        )
        palette_ids = sorted(
            {
                str(assignments[mass_id].get("palette_id"))
                for mass_id in mass_ids
                if mass_id in assignments
            }
        )

        for component_index, component in enumerate(_component_rows(mask)):
            area = int(component["area"])
            tiny = area < threshold
            if tiny:
                tiny_count += 1
            component_mask = component.pop("mask")
            source_overlap = {
                source_id: int(
                    np.count_nonzero(component_mask & phase11_masks[source_id])
                )
                for source_id in source_ids
                if source_id in phase11_masks
            }
            source_overlap = {
                key: value for key, value in source_overlap.items() if value > 0
            }
            phase7_overlap = {
                mass_id: int(
                    np.count_nonzero(component_mask & phase7_masks[mass_id])
                )
                for mass_id in mass_ids
                if mass_id in phase7_masks
            }
            phase7_overlap = {
                key: value for key, value in phase7_overlap.items() if value > 0
            }
            if not tiny:
                origin = "not-tiny"
            elif primitive.get("source_guided_kind"):
                origin = "phase12-source-guided-emission"
            elif any(
                any(
                    int(row["area"]) < threshold
                    and np.any(component_mask & row["mask"])
                    for row in _component_rows(phase11_masks[source_id])
                )
                for source_id in source_overlap
            ):
                origin = "phase10-selected-primitive"
            elif source_overlap:
                origin = "phase12-regrouping"
            else:
                origin = "phase12-untraced"

            component_rows.append(
                {
                    "primitive_id": primitive_id,
                    "component_index": component_index,
                    "semantic_part_id": primitive.get("semantic_part_id"),
                    "composition_part": primitive.get("composition_part"),
                    "binding_status": primitive.get("binding_status"),
                    "structural_support_only": bool(
                        primitive.get("structural_support_only", False)
                    ),
                    "source_guided_kind": primitive.get("source_guided_kind"),
                    "source_primitive_ids": source_ids,
                    "mass_ids": mass_ids,
                    "phase8_actions": actions,
                    "phase9_palette_ids": palette_ids,
                    "phase11_overlap_pixels": source_overlap,
                    "phase7_overlap_pixels": phase7_overlap,
                    "origin": origin,
                    "tiny": tiny,
                    **component,
                }
            )

    tiny_rows = [row for row in component_rows if row["tiny"]]
    origin_counts: dict[str, int] = {}
    owner_counts: dict[str, int] = {}
    action_counts: dict[str, int] = {}
    for row in tiny_rows:
        origin = str(row["origin"])
        owner = str(row.get("composition_part") or "__unbound__")
        origin_counts[origin] = origin_counts.get(origin, 0) + 1
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
        for action in row["phase8_actions"]:
            action_counts[action] = action_counts.get(action, 0) + 1

    return {
        "schema_version": "sa10.17-fragmentation-ownership-v1",
        "selected_profile": phase12_payload.get("selected_name"),
        "coordinate_space": {
            "pixel_width": width,
            "pixel_height": height,
        },
        "policy": {
            "tiny_component_area_ratio": tiny_component_area_ratio,
            "tiny_component_area_threshold": threshold,
            "connectivity": 8,
            "threshold_changed": False,
            "aggregate_score": False,
            "calibration_authority": False,
        },
        "summary": {
            "component_count": len(component_rows),
            "tiny_component_count": tiny_count,
            "fragmentation_penalty": float(
                tiny_count / max(len(component_rows), 1)
            ),
            "tiny_origin_counts": dict(sorted(origin_counts.items())),
            "tiny_owner_counts": dict(sorted(owner_counts.items())),
            "tiny_phase8_action_counts": dict(sorted(action_counts.items())),
        },
        "tiny_components": tiny_rows,
        "components": component_rows,
    }
