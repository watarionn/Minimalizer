from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import cv2
import numpy as np

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from .structural_source_repair import apply_structural_source_repair


UNBOUND_PART = "__unbound__"


@dataclass(frozen=True)
class SimplificationProfile:
    name: str
    epsilon_ratio: float
    min_component_area_ratio: float
    merge_gap_px: int
    minimum_silhouette_iou: float
    minimum_critical_part_recall: float
    minimum_critical_part_iou: float


@dataclass(frozen=True)
class StyleSimplificationPolicy:
    conservative: SimplificationProfile = SimplificationProfile(
        name="conservative",
        epsilon_ratio=0.006,
        min_component_area_ratio=0.00006,
        merge_gap_px=1,
        minimum_silhouette_iou=0.965,
        minimum_critical_part_recall=0.90,
        minimum_critical_part_iou=0.92,
    )
    aggressive: SimplificationProfile = SimplificationProfile(
        name="aggressive",
        epsilon_ratio=0.015,
        min_component_area_ratio=0.00025,
        merge_gap_px=2,
        minimum_silhouette_iou=0.92,
        minimum_critical_part_recall=0.82,
        minimum_critical_part_iou=0.84,
    )
    critical_parts: tuple[str, ...] = (
        "face",
        "hair",
        "torso",
        "left_arm",
        "right_arm",
        "major_clothing",
        "accessory_or_held_object",
    )
    minimum_visible_part_pixels: int = 8
    support_only_parts: tuple[str, ...] = ("head",)
    minimum_support_only_part_pixels: int = 64
    structural_source_repair: bool = True
    structural_minimum_bbox_area_ratio: float = 0.35
    structural_maximum_bbox_area_ratio: float = 2.8
    source_guided_lower_body: bool = True
    source_guided_foot: bool = True
    source_guided_face: bool = True
    source_guided_hair: bool = True
    source_guided_torso_color: bool = True
    source_guided_wrist_skin: bool = True
    wrist_skin_min_arm_area_ratio: float = 0.003
    wrist_skin_max_arm_area_ratio: float = 0.02
    wrist_skin_min_local_delta: float = 60.0
    wrist_skin_max_face_lab_distance: float = 35.0
    wrist_skin_existing_unbound_max_area_ratio: float = 0.001
    wrist_skin_output_area_ratio: float = 0.00005
    wrist_skin_epsilon_ratio: float = 0.010
    torso_color_quantile: float = 0.50
    torso_color_max_median_luminance: float = 96.0
    torso_color_min_luminance_span: float = 12.0
    face_min_retained_area_ratio: float = 0.96
    lower_body_split_min_y_ratio: float = 0.60
    lower_body_light_component_area_ratio: float = 0.001
    lower_body_panel_color_quantile: float = 0.90
    lower_body_panel_epsilon_ratio: float = 0.008
    lower_body_panel_min_retained_ratio: float = 0.90
    lower_body_panel_max_expansion_ratio: float = 1.15
    lower_body_foot_component_area_ratio: float = 0.00035
    lower_body_foot_zone_start_ratio: float = 0.60
    lower_body_foot_light_min_area_ratio: float = 0.015
    lower_body_foot_light_max_area_ratio: float = 0.25
    lower_body_foot_light_min_delta: float = 60.0
    lower_body_foot_light_min_elongation: float = 1.6
    lower_body_foot_light_output_area_ratio: float = 0.00015
    lower_body_foot_light_epsilon_ratio: float = 0.015
    lower_body_leg_foot_epsilon_ratio: float = 0.0025
    lower_body_dark_foot_epsilon_ratio: float = 0.005
    major_clothing_palette_merge_delta: int = 12
    accessory_palette_merge_delta: int = 32
    unbound_palette_merge_delta: int = 40
    unbound_neutral_micro_max_area_ratio: float = 0.00045
    unbound_neutral_micro_max_channel_range: int = 12
    right_arm_palette_merge_delta: int = 22
    hair_min_hole_area_ratio: float = 0.0005
    hair_highlight_source_min_area_ratio: float = 0.002
    hair_highlight_component_area_ratio: float = 0.0002
    hair_highlight_max_components: int = 3
    hair_highlight_hull_expansion_limit: float = 1.42
    hair_highlight_max_base_saturation: int = 96
    hair_highlight_color_quantile: float = 0.90
    hair_highlight_min_plane_luminance_quantile: float = 0.90
    hair_local_contrast_min_area_ratio: float = 0.005
    hair_local_contrast_max_area_ratio: float = 0.04
    hair_local_contrast_min_delta: float = 30.0
    hair_local_contrast_min_elongation: float = 2.0
    hair_local_contrast_color_quantile: float = 0.90
    hair_local_contrast_epsilon_ratio: float = 0.006
    hair_crown_min_area_ratio: float = 0.006
    hair_crown_max_area_ratio: float = 0.04
    hair_crown_min_delta: float = 60.0
    hair_crown_color_quantile: float = 0.80
    hair_crown_output_area_ratio: float = 0.00015
    hair_crown_epsilon_ratio: float = 0.020
    hair_light_palette_merge_delta: int = 16
    hair_highlight_min_luminance_span: float = 12.0
    hair_epsilon_cap: float = 0.00125
    face_epsilon_cap: float = 0.008
    accessory_epsilon_cap: float = 0.004
    accessory_min_component_area_ratio: float = 0.00008
    arm_epsilon_cap: float = 0.002
    lower_body_epsilon_cap: float = 0.0025
    torso_epsilon_cap: float = 0.004
    major_clothing_epsilon_cap: float = 0.0011

    def to_dict(self) -> dict[str, Any]:
        def profile(item: SimplificationProfile) -> dict[str, Any]:
            return {
                "name": item.name,
                "epsilon_ratio": item.epsilon_ratio,
                "min_component_area_ratio": item.min_component_area_ratio,
                "merge_gap_px": item.merge_gap_px,
                "minimum_silhouette_iou": item.minimum_silhouette_iou,
                "minimum_critical_part_recall": item.minimum_critical_part_recall,
                "minimum_critical_part_iou": item.minimum_critical_part_iou,
            }
        return {
            "profiles": [profile(self.conservative), profile(self.aggressive)],
            "critical_parts": list(self.critical_parts),
            "minimum_visible_part_pixels": self.minimum_visible_part_pixels,
            "support_only_parts": list(self.support_only_parts),
            "minimum_support_only_part_pixels": self.minimum_support_only_part_pixels,
            "structural_source_repair": self.structural_source_repair,
            "structural_minimum_bbox_area_ratio": self.structural_minimum_bbox_area_ratio,
            "structural_maximum_bbox_area_ratio": self.structural_maximum_bbox_area_ratio,
            "source_guided_lower_body": self.source_guided_lower_body,
            "source_guided_foot": self.source_guided_foot,
            "source_guided_face": self.source_guided_face,
            "source_guided_hair": self.source_guided_hair,
            "source_guided_torso_color": self.source_guided_torso_color,
            "source_guided_wrist_skin": self.source_guided_wrist_skin,
            "wrist_skin_min_arm_area_ratio": self.wrist_skin_min_arm_area_ratio,
            "wrist_skin_max_arm_area_ratio": self.wrist_skin_max_arm_area_ratio,
            "wrist_skin_min_local_delta": self.wrist_skin_min_local_delta,
            "wrist_skin_max_face_lab_distance": self.wrist_skin_max_face_lab_distance,
            "wrist_skin_existing_unbound_max_area_ratio": self.wrist_skin_existing_unbound_max_area_ratio,
            "wrist_skin_output_area_ratio": self.wrist_skin_output_area_ratio,
            "wrist_skin_epsilon_ratio": self.wrist_skin_epsilon_ratio,
            "torso_color_quantile": self.torso_color_quantile,
            "torso_color_max_median_luminance": self.torso_color_max_median_luminance,
            "torso_color_min_luminance_span": self.torso_color_min_luminance_span,
            "face_min_retained_area_ratio": self.face_min_retained_area_ratio,
            "lower_body_split_min_y_ratio": self.lower_body_split_min_y_ratio,
            "lower_body_light_component_area_ratio": self.lower_body_light_component_area_ratio,
            "lower_body_panel_color_quantile": self.lower_body_panel_color_quantile,
            "lower_body_panel_epsilon_ratio": self.lower_body_panel_epsilon_ratio,
            "lower_body_panel_min_retained_ratio": self.lower_body_panel_min_retained_ratio,
            "lower_body_panel_max_expansion_ratio": self.lower_body_panel_max_expansion_ratio,
            "lower_body_foot_component_area_ratio": self.lower_body_foot_component_area_ratio,
            "lower_body_foot_zone_start_ratio": self.lower_body_foot_zone_start_ratio,
            "lower_body_foot_light_min_area_ratio": self.lower_body_foot_light_min_area_ratio,
            "lower_body_foot_light_max_area_ratio": self.lower_body_foot_light_max_area_ratio,
            "lower_body_foot_light_min_delta": self.lower_body_foot_light_min_delta,
            "lower_body_foot_light_min_elongation": self.lower_body_foot_light_min_elongation,
            "lower_body_foot_light_output_area_ratio": self.lower_body_foot_light_output_area_ratio,
            "lower_body_foot_light_epsilon_ratio": self.lower_body_foot_light_epsilon_ratio,
            "lower_body_leg_foot_epsilon_ratio": self.lower_body_leg_foot_epsilon_ratio,
            "lower_body_dark_foot_epsilon_ratio": self.lower_body_dark_foot_epsilon_ratio,
            "major_clothing_palette_merge_delta": self.major_clothing_palette_merge_delta,
            "accessory_palette_merge_delta": self.accessory_palette_merge_delta,
            "unbound_palette_merge_delta": self.unbound_palette_merge_delta,
            "unbound_neutral_micro_max_area_ratio": self.unbound_neutral_micro_max_area_ratio,
            "unbound_neutral_micro_max_channel_range": self.unbound_neutral_micro_max_channel_range,
            "right_arm_palette_merge_delta": self.right_arm_palette_merge_delta,
            "hair_min_hole_area_ratio": self.hair_min_hole_area_ratio,
            "hair_highlight_source_min_area_ratio": self.hair_highlight_source_min_area_ratio,
            "hair_highlight_component_area_ratio": self.hair_highlight_component_area_ratio,
            "hair_highlight_max_components": self.hair_highlight_max_components,
            "hair_highlight_hull_expansion_limit": self.hair_highlight_hull_expansion_limit,
            "hair_highlight_max_base_saturation": self.hair_highlight_max_base_saturation,
            "hair_highlight_color_quantile": self.hair_highlight_color_quantile,
            "hair_highlight_min_plane_luminance_quantile": self.hair_highlight_min_plane_luminance_quantile,
            "hair_local_contrast_min_area_ratio": self.hair_local_contrast_min_area_ratio,
            "hair_local_contrast_max_area_ratio": self.hair_local_contrast_max_area_ratio,
            "hair_local_contrast_min_delta": self.hair_local_contrast_min_delta,
            "hair_local_contrast_min_elongation": self.hair_local_contrast_min_elongation,
            "hair_local_contrast_color_quantile": self.hair_local_contrast_color_quantile,
            "hair_local_contrast_epsilon_ratio": self.hair_local_contrast_epsilon_ratio,
            "hair_crown_min_area_ratio": self.hair_crown_min_area_ratio,
            "hair_crown_max_area_ratio": self.hair_crown_max_area_ratio,
            "hair_crown_min_delta": self.hair_crown_min_delta,
            "hair_crown_color_quantile": self.hair_crown_color_quantile,
            "hair_crown_output_area_ratio": self.hair_crown_output_area_ratio,
            "hair_crown_epsilon_ratio": self.hair_crown_epsilon_ratio,
            "hair_light_palette_merge_delta": self.hair_light_palette_merge_delta,
            "hair_highlight_min_luminance_span": self.hair_highlight_min_luminance_span,
            "hair_epsilon_cap": self.hair_epsilon_cap,
            "face_epsilon_cap": self.face_epsilon_cap,
            "accessory_epsilon_cap": self.accessory_epsilon_cap,
            "accessory_min_component_area_ratio": self.accessory_min_component_area_ratio,
            "arm_epsilon_cap": self.arm_epsilon_cap,
            "lower_body_epsilon_cap": self.lower_body_epsilon_cap,
            "torso_epsilon_cap": self.torso_epsilon_cap,
            "major_clothing_epsilon_cap": self.major_clothing_epsilon_cap,
            "grouping": "composition-part-plus-rgb",
            "owner_local_palette_merge": "near-palette-before-profile-simplification",
            "micro_fragment_policy": "drop-only-after-part-level-coverage-gate",
            "hole_preservation": "contour-tree-even-odd",
            "generated_pixels": "forbidden-outside-rasterized-deterministic-geometry",
        }


