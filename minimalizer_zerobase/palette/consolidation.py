from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, Mapping

import numpy as np


CRITICAL_PARTS = frozenset(
    {"face", "hair", "major_clothing", "accessory_or_held_object"}
)


def _rounded(value: float) -> float:
    return round(float(value), 6)


def _distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> float:
    return sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


@dataclass(frozen=True)
class PaletteConsolidationPolicy:
    near_color_distance: float = 30.0
    critical_near_color_distance: float = 18.0
    critical_contrast_distance: float = 28.0
    allow_cross_part_merge: bool = False
    reinterpret_unbound: bool = False
    representative_strategy: str = "source-pixel-mode"

    def __post_init__(self) -> None:
        if self.near_color_distance < 0 or self.critical_near_color_distance < 0:
            raise ValueError("palette merge distances must be non-negative")
        if self.critical_contrast_distance <= 0:
            raise ValueError("critical contrast distance must be positive")
        if self.critical_near_color_distance >= self.critical_contrast_distance:
            raise ValueError(
                "critical merge distance must stay below the contrast guard"
            )
        if self.allow_cross_part_merge:
            raise ValueError("Phase 9 forbids cross-part palette merge")
        if self.reinterpret_unbound:
            raise ValueError("Phase 9 forbids unbound reinterpretation")
        if self.representative_strategy != "source-pixel-mode":
            raise ValueError(
                "Phase 9 representatives must be observed source pixels"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "allow_cross_part_merge": False,
            "critical_contrast_distance": self.critical_contrast_distance,
            "critical_near_color_distance": self.critical_near_color_distance,
            "critical_parts": sorted(CRITICAL_PARTS),
            "near_color_distance": self.near_color_distance,
            "reinterpret_unbound": False,
            "representative_strategy": self.representative_strategy,
        }


@dataclass(frozen=True)
class PaletteEntry:
    palette_id: str
    semantic_part_id: str | None
    color_rgb: tuple[int, int, int]
    source_mass_id: str
    source_pixel_xy: tuple[int, int]
    source_action: str
    protected_anchor: bool
    assigned_mass_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "palette_id": self.palette_id,
            "semantic_part_id": self.semantic_part_id,
            "color_rgb": list(self.color_rgb),
            "source_mass_id": self.source_mass_id,
            "source_pixel_xy": list(self.source_pixel_xy),
            "source_action": self.source_action,
            "protected_anchor": self.protected_anchor,
            "assigned_mass_ids": list(self.assigned_mass_ids),
            "representative_provenance": "observed-source-pixel",
        }


@dataclass(frozen=True)
class PaletteAssignment:
    mass_id: str
    semantic_part_id: str | None
    binding_status: str
    action: str
    pixel_count: int
    bbox_xywh: tuple[int, int, int, int]
    source_color_rgb: tuple[int, int, int]
    source_pixel_xy: tuple[int, int]
    palette_id: str | None
    palette_color_rgb: tuple[int, int, int] | None
    assignment_kind: str
    color_distance: float | None
    merge_rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "mass_id": self.mass_id,
            "semantic_part_id": self.semantic_part_id,
            "binding_status": self.binding_status,
            "action": self.action,
            "pixel_count": self.pixel_count,
            "bbox_xywh": list(self.bbox_xywh),
            "source_color_rgb": list(self.source_color_rgb),
            "source_pixel_xy": list(self.source_pixel_xy),
            "palette_id": self.palette_id,
            "palette_color_rgb": (
                list(self.palette_color_rgb)
                if self.palette_color_rgb is not None
                else None
            ),
            "assignment_kind": self.assignment_kind,
            "color_distance": (
                _rounded(self.color_distance)
                if self.color_distance is not None
                else None
            ),
            "merge_rationale": self.merge_rationale,
        }