@dataclass(frozen=True)
class SimplificationCandidate:
    name: str
    primitives: tuple[dict[str, Any], ...]
    primitive_masks: dict[str, np.ndarray]
    metrics: dict[str, Any]

    @property
    def passed(self) -> bool:
        return bool(self.metrics.get("pass"))


@dataclass(frozen=True)
class StyleSimplificationResult:
    width: int
    height: int
    baseline_primitives: tuple[dict[str, Any], ...]
    baseline_masks: dict[str, np.ndarray]
    candidates: tuple[SimplificationCandidate, ...]
    selected_name: str | None
    validation: dict[str, Any]
    policy: StyleSimplificationPolicy

    @property
    def selected(self) -> SimplificationCandidate | None:
        return next((item for item in self.candidates if item.name == self.selected_name), None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "coordinate_space": {
                "pixel_width": self.width,
                "pixel_height": self.height,
                "normalized_origin": "top-left",
                "normalized_range": [0.0, 1.0],
            },
            "policy": self.policy.to_dict(),
            "baseline": {
                "primitive_count": len(self.baseline_primitives),
                "primitives": list(self.baseline_primitives),
            },
            "candidates": [
                {
                    "name": item.name,
                    "metrics": item.metrics,
                    "primitives": list(item.primitives),
                }
                for item in self.candidates
            ],
            "selected_name": self.selected_name,
            "validation": self.validation,
        }


def _coordinate(payload: Mapping[str, Any]) -> tuple[int, int]:
    coordinate = payload.get("coordinate_space")
    if not isinstance(coordinate, Mapping):
        raise ValueError("Phase 12 requires Phase 11 coordinate_space")
    width = int(coordinate.get("pixel_width", 0))
    height = int(coordinate.get("pixel_height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("Phase 11 coordinate_space must be positive")
    return width, height


def _baseline(
    payload: Mapping[str, Any], width: int, height: int
) -> tuple[tuple[dict[str, Any], ...], dict[str, np.ndarray]]:
    raw = payload.get("primitives_back_to_front")
    if not isinstance(raw, list) or not raw:
        raise ValueError("Phase 12 requires Phase 11 primitives")
    records: list[dict[str, Any]] = []
    masks: dict[str, np.ndarray] = {}
    for item in raw:
        if not isinstance(item, Mapping):
            raise ValueError("Phase 11 primitive must be an object")
        record = dict(item)
        primitive_id = str(record.get("primitive_id") or "")
        if not primitive_id or primitive_id in masks:
            raise ValueError("Phase 11 primitive IDs must be unique")
        mask = rasterize_primitive_candidate(record, width=width, height=height)
        if not np.any(mask):
            raise ValueError(f"Phase 11 primitive rasterized empty: {primitive_id}")
        records.append(record)
        masks[primitive_id] = mask
    return tuple(records), masks


def _union(masks: list[np.ndarray], shape: tuple[int, int]) -> np.ndarray:
    out = np.zeros(shape, dtype=bool)
    for mask in masks:
        out |= mask
    return out


def _iou(first: np.ndarray, second: np.ndarray) -> float:
    union = np.count_nonzero(first | second)
    return 1.0 if union == 0 else float(np.count_nonzero(first & second) / union)


def _recall(reference: np.ndarray, candidate: np.ndarray) -> float:
    total = np.count_nonzero(reference)
    return 1.0 if total == 0 else float(np.count_nonzero(reference & candidate) / total)


def _vertex_count(record: Mapping[str, Any]) -> int:
    params = record.get("parameters") or {}
    family = record.get("primitive_type")
    if family in {"polygon", "rounded_polygon"}:
        return sum(len(component) for component in params.get("components") or [])
    if family in {"oriented_rectangle", "tapered_strip"}:
        return len(params.get("points") or [])
    if family == "polyline_ribbon":
        return len(params.get("outline") or [])
    if family in {"ellipse", "capsule"}:
        return 4
    return 0


def _group_baseline(
    primitives: tuple[dict[str, Any], ...],
    masks: dict[str, np.ndarray],
    shape: tuple[int, int],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, tuple[int, int, int]], dict[str, Any]] = {}
    for order, item in enumerate(primitives):
        part = str(item.get("composition_part") or UNBOUND_PART)
        color = tuple(int(value) for value in item.get("palette_color_rgb") or (0, 0, 0))
        key = (part, color)
        group = grouped.setdefault(
            key,
            {
                "part": part,
                "color": color,
                "mask": np.zeros(shape, dtype=bool),
                "source_ids": [],
                "source_actions": set(),
                "first_order": order,
            },
        )
        group["mask"] |= masks[str(item["primitive_id"])]
        group["source_ids"].append(str(item["primitive_id"]))
        group["source_actions"].add(str(item.get("phase8_action") or ""))
        group["first_order"] = min(int(group["first_order"]), order)
    return sorted(grouped.values(), key=lambda item: int(item["first_order"]))


def _merge_owner_local_near_palette_groups(
    groups: list[dict[str, Any]],
    policy: StyleSimplificationPolicy,
) -> list[dict[str, Any]]:
    thresholds = {
        "major_clothing": int(policy.major_clothing_palette_merge_delta),
        "accessory_or_held_object": int(policy.accessory_palette_merge_delta),
        UNBOUND_PART: int(policy.unbound_palette_merge_delta),
        # Both arms use the same owner-local palette merge policy. Keeping the
        # left arm out made tiny/foreshortened left arms fragment into many
        # micro-planes before simplification.
        "left_arm": int(policy.right_arm_palette_merge_delta),
        "right_arm": int(policy.right_arm_palette_merge_delta),
    }
    passthrough: list[dict[str, Any]] = []
    clusters: list[dict[str, Any]] = []
    for group in groups:
        part = str(group["part"])
        threshold = thresholds.get(part)
        if threshold is None:
            passthrough.append(group)
            continue
        color = np.asarray(group["color"], dtype=np.int16)
        matched: dict[str, Any] | None = None
        for cluster in clusters:
            if cluster["part"] != part:
                continue
            cluster_color = np.asarray(cluster["color"], dtype=np.int16)
            if int(np.max(np.abs(color - cluster_color))) <= threshold:
                matched = cluster
                break
        if matched is None:
            clone = dict(group)
            clone["source_ids"] = list(group["source_ids"])
            clone["source_actions"] = set(group["source_actions"])
            clone["dominant_pixels"] = int(np.count_nonzero(group["mask"]))
            clusters.append(clone)
            continue
        matched["mask"] |= group["mask"]
        matched["source_ids"].extend(group["source_ids"])
        matched["source_actions"].update(group["source_actions"])
        matched["first_order"] = min(
            int(matched["first_order"]), int(group["first_order"])
        )
        pixels = int(np.count_nonzero(group["mask"]))
        if pixels > int(matched["dominant_pixels"]):
            matched["color"] = group["color"]
            matched["dominant_pixels"] = pixels
    for cluster in clusters:
        cluster.pop("dominant_pixels", None)
    return sorted(
        [*passthrough, *clusters], key=lambda item: int(item["first_order"])
    )


def _drop_neutral_unbound_micro_groups(
    groups: list[dict[str, Any]],
    shape: tuple[int, int],
    policy: StyleSimplificationPolicy,
) -> list[dict[str, Any]]:
    height, width = shape
    max_area = max(
        1,
        int(round(width * height * policy.unbound_neutral_micro_max_area_ratio)),
    )
    output: list[dict[str, Any]] = []
    for group in groups:
        if group["part"] != UNBOUND_PART:
            output.append(group)
            continue
        area = int(np.count_nonzero(group["mask"]))
        color = np.asarray(group["color"], dtype=np.int16)
        channel_range = int(color.max() - color.min())
        if (
            area <= max_area
            and channel_range <= policy.unbound_neutral_micro_max_channel_range
        ):
            continue
        output.append(group)
    return sorted(output, key=lambda item: int(item["first_order"]))


def _hair_local_contrast_plane(
    base_mask: np.ndarray,
    excluded: np.ndarray,
    gray: np.ndarray,
    rgb: np.ndarray,
    alpha: np.ndarray,
    shape: tuple[int, int],
    policy: StyleSimplificationPolicy,
) -> tuple[np.ndarray, tuple[int, int, int] | None]:
    source = base_mask & alpha
    sample = gray[source]
    if sample.size < 32:
        return np.zeros(shape, dtype=bool), None
    threshold, _ = cv2.threshold(
        sample.reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    bright = source & (gray > int(threshold)) & ~excluded
    bright = cv2.morphologyEx(
        bright.astype(np.uint8),
        cv2.MORPH_CLOSE,
        np.ones((3, 3), np.uint8),
    )

    base_pixels = max(1, int(np.count_nonzero(base_mask)))
    minimum_area = max(
        20,
        int(round(base_pixels * policy.hair_local_contrast_min_area_ratio)),
    )
    maximum_area = max(
        minimum_area,
        int(round(base_pixels * policy.hair_local_contrast_max_area_ratio)),
    )
    ring_radius = max(3, int(round(min(shape) * 0.01)))
    ring_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (ring_radius * 2 + 1, ring_radius * 2 + 1),
    )

    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        bright, connectivity=8
    )
    kept = np.zeros(shape, dtype=bool)
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < minimum_area or area > maximum_area:
            continue
        component = labels == label
        ring = (
            cv2.dilate(component.astype(np.uint8), ring_kernel).astype(bool)
            & base_mask
            & alpha
            & ~component
            & ~excluded
        )
        if int(np.count_nonzero(ring)) < 8:
            continue
        local_delta = float(np.median(gray[component])) - float(
            np.median(gray[ring])
        )
        if local_delta < policy.hair_local_contrast_min_delta:
            continue
        points_yx = np.column_stack(np.where(component)).astype(np.float32)
        if len(points_yx) < 3:
            continue
        covariance = np.cov(points_yx.T)
        eigenvalues = np.linalg.eigvalsh(covariance)
        elongation = float(
            np.sqrt(
                max(float(eigenvalues[-1]), 1e-6)
                / max(float(eigenvalues[0]), 1e-6)
            )
        )
        if elongation < policy.hair_local_contrast_min_elongation:
            continue
        kept |= component

    color_source = kept & alpha
    if not np.any(color_source):
        return kept, None
    luminance = gray[color_source]
    color_threshold = float(
        np.quantile(luminance, policy.hair_local_contrast_color_quantile)
    )
    color_support = color_source & (gray >= color_threshold)
    if not np.any(color_support):
        color_support = color_source
    median = np.median(rgb[color_support], axis=0)
    color = tuple(int(round(value)) for value in median)
    return kept, color


def _hair_crown_light_plane(
    base_mask: np.ndarray,
    excluded: np.ndarray,
    face_bbox: tuple[int, int, int, int] | None,
    gray: np.ndarray,
    rgb: np.ndarray,
    alpha: np.ndarray,
    shape: tuple[int, int],
    policy: StyleSimplificationPolicy,
) -> tuple[np.ndarray, tuple[int, int, int] | None]:
    if face_bbox is None:
        return np.zeros(shape, dtype=bool), None
    source = base_mask & alpha
    sample = gray[source]
    if sample.size < 32:
        return np.zeros(shape, dtype=bool), None
    threshold, _ = cv2.threshold(
        sample.reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    fx0, fy0, fx1, fy1 = face_bbox
    fw = max(fx1 - fx0, 1)
    fh = max(fy1 - fy0, 1)
    yy, xx = np.indices(shape)
    corridor = (
        (xx >= fx0 - int(round(fw * 0.22)))
        & (xx <= fx1 + int(round(fw * 0.22)))
        & (yy >= fy0 - int(round(fh * 0.70)))
        & (yy <= fy0 + int(round(fh * 0.35)))
    )
    bright = (
        source
        & corridor
        & ~excluded
        & (gray > int(threshold))
    )
    bright = cv2.morphologyEx(
        bright.astype(np.uint8),
        cv2.MORPH_OPEN,
        np.ones((3, 3), np.uint8),
    )

    base_pixels = max(1, int(np.count_nonzero(base_mask)))
    minimum_area = max(
        20,
        int(round(base_pixels * policy.hair_crown_min_area_ratio)),
    )
    maximum_area = max(
        minimum_area,
        int(round(base_pixels * policy.hair_crown_max_area_ratio)),
    )
    ring_radius = max(3, int(round(min(shape) * 0.008)))
    ring_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (ring_radius * 2 + 1, ring_radius * 2 + 1),
    )
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        bright, connectivity=8
    )
    kept = np.zeros(shape, dtype=bool)
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < minimum_area or area > maximum_area:
            continue
        component = labels == label
        ring = (
            cv2.dilate(component.astype(np.uint8), ring_kernel).astype(bool)
            & base_mask
            & alpha
            & ~component
            & ~excluded
        )
        if int(np.count_nonzero(ring)) < 8:
            continue
        local_delta = float(np.median(gray[component])) - float(
            np.median(gray[ring])
        )
        if local_delta < policy.hair_crown_min_delta:
            continue
        kept |= component

    color_source = kept & alpha
    if not np.any(color_source):
        return kept, None
    luminance = gray[color_source]
    color_threshold = float(
        np.quantile(luminance, policy.hair_crown_color_quantile)
    )
    color_support = color_source & (gray >= color_threshold)
    if not np.any(color_support):
        color_support = color_source
    median = np.median(rgb[color_support], axis=0)
    color = tuple(int(round(value)) for value in median)
    return kept, color