@dataclass(frozen=True)
class PaletteConsolidationResult:
    width: int
    height: int
    palette: tuple[PaletteEntry, ...]
    assignments: tuple[PaletteAssignment, ...]
    validation: dict[str, Any]
    policy: PaletteConsolidationPolicy
    mass_labels: np.ndarray

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "coordinate_space": {
                "pixel_width": self.width,
                "pixel_height": self.height,
                "normalized_origin": "top-left",
                "normalized_range": [0.0, 1.0],
            },
            "palette_policy": self.policy.to_dict(),
            "palette": [entry.to_dict() for entry in self.palette],
            "assignments": [item.to_dict() for item in self.assignments],
            "validation": self.validation,
        }


def _decode_runs(runs: Any, *, width: int, height: int) -> np.ndarray:
    if not isinstance(runs, list):
        raise ValueError("Phase 7 mass pixel_runs must be a list")
    mask = np.zeros((height, width), dtype=bool)
    for raw in runs:
        if not isinstance(raw, (list, tuple)) or len(raw) != 3:
            raise ValueError("Phase 7 mass pixel_runs must contain [y, x0, x1]")
        y, x0, x1 = (int(raw[0]), int(raw[1]), int(raw[2]))
        if not (0 <= y < height and 0 <= x0 < x1 <= width):
            raise ValueError("Phase 7 mass pixel run is outside the canvas")
        if np.any(mask[y, x0:x1]):
            raise ValueError("Phase 7 mass pixel_runs overlap")
        mask[y, x0:x1] = True
    return mask


def _source_representative(
    image: np.ndarray,
    mask: np.ndarray,
    declared_mean: Any,
) -> tuple[tuple[int, int, int], tuple[int, int]]:
    pixels = image[mask]
    if pixels.size == 0:
        raise ValueError("Phase 9 cannot represent an empty mass")
    colors, counts = np.unique(pixels, axis=0, return_counts=True)
    mean = np.asarray(declared_mean, dtype=np.float64)
    if mean.shape != (3,) or not np.all(np.isfinite(mean)):
        raise ValueError("Phase 7 mean_rgb must contain three finite values")
    ranked = sorted(
        (
            float(np.sum((color.astype(np.float64) - mean) ** 2)),
            -int(count),
            tuple(int(value) for value in color),
        )
        for color, count in zip(colors, counts)
    )
    color = ranked[0][2]
    match = mask & np.all(image == np.asarray(color, dtype=np.uint8), axis=2)
    locations = np.argwhere(match)
    if locations.size == 0:
        raise ValueError("source representative is not present in its mass")
    y, x = (int(locations[0, 0]), int(locations[0, 1]))
    return color, (x, y)