def _source_guided_hair_groups(
    groups: list[dict[str, Any]],
    source_rgba: np.ndarray | None,
    shape: tuple[int, int],
    policy: StyleSimplificationPolicy,
) -> list[dict[str, Any]]:
    if not policy.source_guided_hair or source_rgba is None:
        return groups
    height, width = shape
    if source_rgba.shape[:2] != shape or source_rgba.ndim != 3:
        raise ValueError("Phase 12 source evidence must match composition dimensions")
    if source_rgba.shape[2] not in {3, 4}:
        raise ValueError("Phase 12 source evidence must be RGB or RGBA")
    rgb = source_rgba[:, :, :3].astype(np.uint8)
    alpha = (
        source_rgba[:, :, 3] > 0
        if source_rgba.shape[2] == 4
        else np.ones(shape, dtype=bool)
    )
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    source_min_area = max(
        32,
        int(round(width * height * policy.hair_highlight_source_min_area_ratio)),
    )
    component_min_area = max(
        8,
        int(round(width * height * policy.hair_highlight_component_area_ratio)),
    )
    close_size = max(3, int(round(min(width, height) * 0.01)))
    if close_size % 2 == 0:
        close_size += 1
    face_mask = np.zeros(shape, dtype=bool)
    for candidate in groups:
        if candidate["part"] == "face":
            face_mask |= candidate["mask"].astype(bool)
    face_ys, face_xs = np.where(face_mask)
    face_bbox = None
    if face_xs.size:
        face_bbox = (
            int(face_xs.min()),
            int(face_ys.min()),
            int(face_xs.max()) + 1,
            int(face_ys.max()) + 1,
        )
    output: list[dict[str, Any]] = []
    for group in groups:
        if group["part"] != "hair":
            output.append(group)
            continue
        base_mask = group["mask"].astype(bool)
        if int(np.count_nonzero(base_mask)) < source_min_area:
            output.append(group)
            continue
        base_color = np.asarray(group["color"], dtype=np.uint8).reshape(1, 1, 3)
        base_saturation = int(
            cv2.cvtColor(base_color, cv2.COLOR_RGB2HSV)[0, 0, 1]
        )
        if base_saturation > policy.hair_highlight_max_base_saturation:
            output.append(group)
            continue
        sample = gray[base_mask & alpha]
        if sample.size < source_min_area:
            output.append(group)
            continue
        q10, q90 = np.quantile(sample, [0.10, 0.90])
        if float(q90 - q10) < policy.hair_highlight_min_luminance_span:
            output.append(group)
            continue
        threshold, _ = cv2.threshold(
            sample.reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        bright = base_mask & alpha & (gray > int(threshold))
        bright = cv2.morphologyEx(
            bright.astype(np.uint8),
            cv2.MORPH_CLOSE,
            np.ones((close_size, close_size), np.uint8),
        )
        bright = cv2.morphologyEx(
            bright, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)
        )

        side_planes: list[tuple[str, np.ndarray, np.ndarray]] = []
        if face_bbox is not None:
            fx0, fy0, fx1, fy1 = face_bbox
            fw = max(fx1 - fx0, 1)
            fh = max(fy1 - fy0, 1)
            yy, xx = np.indices(shape)
            side_close_height = max(5, int(round(fh * 0.26)))
            if side_close_height % 2 == 0:
                side_close_height += 1
            side_corridors = (
                (
                    "left",
                    (xx >= fx0 - int(round(fw * 0.85)))
                    & (xx <= fx0 + int(round(fw * 0.18)))
                    & (yy >= fy0)
                    & (yy <= fy1 + int(round(fh * 1.65))),
                ),
                (
                    "right",
                    (xx >= fx1 - int(round(fw * 0.18)))
                    & (xx <= fx1 + int(round(fw * 0.85)))
                    & (yy >= fy0)
                    & (yy <= fy1 + int(round(fh * 1.65))),
                ),
            )
            for side_name, corridor in side_corridors:
                side_support = (bright > 0) & corridor
                side_connected = cv2.morphologyEx(
                    side_support.astype(np.uint8),
                    cv2.MORPH_CLOSE,
                    cv2.getStructuringElement(
                        cv2.MORPH_ELLIPSE, (3, side_close_height)
                    ),
                )
                side_connected = cv2.morphologyEx(
                    side_connected,
                    cv2.MORPH_OPEN,
                    np.ones((3, 3), np.uint8),
                )
                side_count, side_labels, side_stats, _ = cv2.connectedComponentsWithStats(
                    side_connected, connectivity=8
                )
                side_eligible = [
                    label
                    for label in range(1, side_count)
                    if int(side_stats[label, cv2.CC_STAT_AREA])
                    >= component_min_area
                ]
                if not side_eligible:
                    continue
                best = max(
                    side_eligible,
                    key=lambda label: int(
                        side_stats[label, cv2.CC_STAT_AREA]
                    ),
                )
                component = side_labels == best
                points_yx = np.column_stack(np.where(component))
                if len(points_yx) < 3:
                    continue
                hull = cv2.convexHull(points_yx[:, ::-1].astype(np.int32))
                hull_mask = np.zeros(shape, dtype=np.uint8)
                cv2.fillPoly(hull_mask, [hull], 1)
                plane = (hull_mask > 0) & base_mask & corridor
                support_pixels = int(side_stats[best, cv2.CC_STAT_AREA])
                plane_pixels = int(np.count_nonzero(plane))
                plane_source = plane & alpha
                plane_luminance = gray[plane_source]
                minimum_plane_luminance = float(
                    np.quantile(
                        sample,
                        policy.hair_highlight_min_plane_luminance_quantile,
                    )
                )
                plane_is_bright = (
                    plane_luminance.size > 0
                    and float(np.median(plane_luminance))
                    >= minimum_plane_luminance
                )
                if (
                    plane_is_bright
                    and support_pixels <= plane_pixels
                    <= int(
                        round(
                            support_pixels
                            * policy.hair_highlight_hull_expansion_limit
                        )
                    )
                ):
                    side_planes.append((side_name, plane, component))

        if side_planes:
            side_highlight = np.zeros(shape, dtype=bool)
            for _side_name, plane, _component in side_planes:
                side_highlight |= plane
            if int(np.count_nonzero(side_highlight)) >= source_min_area:
                local_contrast, local_color = _hair_local_contrast_plane(
                    base_mask,
                    side_highlight,
                    gray,
                    rgb,
                    alpha,
                    shape,
                    policy,
                )
                crown_light, crown_color = _hair_crown_light_plane(
                    base_mask,
                    side_highlight | local_contrast,
                    face_bbox,
                    gray,
                    rgb,
                    alpha,
                    shape,
                    policy,
                )
                dark = dict(group)
                dark["mask"] = (
                    base_mask
                    & ~side_highlight
                    & ~crown_light
                )
                dark["source_guided_kind"] = "hair-dark-plane"
                if np.any(dark["mask"]):
                    output.append(dark)
                for side_name, plane, component in side_planes:
                    light = dict(group)
                    light["mask"] = plane
                    support_luminance = gray[component]
                    color_threshold = float(
                        np.quantile(
                            support_luminance,
                            policy.hair_highlight_color_quantile,
                        )
                    )
                    color_support = component & (gray >= color_threshold)
                    if not np.any(color_support):
                        color_support = component
                    median = np.median(rgb[color_support], axis=0)
                    light["color"] = tuple(
                        int(round(value)) for value in median
                    )
                    light["source_guided_kind"] = (
                        f"hair-light-{side_name}-plane"
                    )
                    output.append(light)
                if local_color is not None and np.any(local_contrast):
                    local = dict(group)
                    local["mask"] = local_contrast
                    local["color"] = local_color
                    local["source_guided_kind"] = "hair-local-contrast-plane"
                    output.append(local)
                if crown_color is not None and np.any(crown_light):
                    crown = dict(group)
                    crown["mask"] = crown_light
                    crown["color"] = crown_color
                    crown["source_guided_kind"] = "hair-crown-light-plane"
                    output.append(crown)
                continue

        count, labels, stats, _ = cv2.connectedComponentsWithStats(
            bright, connectivity=8
        )
        eligible = [
            label
            for label in range(1, count)
            if int(stats[label, cv2.CC_STAT_AREA]) >= component_min_area
        ]
        eligible.sort(
            key=lambda label: int(stats[label, cv2.CC_STAT_AREA]), reverse=True
        )
        highlight = np.zeros(shape, dtype=bool)
        support = np.zeros(shape, dtype=bool)
        for label in eligible[: policy.hair_highlight_max_components]:
            component = labels == label
            points_yx = np.column_stack(np.where(component))
            if len(points_yx) < 3:
                continue
            hull = cv2.convexHull(points_yx[:, ::-1].astype(np.int32))
            hull_mask = np.zeros(shape, dtype=np.uint8)
            cv2.fillPoly(hull_mask, [hull], 1)
            plane = (hull_mask > 0) & base_mask
            support_pixels = int(stats[label, cv2.CC_STAT_AREA])
            plane_pixels = int(np.count_nonzero(plane))
            if (
                support_pixels <= plane_pixels
                <= int(round(support_pixels * policy.hair_highlight_hull_expansion_limit))
            ):
                highlight |= plane
                support |= component
        if not np.any(highlight) or not np.any(support):
            output.append(group)
            continue
        dark = dict(group)
        dark["mask"] = base_mask & ~highlight
        dark["source_guided_kind"] = "hair-dark-plane"
        if np.any(dark["mask"]):
            output.append(dark)
        light = dict(group)
        light["mask"] = highlight
        support_luminance = gray[support]
        color_threshold = float(
            np.quantile(support_luminance, policy.hair_highlight_color_quantile)
        )
        color_support = support & (gray >= color_threshold)
        if not np.any(color_support):
            color_support = support
        median = np.median(rgb[color_support], axis=0)
        light["color"] = tuple(int(round(value)) for value in median)
        light["source_guided_kind"] = "hair-light-plane"
        output.append(light)
    return sorted(output, key=lambda item: int(item["first_order"]))


def _merge_source_guided_hair_light_groups(
    groups: list[dict[str, Any]],
    policy: StyleSimplificationPolicy,
) -> list[dict[str, Any]]:
    merge_kinds = {
        "hair-light-left-plane",
        "hair-light-right-plane",
        "hair-crown-light-plane",
    }
    passthrough: list[dict[str, Any]] = []
    clusters: list[dict[str, Any]] = []
    threshold = int(policy.hair_light_palette_merge_delta)

    for group in groups:
        kind = str(group.get("source_guided_kind") or "")
        if group["part"] != "hair" or kind not in merge_kinds:
            passthrough.append(group)
            continue
        color = np.asarray(group["color"], dtype=np.int32)
        pixels = max(1, int(np.count_nonzero(group["mask"])))
        matched: dict[str, Any] | None = None
        for cluster in clusters:
            cluster_color = np.asarray(cluster["color"], dtype=np.int32)
            if int(np.max(np.abs(color - cluster_color))) <= threshold:
                matched = cluster
                break
        if matched is None:
            clone = dict(group)
            clone["source_ids"] = list(group["source_ids"])
            clone["source_actions"] = set(group["source_actions"])
            clone["_merge_count"] = 1
            clone["_weighted_pixels"] = pixels
            clone["_weighted_color_sum"] = color.astype(np.float64) * pixels
            clusters.append(clone)
            continue
        matched["mask"] |= group["mask"]
        matched["source_ids"].extend(group["source_ids"])
        matched["source_actions"].update(group["source_actions"])
        matched["first_order"] = min(
            int(matched["first_order"]), int(group["first_order"])
        )
        matched["_merge_count"] += 1
        matched["_weighted_pixels"] += pixels
        matched["_weighted_color_sum"] += color.astype(np.float64) * pixels

    for cluster in clusters:
        if int(cluster["_merge_count"]) > 1:
            weighted = cluster["_weighted_color_sum"] / max(
                int(cluster["_weighted_pixels"]), 1
            )
            cluster["color"] = tuple(
                int(round(float(value))) for value in weighted
            )
            cluster["source_guided_kind"] = "hair-light-merged-plane"
        cluster.pop("_merge_count", None)
        cluster.pop("_weighted_pixels", None)
        cluster.pop("_weighted_color_sum", None)

    return sorted(
        [*passthrough, *clusters],
        key=lambda item: int(item["first_order"]),
    )


def _source_guided_face_groups(
    groups: list[dict[str, Any]],
    source_rgba: np.ndarray | None,
    shape: tuple[int, int],
    policy: StyleSimplificationPolicy,
) -> list[dict[str, Any]]:
    if not policy.source_guided_face or source_rgba is None:
        return groups
    if source_rgba.shape[:2] != shape or source_rgba.ndim != 3:
        raise ValueError("Phase 12 source evidence must match composition dimensions")
    if source_rgba.shape[2] not in {3, 4}:
        raise ValueError("Phase 12 source evidence must be RGB or RGBA")
    rgb = source_rgba[:, :, :3].astype(np.uint8)
    alpha = (
        source_rgba[:, :, 3] > 0
        if source_rgba.shape[2] == 4
        else np.ones(shape, dtype=bool)
    )
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    kernel_size = max(3, int(round(min(shape) * 0.014)))
    if kernel_size % 2 == 0:
        kernel_size += 1
    output: list[dict[str, Any]] = []
    for group in groups:
        if group["part"] != "face":
            output.append(group)
            continue
        base_mask = group["mask"].astype(bool)
        sample = gray[base_mask & alpha]
        if sample.size < 32:
            output.append(group)
            continue
        threshold, _ = cv2.threshold(
            sample.reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        support = base_mask & alpha & (gray > int(threshold))
        support = cv2.morphologyEx(
            support.astype(np.uint8),
            cv2.MORPH_CLOSE,
            np.ones((kernel_size, kernel_size), np.uint8),
        )
        support = cv2.morphologyEx(
            support, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)
        )
        count, labels, stats, _ = cv2.connectedComponentsWithStats(
            support, connectivity=8
        )
        if count <= 1:
            output.append(group)
            continue
        best = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        points_yx = np.column_stack(np.where(labels == best))
        if len(points_yx) < 3:
            output.append(group)
            continue
        hull = cv2.convexHull(points_yx[:, ::-1].astype(np.int32))
        hull_mask = np.zeros(shape, dtype=np.uint8)
        cv2.fillPoly(hull_mask, [hull], 1)
        candidate = (hull_mask > 0) & base_mask
        base_pixels = max(1, int(np.count_nonzero(base_mask)))
        minimum_pixels = int(round(base_pixels * policy.face_min_retained_area_ratio))
        dilation = np.ones((3, 3), np.uint8)
        for _ in range(3):
            if int(np.count_nonzero(candidate)) >= minimum_pixels:
                break
            candidate = (
                cv2.dilate(candidate.astype(np.uint8), dilation, iterations=1) > 0
            ) & base_mask
        if int(np.count_nonzero(candidate)) < minimum_pixels:
            output.append(group)
            continue
        clone = dict(group)
        clone["mask"] = candidate
        color_support = (
            (labels == best)
            & base_mask
            & alpha
            & (gray > int(threshold))
        )
        if not np.any(color_support):
            color_support = labels == best
        median = np.median(rgb[color_support], axis=0)
        clone["color"] = tuple(int(round(value)) for value in median)
        clone["source_guided_kind"] = "face-light-plane"
        output.append(clone)
    return sorted(output, key=lambda item: int(item["first_order"]))


def _source_guided_wrist_skin_groups(
    groups: list[dict[str, Any]],
    source_rgba: np.ndarray | None,
    shape: tuple[int, int],
    policy: StyleSimplificationPolicy,
) -> list[dict[str, Any]]:
    if not policy.source_guided_wrist_skin or source_rgba is None:
        return groups
    if source_rgba.shape[:2] != shape or source_rgba.ndim != 3:
        raise ValueError("Phase 12 source evidence must match composition dimensions")
    if source_rgba.shape[2] not in {3, 4}:
        raise ValueError("Phase 12 source evidence must be RGB or RGBA")

    face_groups = [group for group in groups if group["part"] == "face"]
    if not face_groups:
        return groups
    face_group = max(
        face_groups,
        key=lambda group: int(np.count_nonzero(group["mask"])),
    )
    face_rgb = np.asarray(face_group["color"], dtype=np.uint8)
    face_lab = cv2.cvtColor(
        face_rgb.reshape(1, 1, 3), cv2.COLOR_RGB2LAB
    ).astype(np.float32)[0, 0]

    rgb = source_rgba[:, :, :3].astype(np.uint8)
    alpha = (
        source_rgba[:, :, 3] > 0
        if source_rgba.shape[2] == 4
        else np.ones(shape, dtype=bool)
    )
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)

    arm_union = np.zeros(shape, dtype=bool)
    wrist = np.zeros(shape, dtype=bool)
    contributing_parts: set[str] = set()
    for part in ("left_arm", "right_arm"):
        part_groups = [group for group in groups if group["part"] == part]
        if not part_groups:
            continue
        owner = np.zeros(shape, dtype=bool)
        for group in part_groups:
            owner |= group["mask"].astype(bool)
        arm_union |= owner
        owner_source = owner & alpha
        sample = gray[owner_source]
        owner_pixels = int(np.count_nonzero(owner))
        if sample.size < 24 or owner_pixels < 24:
            continue
        threshold, _ = cv2.threshold(
            sample.reshape(-1, 1),
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )
        bright = owner_source & (gray > int(threshold))
        count, labels, stats, _ = cv2.connectedComponentsWithStats(
            bright.astype(np.uint8), connectivity=8
        )
        minimum_area = max(
            6,
            int(round(owner_pixels * policy.wrist_skin_min_arm_area_ratio)),
        )
        maximum_area = max(
            minimum_area,
            int(round(owner_pixels * policy.wrist_skin_max_arm_area_ratio)),
        )
        ring_radius = max(2, int(round(min(shape) * 0.008)))
        ring_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (ring_radius * 2 + 1, ring_radius * 2 + 1),
        )
        for label_id in range(1, count):
            area = int(stats[label_id, cv2.CC_STAT_AREA])
            if area < minimum_area or area > maximum_area:
                continue
            component = labels == label_id
            ring = (
                cv2.dilate(component.astype(np.uint8), ring_kernel).astype(bool)
                & owner_source
                & ~component
            )
            if int(np.count_nonzero(ring)) < 4:
                continue
            local_delta = float(np.median(gray[component])) - float(
                np.median(gray[ring])
            )
            if local_delta < policy.wrist_skin_min_local_delta:
                continue
            component_lab = np.median(lab[component], axis=0)
            face_distance = float(np.linalg.norm(component_lab - face_lab))
            if face_distance > policy.wrist_skin_max_face_lab_distance:
                continue
            wrist |= component
            contributing_parts.add(part)

    if not np.any(wrist):
        return groups

    arm_support_radius = max(3, int(round(min(shape) * 0.02)))
    arm_support = cv2.dilate(
        arm_union.astype(np.uint8),
        cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (arm_support_radius * 2 + 1, arm_support_radius * 2 + 1),
        ),
    ).astype(bool)
    max_existing_area = max(
        8,
        int(
            round(
                shape[0]
                * shape[1]
                * policy.wrist_skin_existing_unbound_max_area_ratio
            )
        ),
    )

    matched_unbound: list[dict[str, Any]] = []
    for group in groups:
        if group["part"] != UNBOUND_PART:
            continue
        mask = group["mask"].astype(bool)
        area = int(np.count_nonzero(mask))
        if area == 0 or area > max_existing_area:
            continue
        if not np.any(mask & arm_support):
            continue
        color = np.asarray(group["color"], dtype=np.uint8)
        color_lab = cv2.cvtColor(
            color.reshape(1, 1, 3), cv2.COLOR_RGB2LAB
        ).astype(np.float32)[0, 0]
        if (
            float(np.linalg.norm(color_lab - face_lab))
            > policy.wrist_skin_max_face_lab_distance
        ):
            continue
        matched_unbound.append(group)

    merged_mask = wrist.copy()
    for group in matched_unbound:
        merged_mask |= group["mask"].astype(bool)

    color_support = merged_mask & alpha
    if not np.any(color_support):
        return groups
    median = np.median(rgb[color_support], axis=0)
    merged_color = tuple(int(round(value)) for value in median)

    source_ids: list[str] = []
    source_actions: set[str] = set()
    for group in matched_unbound:
        source_ids.extend(group["source_ids"])
        source_actions.update(group["source_actions"])
    for group in groups:
        if group["part"] in contributing_parts:
            source_ids.extend(group["source_ids"])
            source_actions.update(group["source_actions"])

    matched_ids = {id(group) for group in matched_unbound}
    output = [group for group in groups if id(group) not in matched_ids]
    base = matched_unbound[0] if matched_unbound else next(
        group for group in groups if group["part"] in contributing_parts
    )
    overlay = dict(base)
    overlay["part"] = UNBOUND_PART
    overlay["mask"] = merged_mask
    overlay["color"] = merged_color
    overlay["source_ids"] = list(dict.fromkeys(source_ids))
    overlay["source_actions"] = set(source_actions)
    overlay["first_order"] = max(int(group["first_order"]) for group in groups) + 1
    overlay["source_guided_kind"] = "wrist-skin-overlay"
    output.append(overlay)
    return sorted(output, key=lambda item: int(item["first_order"]))


def _source_guided_torso_color_groups(
    groups: list[dict[str, Any]],
    source_rgba: np.ndarray | None,
    shape: tuple[int, int],
    policy: StyleSimplificationPolicy,
) -> list[dict[str, Any]]:
    if not policy.source_guided_torso_color or source_rgba is None:
        return groups
    if source_rgba.shape[:2] != shape or source_rgba.ndim != 3:
        raise ValueError("Phase 12 source evidence must match composition dimensions")
    if source_rgba.shape[2] not in {3, 4}:
        raise ValueError("Phase 12 source evidence must be RGB or RGBA")
    rgb = source_rgba[:, :, :3].astype(np.uint8)
    alpha = (
        source_rgba[:, :, 3] > 0
        if source_rgba.shape[2] == 4
        else np.ones(shape, dtype=bool)
    )
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    output: list[dict[str, Any]] = []
    for group in groups:
        if group["part"] != "torso":
            output.append(group)
            continue
        mask = group["mask"].astype(bool) & alpha
        sample = gray[mask]
        if sample.size < 32:
            output.append(group)
            continue
        median_luminance = float(np.median(sample))
        luminance_span = float(np.quantile(sample, 0.90) - np.quantile(sample, 0.10))
        if median_luminance > policy.torso_color_max_median_luminance:
            output.append(group)
            continue
        if luminance_span < policy.torso_color_min_luminance_span:
            output.append(group)
            continue
        threshold = float(np.quantile(sample, policy.torso_color_quantile))
        support = mask & (gray >= threshold)
        if not np.any(support):
            output.append(group)
            continue
        clone = dict(group)
        median = np.median(rgb[support], axis=0)
        clone["color"] = tuple(int(round(value)) for value in median)
        clone["source_guided_kind"] = "torso-source-midplane-color"
        output.append(clone)
    return sorted(output, key=lambda item: int(item["first_order"]))