def consolidate_palette(
    source_rgb: np.ndarray,
    phase7_payload: Mapping[str, Any],
    phase8_payload: Mapping[str, Any],
    mass_labels: np.ndarray,
    *,
    policy: PaletteConsolidationPolicy | None = None,
) -> PaletteConsolidationResult:
    policy = policy or PaletteConsolidationPolicy()
    image = np.asarray(source_rgb, dtype=np.uint8)
    if image.ndim != 3 or image.shape[2] < 3:
        raise ValueError("Phase 9 requires an RGB source image")
    image = image[..., :3]

    coordinate = phase7_payload.get("coordinate_space")
    if not isinstance(coordinate, Mapping):
        raise ValueError("Phase 9 requires Phase 7 coordinate_space")
    width = int(coordinate.get("pixel_width", 0))
    height = int(coordinate.get("pixel_height", 0))
    if width <= 0 or height <= 0 or image.shape[:2] != (height, width):
        raise ValueError("Phase 9 source dimensions must match Phase 7")
    if phase7_payload.get("validation", {}).get("pass") is not True:
        raise ValueError("Phase 9 requires a passing Phase 7 result")
    if phase8_payload.get("validation", {}).get("pass") is not True:
        raise ValueError("Phase 9 requires a passing Phase 8 result")

    raw_labels = np.asarray(mass_labels)
    if raw_labels.shape != (height, width):
        raise ValueError("Phase 7 mass labels do not match coordinate space")
    labels = raw_labels.astype(np.int64, copy=True)
    labels[labels == 65535] = -1

    raw_masses = phase7_payload.get("masses")
    raw_decisions = phase8_payload.get("decisions")
    if not isinstance(raw_masses, list) or not raw_masses:
        raise ValueError("Phase 9 requires non-empty Phase 7 masses")
    if not isinstance(raw_decisions, list):
        raise ValueError("Phase 9 requires Phase 8 decisions")
    if np.any(labels >= len(raw_masses)):
        raise ValueError("Phase 7 labels reference a missing mass")

    decisions: dict[str, Mapping[str, Any]] = {}
    for raw in raw_decisions:
        if not isinstance(raw, Mapping):
            raise ValueError("Phase 8 decisions must be objects")
        mass_id = str(raw.get("mass_id", ""))
        if not mass_id or mass_id in decisions:
            raise ValueError("Phase 8 mass_id must be present and unique")
        decisions[mass_id] = raw

    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(raw_masses):
        if not isinstance(raw, Mapping):
            raise ValueError("Phase 7 masses must be objects")
        mass_id = str(raw.get("mass_id", ""))
        if not mass_id or mass_id in seen_ids:
            raise ValueError("Phase 7 mass_id must be present and unique")
        seen_ids.add(mass_id)
        decision = decisions.get(mass_id)
        if decision is None:
            raise ValueError(f"Phase 8 decision missing for {mass_id}")

        status = str(raw.get("binding_status", ""))
        part_id = raw.get("semantic_part_id")
        if status == "bound" and not isinstance(part_id, str):
            raise ValueError("bound Phase 7 mass requires semantic_part_id")
        if status == "unbound" and part_id is not None:
            raise ValueError("unbound Phase 7 mass must not claim semantic_part_id")
        if status not in {"bound", "unbound"}:
            raise ValueError("unsupported Phase 7 binding_status")
        action = str(decision.get("action", ""))
        if action not in {"protect", "keep", "prune"}:
            raise ValueError("unsupported Phase 8 action")
        if decision.get("semantic_part_id") != part_id:
            raise ValueError(f"Phase 8 semantic owner drift for {mass_id}")
        if decision.get("binding_status") != status:
            raise ValueError(f"Phase 8 binding status drift for {mass_id}")

        mask = labels == index
        pixel_count = int(np.count_nonzero(mask))
        if pixel_count <= 0 or pixel_count != int(raw.get("pixel_count", -1)):
            raise ValueError(f"Phase 7 pixel_count mismatch for {mass_id}")
        if int(decision.get("pixel_count", -1)) != pixel_count:
            raise ValueError(f"Phase 8 pixel_count drift for {mass_id}")
        if not np.array_equal(
            _decode_runs(raw.get("pixel_runs"), width=width, height=height),
            mask,
        ):
            raise ValueError(f"Phase 7 labels and pixel_runs disagree for {mass_id}")
        ys, xs = np.where(mask)
        bbox = (
            int(xs.min()),
            int(ys.min()),
            int(xs.max() - xs.min() + 1),
            int(ys.max() - ys.min() + 1),
        )
        declared_bbox = tuple(int(value) for value in raw.get("bbox_xywh", ()))
        if declared_bbox != bbox:
            raise ValueError(f"Phase 7 bbox drift for {mass_id}")
        color, source_xy = _source_representative(
            image,
            mask,
            raw.get("mean_rgb"),
        )
        rationale = tuple(str(item) for item in decision.get("rationale", ()))
        if status == "unbound" and action == "prune":
            raise ValueError("Phase 9 refuses a pruned unbound mass")
        if part_id in {"face", "accessory_or_held_object"} and action != "protect":
            raise ValueError("Phase 9 requires face/accessory anchors to be protected")
        records.append(
            {
                "index": index,
                "mass_id": mass_id,
                "semantic_part_id": part_id,
                "binding_status": status,
                "action": action,
                "pixel_count": pixel_count,
                "bbox_xywh": bbox,
                "source_color": color,
                "source_xy": source_xy,
                "rationale": rationale,
                "mask": mask,
            }
        )
    if set(decisions) != seen_ids:
        raise ValueError("Phase 8 decisions contain unknown masses")

    groups: list[dict[str, Any]] = []
    record_group: dict[str, dict[str, Any]] = {}
    by_part: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record["action"] == "prune" or record["binding_status"] == "unbound":
            continue
        by_part.setdefault(str(record["semantic_part_id"]), []).append(record)

    for part_id, part_records in sorted(by_part.items()):
        ordered = sorted(
            part_records,
            key=lambda item: (
                0 if item["action"] == "protect" else 1,
                -item["pixel_count"],
                item["mass_id"],
            ),
        )
        threshold = (
            policy.critical_near_color_distance
            if part_id in CRITICAL_PARTS
            else policy.near_color_distance
        )
        part_groups: list[dict[str, Any]] = []
        for record in ordered:
            nearest = min(
                part_groups,
                key=lambda group: (
                    _distance(record["source_color"], group["color"]),
                    group["source_mass_id"],
                ),
                default=None,
            )
            distance = (
                _distance(record["source_color"], nearest["color"])
                if nearest is not None
                else None
            )
            if nearest is None or distance is None or distance > threshold:
                group = {
                    "semantic_part_id": part_id,
                    "color": record["source_color"],
                    "source_mass_id": record["mass_id"],
                    "source_xy": record["source_xy"],
                    "source_action": record["action"],
                    "members": [record["mass_id"]],
                }
                part_groups.append(group)
                groups.append(group)
                record_group[record["mass_id"]] = group
            else:
                nearest["members"].append(record["mass_id"])
                record_group[record["mass_id"]] = nearest

    for record in sorted(records, key=lambda item: item["mass_id"]):
        if record["binding_status"] != "unbound" or record["action"] == "prune":
            continue
        group = {
            "semantic_part_id": None,
            "color": record["source_color"],
            "source_mass_id": record["mass_id"],
            "source_xy": record["source_xy"],
            "source_action": record["action"],
            "members": [record["mass_id"]],
        }
        groups.append(group)
        record_group[record["mass_id"]] = group

    ordered_groups = sorted(
        groups,
        key=lambda group: (
            group["semantic_part_id"] is None,
            group["semantic_part_id"] or "",
            group["source_mass_id"],
        ),
    )
    group_ids = {id(group): f"palette-{index:04d}" for index, group in enumerate(ordered_groups)}
    palette = tuple(
        PaletteEntry(
            palette_id=group_ids[id(group)],
            semantic_part_id=group["semantic_part_id"],
            color_rgb=group["color"],
            source_mass_id=group["source_mass_id"],
            source_pixel_xy=group["source_xy"],
            source_action=group["source_action"],
            protected_anchor=group["source_action"] == "protect",
            assigned_mass_ids=tuple(sorted(group["members"])),
        )
        for group in ordered_groups
    )

    assignments: list[PaletteAssignment] = []
    for record in records:
        if record["action"] == "prune":
            group = None
            kind = "pruned"
            rationale = "phase8-prune-remains-omitted"
        else:
            group = record_group[record["mass_id"]]
            if record["binding_status"] == "unbound":
                kind = "unbound-isolated"
                rationale = "unbound-preserved-without-merge-or-owner"
            elif group["source_mass_id"] == record["mass_id"]:
                kind = "part-anchor"
                rationale = "source-derived-same-part-anchor"
            else:
                kind = "same-part-near-color"
                rationale = "same-semantic-part-near-color-merge"
        palette_color = group["color"] if group is not None else None
        assignments.append(
            PaletteAssignment(
                mass_id=record["mass_id"],
                semantic_part_id=record["semantic_part_id"],
                binding_status=record["binding_status"],
                action=record["action"],
                pixel_count=record["pixel_count"],
                bbox_xywh=record["bbox_xywh"],
                source_color_rgb=record["source_color"],
                source_pixel_xy=record["source_xy"],
                palette_id=group_ids[id(group)] if group is not None else None,
                palette_color_rgb=palette_color,
                assignment_kind=kind,
                color_distance=(
                    _distance(record["source_color"], palette_color)
                    if palette_color is not None
                    else None
                ),
                merge_rationale=rationale,
            )
        )

    cross_part_merge_count = 0
    unbound_merge_count = 0
    source_derived_violation_count = 0
    for entry in palette:
        members = [next(item for item in records if item["mass_id"] == mass_id) for mass_id in entry.assigned_mass_ids]
        owners = {item["semantic_part_id"] for item in members}
        if len(owners) != 1:
            cross_part_merge_count += 1
        if entry.semantic_part_id is None and len(members) != 1:
            unbound_merge_count += 1
        x, y = entry.source_pixel_xy
        source_record = next(item for item in records if item["mass_id"] == entry.source_mass_id)
        if (
            not source_record["mask"][y, x]
            or tuple(int(value) for value in image[y, x]) != entry.color_rgb
        ):
            source_derived_violation_count += 1

    critical_contrast_violation_count = sum(
        1
        for item in assignments
        if item.semantic_part_id in CRITICAL_PARTS
        and item.palette_color_rgb is not None
        and item.assignment_kind == "same-part-near-color"
        and _distance(item.source_color_rgb, item.palette_color_rgb)
        >= policy.critical_contrast_distance
    )
    prune_resurrection_count = sum(
        1
        for item in assignments
        if item.action == "prune" and item.palette_id is not None
    )
    critical_anchor_violation_count = sum(
        1
        for part_id in sorted(CRITICAL_PARTS)
        if part_id in by_part
        and not any(
            entry.semantic_part_id == part_id and entry.protected_anchor
            for entry in palette
        )
    )
    active_count = sum(item.action != "prune" for item in assignments)
    same_part_merge_count = sum(
        max(0, len(entry.assigned_mass_ids) - 1)
        for entry in palette
        if entry.semantic_part_id is not None
    )
    validation = {
        "mass_count": len(assignments),
        "active_mass_count": active_count,
        "pruned_mass_count": len(assignments) - active_count,
        "palette_entry_count": len(palette),
        "unique_palette_rgb_count": len({entry.color_rgb for entry in palette}),
        "same_part_merge_count": same_part_merge_count,
        "palette_reduction_ratio": _rounded(
            1.0 - len(palette) / float(active_count) if active_count else 0.0
        ),
        "cross_part_merge_count": cross_part_merge_count,
        "unbound_merge_count": unbound_merge_count,
        "unbound_reinterpretation_count": 0,
        "prune_resurrection_count": prune_resurrection_count,
        "critical_contrast_violation_count": critical_contrast_violation_count,
        "critical_anchor_violation_count": critical_anchor_violation_count,
        "source_derived_representative_violation_count": source_derived_violation_count,
        "semantic_owner_change_count": 0,
        "action_change_count": 0,
        "geometry_change_count": 0,
        "representative_strategy": policy.representative_strategy,
        "pass": all(
            count == 0
            for count in (
                cross_part_merge_count,
                unbound_merge_count,
                prune_resurrection_count,
                critical_contrast_violation_count,
                critical_anchor_violation_count,
                source_derived_violation_count,
            )
        ),
    }
    return PaletteConsolidationResult(
        width=width,
        height=height,
        palette=palette,
        assignments=tuple(assignments),
        validation=validation,
        policy=policy,
        mass_labels=labels,
    )