def _source_guided_lower_body_groups(
    groups: list[dict[str, Any]],
    source_rgba: np.ndarray | None,
    shape: tuple[int, int],
    policy: StyleSimplificationPolicy,
) -> list[dict[str, Any]]:
    if not policy.source_guided_lower_body or source_rgba is None:
        return groups
    height, width = shape
    if source_rgba.shape[:2] != shape or source_rgba.ndim != 3:
        raise ValueError("Phase 12 source evidence must match composition dimensions")
    if source_rgba.shape[2] not in {3, 4}:
        raise ValueError("Phase 12 source evidence must be RGB or RGBA")
    rgb = source_rgba[:, :, :3].astype(np.uint8)
    alpha = (
        source_rgba[:, :, 3] > 0
        if source_rgba.shape[2] == 4
        else np.ones(shape, dtype=bool)
    )
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    y_gate = int(round(height * policy.lower_body_split_min_y_ratio))
    yy = np.arange(height, dtype=np.int32)[:, None]
    min_area = max(
        24,
        int(round(width * height * policy.lower_body_light_component_area_ratio)),
    )
    output: list[dict[str, Any]] = []
    for group in groups:
        if group["part"] != "lower_body":
            output.append(group)
            continue
        base_mask = group["mask"].astype(bool)
        sample = gray[base_mask & alpha]
        if sample.size < min_area:
            output.append(group)
            continue
        threshold, _ = cv2.threshold(
            sample.reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        light = base_mask & alpha & (yy >= y_gate) & (gray > int(threshold))
        light = cv2.morphologyEx(
            light.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)
        ).astype(bool)
        count, labels, stats, _ = cv2.connectedComponentsWithStats(
            light.astype(np.uint8), connectivity=8
        )
        kept = np.zeros(shape, dtype=bool)
        for label in range(1, count):
            if int(stats[label, cv2.CC_STAT_AREA]) >= min_area:
                kept |= labels == label

        panel_kept = np.zeros(shape, dtype=bool)
        panel_support = np.zeros(shape, dtype=bool)
        base_ys, base_xs = np.where(base_mask)
        if base_xs.size:
            x0, x1 = int(base_xs.min()), int(base_xs.max())
            y0, y1 = int(base_ys.min()), int(base_ys.max())
            bbox_w = max(1, x1 - x0 + 1)
            bbox_h = max(1, y1 - y0 + 1)
            center_x = float(base_xs.mean())
            panel_support = (
                base_mask
                & alpha
                & (gray > int(threshold))
                & (yy >= y0 + int(round(bbox_h * 0.04)))
                & (yy <= y0 + int(round(bbox_h * 0.42)))
                & (np.arange(width, dtype=np.int32)[None, :] >= x0 + int(round(bbox_w * 0.12)))
                & (np.arange(width, dtype=np.int32)[None, :] <= center_x + int(round(bbox_w * 0.08)))
            )
            close_size = max(3, int(round(min(width, height) * 0.03)))
            if close_size % 2 == 0:
                close_size += 1
            closed = cv2.morphologyEx(
                panel_support.astype(np.uint8),
                cv2.MORPH_CLOSE,
                np.ones((close_size, close_size), np.uint8),
            )
            p_count, p_labels, p_stats, _ = cv2.connectedComponentsWithStats(
                closed, connectivity=8
            )
            eligible = [
                label for label in range(1, p_count)
                if int(p_stats[label, cv2.CC_STAT_AREA]) >= min_area * 3
            ]
            if eligible:
                best = max(
                    eligible, key=lambda label: int(p_stats[label, cv2.CC_STAT_AREA])
                )
                support_component = (p_labels == best).astype(np.uint8)
                contours, _ = cv2.findContours(
                    support_component,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_NONE,
                )
                if contours:
                    contour = max(contours, key=cv2.contourArea)
                    perimeter = float(cv2.arcLength(contour, True))
                    epsilon = max(
                        0.5,
                        perimeter * policy.lower_body_panel_epsilon_ratio,
                    )
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    panel_mask = np.zeros(shape, dtype=np.uint8)
                    cv2.fillPoly(panel_mask, [approx], 1)
                    candidate_panel = (panel_mask > 0) & base_mask
                    support_pixels = int(p_stats[best, cv2.CC_STAT_AREA])
                    panel_pixels = int(np.count_nonzero(candidate_panel))
                    minimum_panel_pixels = int(
                        round(
                            support_pixels
                            * policy.lower_body_panel_min_retained_ratio
                        )
                    )
                    maximum_panel_pixels = int(
                        round(
                            support_pixels
                            * policy.lower_body_panel_max_expansion_ratio
                        )
                    )
                    if (
                        support_pixels >= min_area * 3
                        and minimum_panel_pixels
                        <= panel_pixels
                        <= maximum_panel_pixels
                    ):
                        panel_kept = candidate_panel
        foot_kept = np.zeros(shape, dtype=bool)
        foot_support_kept = np.zeros(shape, dtype=bool)
        foot_light_kept = np.zeros(shape, dtype=bool)
        if policy.source_guided_foot and base_xs.size:
            foot_start_y = y0 + int(
                round(bbox_h * policy.lower_body_foot_zone_start_ratio)
            )
            foot_support = (
                base_mask
                & alpha
                & (yy >= foot_start_y)
                & (gray < int(threshold))
            )
            foot_close_size = max(3, int(round(min(width, height) * 0.018)))
            if foot_close_size % 2 == 0:
                foot_close_size += 1
            foot_closed = cv2.morphologyEx(
                foot_support.astype(np.uint8),
                cv2.MORPH_CLOSE,
                np.ones((foot_close_size, foot_close_size), np.uint8),
            )
            foot_closed = cv2.morphologyEx(
                foot_closed,
                cv2.MORPH_OPEN,
                np.ones((3, 3), np.uint8),
            )
            f_count, f_labels, f_stats, _ = cv2.connectedComponentsWithStats(
                foot_closed, connectivity=8
            )
            foot_min_area = max(
                32,
                int(
                    round(
                        width
                        * height
                        * policy.lower_body_foot_component_area_ratio
                    )
                ),
            )
            foot_labels = [
                label
                for label in range(1, f_count)
                if int(f_stats[label, cv2.CC_STAT_AREA]) >= foot_min_area
            ]
            foot_labels.sort(
                key=lambda label: int(f_stats[label, cv2.CC_STAT_AREA]),
                reverse=True,
            )
            for label in foot_labels[:2]:
                support_component = f_labels == label
                points_yx = np.column_stack(np.where(support_component))
                if len(points_yx) < 3:
                    continue
                hull = cv2.convexHull(points_yx[:, ::-1].astype(np.int32))
                hull_mask = np.zeros(shape, dtype=np.uint8)
                cv2.fillPoly(hull_mask, [hull], 1)
                candidate_foot = (hull_mask > 0) & base_mask
                support_pixels = int(f_stats[label, cv2.CC_STAT_AREA])
                foot_pixels = int(np.count_nonzero(candidate_foot))
                minimum_foot_pixels = int(round(support_pixels * 0.95))
                if minimum_foot_pixels <= foot_pixels <= int(round(support_pixels * 2.0)):
                    foot_kept |= candidate_foot
                    foot_support_kept |= support_component
        if np.any(foot_kept):
            foot_source = foot_kept & alpha
            foot_sample = gray[foot_source]
            if foot_sample.size >= 24:
                foot_light_threshold, _ = cv2.threshold(
                    foot_sample.reshape(-1, 1),
                    0,
                    255,
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU,
                )
                foot_light = (
                    foot_source & (gray > int(foot_light_threshold))
                )
                foot_light = cv2.morphologyEx(
                    foot_light.astype(np.uint8),
                    cv2.MORPH_CLOSE,
                    np.ones((3, 3), np.uint8),
                )
                fl_count, fl_labels, fl_stats, _ = cv2.connectedComponentsWithStats(
                    foot_light, connectivity=8
                )
                foot_pixels_total = max(1, int(np.count_nonzero(foot_kept)))
                foot_light_min_area = max(
                    12,
                    int(
                        round(
                            foot_pixels_total
                            * policy.lower_body_foot_light_min_area_ratio
                        )
                    ),
                )
                foot_light_max_area = max(
                    foot_light_min_area,
                    int(
                        round(
                            foot_pixels_total
                            * policy.lower_body_foot_light_max_area_ratio
                        )
                    ),
                )
                foot_ring = cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE, (9, 9)
                )
                for label in range(1, fl_count):
                    area = int(fl_stats[label, cv2.CC_STAT_AREA])
                    if area < foot_light_min_area or area > foot_light_max_area:
                        continue
                    component = fl_labels == label
                    ring = (
                        cv2.dilate(component.astype(np.uint8), foot_ring).astype(bool)
                        & foot_kept
                        & alpha
                        & ~component
                    )
                    if int(np.count_nonzero(ring)) < 8:
                        continue
                    local_delta = float(np.median(gray[component])) - float(
                        np.median(gray[ring])
                    )
                    if local_delta < policy.lower_body_foot_light_min_delta:
                        continue
                    points_yx = np.column_stack(np.where(component)).astype(np.float32)
                    if len(points_yx) < 3:
                        continue
                    covariance = np.cov(points_yx.T)
                    eigenvalues = np.linalg.eigvalsh(covariance)
                    elongation = float(
                        np.sqrt(
                            max(float(eigenvalues[-1]), 1e-6)
                            / max(float(eigenvalues[0]), 1e-6)
                        )
                    )
                    if elongation < policy.lower_body_foot_light_min_elongation:
                        continue
                    foot_light_kept |= component
        if (
            not np.any(kept)
            and not np.any(panel_kept)
            and not np.any(foot_kept)
        ):
            output.append(group)
            continue
        dark = dict(group)
        dark_mask = base_mask & ~kept & ~foot_kept
        dark["mask"] = dark_mask
        dark_source = dark_mask & ~panel_kept & alpha
        if np.any(dark_source):
            median = np.median(rgb[dark_source], axis=0)
            dark["color"] = tuple(int(round(value)) for value in median)
        dark["source_guided_kind"] = "lower-body-dark-plane"
        output.append(dark)
        if np.any(panel_kept):
            panel_group = dict(group)
            panel_group["mask"] = panel_kept
            panel_luminance = gray[panel_support]
            panel_color_threshold = float(
                np.quantile(
                    panel_luminance,
                    policy.lower_body_panel_color_quantile,
                )
            )
            panel_color_support = panel_support & (
                gray >= panel_color_threshold
            )
            if not np.any(panel_color_support):
                panel_color_support = panel_support
            median = np.median(rgb[panel_color_support], axis=0)
            panel_group["color"] = tuple(int(round(value)) for value in median)
            panel_group["source_guided_kind"] = "lower-body-light-skirt-plane"
            panel_group["first_order"] = int(group["first_order"]) + 1
            output.append(panel_group)
        combine_leg_and_openings = bool(
            np.any(kept) and np.any(foot_light_kept)
        )
        if np.any(kept) and not combine_leg_and_openings:
            light_group = dict(group)
            light_group["mask"] = kept
            median = np.median(rgb[kept], axis=0)
            light_group["color"] = tuple(int(round(value)) for value in median)
            light_group["source_guided_kind"] = "lower-body-light-leg-plane"
            light_group["first_order"] = int(group["first_order"]) + 2
            output.append(light_group)
        if np.any(foot_kept):
            foot_group = dict(group)
            foot_group["mask"] = foot_kept
            median = np.median(rgb[foot_support_kept], axis=0)
            foot_group["color"] = tuple(int(round(value)) for value in median)
            foot_group["source_guided_kind"] = "lower-body-dark-foot-plane"
            foot_group["first_order"] = int(group["first_order"]) + 3
            if np.any(foot_group["mask"]):
                output.append(foot_group)
        if combine_leg_and_openings:
            combined_light = (kept & ~foot_kept) | foot_light_kept
            combined_group = dict(group)
            combined_group["mask"] = combined_light
            color_support = combined_light & alpha
            median = np.median(rgb[color_support], axis=0)
            combined_group["color"] = tuple(
                int(round(value)) for value in median
            )
            combined_group["source_guided_kind"] = (
                "lower-body-light-leg-and-foot-opening-plane"
            )
            combined_group["first_order"] = int(group["first_order"]) + 4
            output.append(combined_group)
        elif np.any(foot_light_kept):
            foot_light_group = dict(group)
            foot_light_group["mask"] = foot_light_kept
            median = np.median(rgb[foot_light_kept & alpha], axis=0)
            foot_light_group["color"] = tuple(
                int(round(value)) for value in median
            )
            foot_light_group["source_guided_kind"] = (
                "lower-body-light-foot-opening-plane"
            )
            foot_light_group["first_order"] = int(group["first_order"]) + 4
            output.append(foot_light_group)
    return sorted(output, key=lambda item: int(item["first_order"]))


def _simplify_component(
    mask: np.ndarray,
    epsilon_ratio: float,
    *,
    min_hole_area: float = 0.0,
) -> dict[str, Any] | None:
    contours, hierarchy = cv2.findContours(
        (mask.astype(np.uint8) * 255),
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_NONE,
    )
    if not contours or hierarchy is None:
        return None
    hierarchy = hierarchy[0]
    rings: list[dict[str, Any]] = []
    for index, contour in enumerate(contours):
        if len(contour) < 3:
            continue
        depth = 0
        parent = int(hierarchy[index][3])
        while parent >= 0:
            depth += 1
            parent = int(hierarchy[parent][3])
        if depth % 2 == 1 and float(cv2.contourArea(contour)) < min_hole_area:
            continue
        perimeter = float(cv2.arcLength(contour, True))
        epsilon = max(0.5, perimeter * epsilon_ratio)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if len(approx) < 3:
            approx = cv2.convexHull(contour)
        if len(approx) < 3:
            continue
        points = [
            [float(point[0][0]), float(point[0][1])]
            for point in approx
        ]
        rings.append(
            {
                "points": points,
                "depth": depth,
                "role": "fill" if depth % 2 == 0 else "hole",
                "source_contour_index": index,
            }
        )
    if not any(ring["role"] == "fill" for ring in rings):
        return None
    return {
        "components": [
            ring["points"] for ring in rings if ring["role"] == "fill"
        ],
        "holes": [
            ring["points"] for ring in rings if ring["role"] == "hole"
        ],
        "rings": rings,
        "hole_preservation": "contour-tree-even-odd",
    }


def _candidate_for_profile(
    *,
    profile: SimplificationProfile,
    groups: list[dict[str, Any]],
    baseline_part_masks: dict[str, np.ndarray],
    baseline_silhouette: np.ndarray,
    reference_basis: Mapping[str, str] | None = None,
    baseline_primitives: tuple[dict[str, Any], ...],
    width: int,
    height: int,
    policy: StyleSimplificationPolicy,
) -> SimplificationCandidate:
    min_area = max(2, int(round(width * height * profile.min_component_area_ratio)))
    kernel = np.ones((profile.merge_gap_px * 2 + 1, profile.merge_gap_px * 2 + 1), dtype=np.uint8)
    primitives: list[dict[str, Any]] = []
    masks: dict[str, np.ndarray] = {}
    removed_components = 0
    owner_counts: dict[str, int] = {}
    for item in baseline_primitives:
        owner = str(item.get("composition_part", UNBOUND_PART))
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
    for group_index, group in enumerate(groups):
        group_min_area = min_area
        # Critical semantic parts can legitimately be tiny (for example a
        # foreshortened arm). Do not let the generic micro-component floor erase
        # a large fraction of an already-small identity-bearing part.
        if group["part"] in policy.critical_parts:
            part_pixels = sum(
                int(np.count_nonzero(item["mask"]))
                for item in groups
                if item["part"] == group["part"]
            )
            if part_pixels <= max(256, policy.minimum_visible_part_pixels * 32):
                group_min_area = min(
                    group_min_area,
                    max(2, int(round(part_pixels * 0.02))),
                )
        if group["part"] == "accessory_or_held_object":
            accessory_min_area = max(
                8,
                int(
                    round(
                        width
                        * height
                        * policy.accessory_min_component_area_ratio
                    )
                ),
            )
            group_min_area = accessory_min_area
        source_guided_kind = str(group.get("source_guided_kind") or "")
        if source_guided_kind.startswith("structural-source-repair-"):
            group_min_area = 2
        if source_guided_kind in {
            "hair-crown-light-plane",
            "hair-light-merged-plane",
        }:
            crown_min_area = max(
                16,
                int(
                    round(
                        width
                        * height
                        * policy.hair_crown_output_area_ratio
                    )
                ),
            )
            group_min_area = min(group_min_area, crown_min_area)
        if source_guided_kind == "wrist-skin-overlay":
            wrist_min_area = max(
                8,
                int(
                    round(
                        width
                        * height
                        * policy.wrist_skin_output_area_ratio
                    )
                ),
            )
            group_min_area = min(group_min_area, wrist_min_area)
        if source_guided_kind in {
            "lower-body-light-foot-opening-plane",
            "lower-body-light-leg-and-foot-opening-plane",
        }:
            foot_light_min_area = max(
                16,
                int(
                    round(
                        width
                        * height
                        * policy.lower_body_foot_light_output_area_ratio
                    )
                ),
            )
            group_min_area = min(group_min_area, foot_light_min_area)
        raw_mask = group["mask"].astype(np.uint8)
        working = raw_mask
        preserve_clothing_plane = group["part"] == "major_clothing"
        preserve_accessory_plane = group["part"] == "accessory_or_held_object"
        preserve_tiny_critical_plane = (
            owner_counts.get(group["part"], 0) >= 32
            or (
                group["part"] in policy.critical_parts
                and part_pixels <= max(256, policy.minimum_visible_part_pixels * 32)
            )
            or (
                group["part"] in {"left_arm", "right_arm"}
                and len(group["source_ids"]) >= 12
            )
        )
        preserve_source_detail_plane = (
            source_guided_kind.startswith("hair-")
            or source_guided_kind == "wrist-skin-overlay"
            or source_guided_kind.startswith("structural-source-repair-")
            or source_guided_kind
            in {
                "lower-body-light-foot-opening-plane",
                "lower-body-light-leg-and-foot-opening-plane",
            }
        )
        if (
            profile.merge_gap_px > 0
            and not preserve_clothing_plane
            and not preserve_accessory_plane
            and not preserve_tiny_critical_plane
            and not preserve_source_detail_plane
        ):
            working = cv2.morphologyEx(raw_mask, cv2.MORPH_CLOSE, kernel)
        count, labels, stats, _ = cv2.connectedComponentsWithStats(working, connectivity=8)
        components: list[tuple[int, np.ndarray]] = []
        for label in range(1, count):
            area = int(stats[label, cv2.CC_STAT_AREA])
            component = labels == label
            if area < group_min_area:
                removed_components += 1
                continue
            components.append((area, component))
        if not components:
            continue
        polygon_components: list[list[list[float]]] = []
        polygon_holes: list[list[list[float]]] = []
        polygon_rings: list[dict[str, Any]] = []
        for _, component in sorted(components, key=lambda item: -item[0]):
            epsilon_ratio = profile.epsilon_ratio
            if preserve_tiny_critical_plane:
                epsilon_ratio = min(epsilon_ratio, 0.0005)
            if source_guided_kind.startswith("structural-source-repair-"):
                epsilon_ratio = 0.0
            elif source_guided_kind == "hair-crown-light-plane":
                epsilon_ratio = policy.hair_crown_epsilon_ratio
            elif source_guided_kind == "hair-local-contrast-plane":
                epsilon_ratio = policy.hair_local_contrast_epsilon_ratio
            elif source_guided_kind == "wrist-skin-overlay":
                epsilon_ratio = policy.wrist_skin_epsilon_ratio
            elif source_guided_kind == "lower-body-light-foot-opening-plane":
                epsilon_ratio = policy.lower_body_foot_light_epsilon_ratio
            elif source_guided_kind == "lower-body-light-leg-and-foot-opening-plane":
                epsilon_ratio = policy.lower_body_leg_foot_epsilon_ratio
            elif source_guided_kind == "lower-body-dark-foot-plane":
                epsilon_ratio = policy.lower_body_dark_foot_epsilon_ratio
            elif preserve_clothing_plane:
                epsilon_ratio = min(
                    epsilon_ratio, policy.major_clothing_epsilon_cap
                )
            elif group["part"] == "hair":
                epsilon_ratio = min(epsilon_ratio, policy.hair_epsilon_cap)
            elif group["part"] == "face":
                epsilon_ratio = min(epsilon_ratio, policy.face_epsilon_cap)
            elif group["part"] == "accessory_or_held_object":
                epsilon_ratio = min(epsilon_ratio, policy.accessory_epsilon_cap)
            elif group["part"] in {"left_arm", "right_arm"}:
                epsilon_ratio = min(epsilon_ratio, policy.arm_epsilon_cap)
            elif group["part"] == "lower_body":
                epsilon_ratio = min(epsilon_ratio, policy.lower_body_epsilon_cap)
            elif group["part"] == "torso":
                epsilon_ratio = min(epsilon_ratio, policy.torso_epsilon_cap)
            min_hole_area = (
                width * height * policy.hair_min_hole_area_ratio
                if group["part"] == "hair"
                else 0.0
            )
            simplified = _simplify_component(
                component,
                0.0 if (preserve_tiny_critical_plane or preserve_accessory_plane) else epsilon_ratio,
                min_hole_area=min_hole_area,
            )
            if simplified is None:
                continue
            polygon_components.extend(simplified["components"])
            polygon_holes.extend(simplified["holes"])
            polygon_rings.extend(simplified["rings"])
        if not polygon_components:
            continue
        primitive_id = f"phase12-{profile.name}-{group_index:04d}"
        record = {
            "primitive_id": primitive_id,
            "primitive_type": "polygon",
            "parameters": {
                "components": polygon_components,
                "holes": polygon_holes,
                "rings": polygon_rings,
                "corner_radius_px": 0,
                "hole_preservation": "contour-tree-even-odd",
            },
            "composition_part": group["part"],
            "semantic_part_id": None if group["part"] == UNBOUND_PART else group["part"],
            "binding_status": "unbound" if group["part"] == UNBOUND_PART else "bound",
            "palette_color_rgb": list(group["color"]),
            "source_primitive_ids": list(group["source_ids"]),
            "source_phase8_actions": sorted(group["source_actions"]),
            "source_evidence_refs": list(group.get("source_evidence_refs", ())),
            "phase12_profile": profile.name,
            "raster_index": int(group["first_order"]),
        }
        if group.get("source_guided_kind"):
            record["source_guided_kind"] = str(group["source_guided_kind"])
        mask = rasterize_primitive_candidate(record, width=width, height=height)
        if preserve_tiny_critical_plane:
            exact_mask = group["mask"].astype(bool)
            exact_iou = _iou(exact_mask, mask)
            if exact_iou < 0.98 or len(group["source_ids"]) >= 12:
                # Fail closed to the observed Phase 11 geometry for tiny
                # identity-critical parts when polygon simplification itself
                # would erase too much of the part.
                source_records = [
                    item
                    for item in baseline_primitives
                    if str(item["primitive_id"]) in set(group["source_ids"])
                ]
                for source_record in source_records:
                    source_copy = dict(source_record)
                    source_copy["phase12_profile"] = profile.name
                    source_copy["raster_index"] = int(group["first_order"])
                    primitives.append(source_copy)
                    masks[str(source_copy["primitive_id"])] = rasterize_primitive_candidate(
                        source_copy, width=width, height=height
                    )
                continue
        if not np.any(mask):
            continue
        primitives.append(record)
        masks[primitive_id] = mask

    primitives.sort(key=lambda item: int(item["raster_index"]))
    shape = (height, width)
    candidate_silhouette = _union(list(masks.values()), shape)
    candidate_part_masks: dict[str, np.ndarray] = {}
    for item in primitives:
        part = str(item["composition_part"])
        candidate_part_masks.setdefault(part, np.zeros(shape, dtype=bool))
        candidate_part_masks[part] |= masks[str(item["primitive_id"])]

    part_metrics: dict[str, dict[str, Any]] = {}
    critical_failures: list[str] = []
    critical_iou_failures: list[str] = []
    missing_visible_parts: list[str] = []
    for part, reference in sorted(baseline_part_masks.items()):
        candidate = candidate_part_masks.get(part, np.zeros(shape, dtype=bool))
        recall = _recall(reference, candidate)
        part_iou = _iou(reference, candidate)
        pixels = int(np.count_nonzero(reference))
        part_metrics[part] = {
            "reference_basis": (reference_basis or {}).get(part, "phase11"),
            "baseline_pixels": pixels,
            "candidate_pixels": int(np.count_nonzero(candidate)),
            "recall": round(recall, 6),
            "iou": round(part_iou, 6),
        }
        visible_threshold = (
            policy.minimum_support_only_part_pixels
            if part in policy.support_only_parts
            else policy.minimum_visible_part_pixels
        )
        if pixels >= visible_threshold and not np.any(candidate):
            missing_visible_parts.append(part)
        if part in policy.critical_parts and pixels >= policy.minimum_visible_part_pixels:
            if recall < profile.minimum_critical_part_recall:
                critical_failures.append(part)
            if part_iou < profile.minimum_critical_part_iou:
                critical_iou_failures.append(part)

    silhouette_iou = _iou(baseline_silhouette, candidate_silhouette)
    baseline_vertices = sum(_vertex_count(item) for item in baseline_primitives)
    candidate_vertices = sum(_vertex_count(item) for item in primitives)
    passed = (
        silhouette_iou >= profile.minimum_silhouette_iou
        and not critical_failures
        and not critical_iou_failures
        and not missing_visible_parts
        and bool(primitives)
    )
    metrics = {
        "pass": passed,
        "profile": profile.name,
        "primitive_count": len(primitives),
        "baseline_primitive_count": len(baseline_primitives),
        "primitive_reduction": len(baseline_primitives) - len(primitives),
        "vertex_count": candidate_vertices,
        "baseline_vertex_count": baseline_vertices,
        "vertex_reduction": baseline_vertices - candidate_vertices,
        "silhouette_iou": round(silhouette_iou, 6),
        "critical_part_failures": critical_failures,
        "critical_part_iou_failures": critical_iou_failures,
        "missing_visible_parts": missing_visible_parts,
        "removed_micro_component_count": removed_components,
        "part_metrics": part_metrics,
    }
    return SimplificationCandidate(
        name=profile.name,
        primitives=tuple(primitives),
        primitive_masks=masks,
        metrics=metrics,
    )


def simplify_composed_scene(
    composition_payload: Mapping[str, Any],
    *,
    policy: StyleSimplificationPolicy | None = None,
    source_rgba: np.ndarray | None = None,
    source_part_masks: Mapping[str, np.ndarray] | None = None,
) -> StyleSimplificationResult:
    policy = policy or StyleSimplificationPolicy()
    if composition_payload.get("validation", {}).get("pass") is not True:
        raise ValueError("Phase 12 requires a passing Phase 11 composition")
    width, height = _coordinate(composition_payload)
    baseline_primitives, baseline_masks = _baseline(composition_payload, width, height)
    shape = (height, width)
    baseline_silhouette = _union(list(baseline_masks.values()), shape)
    baseline_part_masks: dict[str, np.ndarray] = {}
    for item in baseline_primitives:
        part = str(item.get("composition_part") or UNBOUND_PART)
        baseline_part_masks.setdefault(part, np.zeros(shape, dtype=bool))
        baseline_part_masks[part] |= baseline_masks[str(item["primitive_id"])]
    groups = _group_baseline(baseline_primitives, baseline_masks, shape)
    groups = _merge_owner_local_near_palette_groups(groups, policy)
    groups = _drop_neutral_unbound_micro_groups(groups, shape, policy)
    groups = _source_guided_hair_groups(groups, source_rgba, shape, policy)
    groups = _merge_source_guided_hair_light_groups(groups, policy)
    groups = _source_guided_face_groups(groups, source_rgba, shape, policy)
    groups = _source_guided_wrist_skin_groups(
        groups, source_rgba, shape, policy
    )
    groups = _source_guided_torso_color_groups(
        groups, source_rgba, shape, policy
    )
    groups = _source_guided_lower_body_groups(
        groups, source_rgba, shape, policy
    )
    repair_report = {
        "version": "sa10.11-v1",
        "applied": False,
        "repaired_parts": [],
        "reasons": {},
    }
    reference_part_masks = dict(baseline_part_masks)
    reference_basis = {part: "phase11" for part in baseline_part_masks}
    reference_silhouette = baseline_silhouette
    if (
        policy.structural_source_repair
        and source_rgba is not None
        and source_part_masks is not None
    ):
        groups, repair_report = apply_structural_source_repair(
            groups,
            source_rgba=source_rgba,
            source_part_masks=source_part_masks,
            shape=shape,
            minimum_bbox_area_ratio=policy.structural_minimum_bbox_area_ratio,
            maximum_bbox_area_ratio=policy.structural_maximum_bbox_area_ratio,
        )
        for part in repair_report.get("repaired_parts", ()):
            if part in source_part_masks:
                mask = np.asarray(source_part_masks[part]).astype(bool)
                if mask.shape != shape:
                    raise ValueError(f"Phase 12 structural source mask shape mismatch: {part}")
                reference_part_masks[part] = mask
                reference_basis[part] = "phase04-source-repair"
        reference_silhouette = _union(
            list(reference_part_masks.values()),
            shape,
        )
    candidates = tuple(
        _candidate_for_profile(
            profile=profile,
            groups=groups,
            baseline_part_masks=reference_part_masks,
            baseline_silhouette=reference_silhouette,
            reference_basis=reference_basis,
            baseline_primitives=baseline_primitives,
            width=width,
            height=height,
            policy=policy,
        )
        for profile in (policy.conservative, policy.aggressive)
    )
    passing = [item for item in candidates if item.passed]
    selected = (
        min(
            passing,
            key=lambda item: (
                int(item.metrics["primitive_count"]),
                -float(item.metrics["silhouette_iou"]),
                int(item.metrics["vertex_count"]),
            ),
        )
        if passing
        else None
    )
    validation = {
        "pass": selected is not None,
        "phase11_primitive_count": len(baseline_primitives),
        "candidate_count": len(candidates),
        "passing_candidate_count": len(passing),
        "selected_profile": selected.name if selected else None,
        "selected_primitive_count": len(selected.primitives) if selected else None,
        "generated_or_inpainted_pixel_count": 0,
        "semantic_owner_reinterpretation": False,
        "selection_rule": "fewest-primitives-then-highest-silhouette-then-fewest-vertices",
        "human_visual_gate_required": True,
        "structural_source_repair": repair_report,
    }
    return StyleSimplificationResult(
        width=width,
        height=height,
        baseline_primitives=baseline_primitives,
        baseline_masks=baseline_masks,
        candidates=candidates,
        selected_name=selected.name if selected else None,
        validation=validation,
        policy=policy,
    )
