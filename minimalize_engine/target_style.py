from __future__ import annotations

from colorsys import hsv_to_rgb, rgb_to_hsv
from dataclasses import replace
from math import cos, pi, sin

import cv2
import numpy as np

from .analysis.shape_cleanup import cleanup_minimal_shapes
from .config import MinimalizeConfig
from .models import Scene, Shape
from .macro_subject_guard import (
    MacroSubjectGuardResult,
    build_macro_subject_guard,
    phase15_subject_candidate,
)
from .face_plane_fallback import FacePlaneFallbackResult, build_face_plane_fallback
from .pipeline import minimalize
from .opaque_subject_rescue import OpaqueSubjectRescue, prepare_rinka_opaque_subject_input
from .subject_segmentation import SubjectSegmentation, segment_subject_without_ai
from .subject_planes import SubjectPlaneResult, build_subject_color_planes
from .target_hierarchy import (
    OpaqueSubjectHierarchy,
    OpaqueSubjectZones,
    dominant_shape_zone,
    estimate_opaque_subject_hierarchy,
    estimate_opaque_subject_zones,
    estimate_structure_subject_zones,
    shape_subject_overlap,
)


RINKA_REFERENCE_NAME = "rinka_reference"
RINKA_REFERENCE_VERSION = "phase16"
RINKA_REFERENCE_PRESETS = ("geometric_poster", "faceless_subject", "approved_reference")
DEFAULT_RINKA_REFERENCE_PRESET = "geometric_poster"


def normalize_rinka_reference_preset(preset: str) -> str:
    value = str(preset or "").strip().lower()
    if value not in RINKA_REFERENCE_PRESETS:
        allowed = ", ".join(RINKA_REFERENCE_PRESETS)
        raise ValueError(f"Unknown Rinka Reference preset: {preset!r}. Use one of: {allowed}.")
    return value


_TARGET_MAX_SHAPES = {
    1: 72,
    2: 56,
    3: 42,
    4: 28,
    5: 18,
}

_TARGET_PALETTE_COLORS = {
    1: 8,
    2: 7,
    3: 6,
    4: 6,
    5: 4,
}

_TARGET_EPSILON = {
    1: 0.012,
    2: 0.018,
    3: 0.026,
    4: 0.040,
    5: 0.060,
}

_CHARACTER_TOKENS = (
    "character",
    "hair",
    "head",
    "face",
    "hand",
    "finger",
    "arm",
    "leg",
    "limb",
    "shoe",
    "torso",
    "outfit",
    "dress",
    "skirt",
    "sleeve",
    "clothing",
    "prop",
)


def rinka_reference_config(level: int = 4, **overrides) -> MinimalizeConfig:
    """Return an opt-in config aimed at the formal Rinka Reference target.

    Stable ``from_level`` presets stay unchanged. The target profile deliberately
    spends fewer shapes and colors on local detail, disables structural lines,
    keeps dedicated face primitives off, and disables quality retry so a retry
    cannot re-introduce detail after the target-style simplification decisions.
    """
    base = MinimalizeConfig.from_level(level)
    profile = {
        "palette_colors": min(base.palette_colors, _TARGET_PALETTE_COLORS[level]),
        "target_max_shapes": min(base.target_max_shapes, _TARGET_MAX_SHAPES[level]),
        "contour_epsilon_ratio": max(base.contour_epsilon_ratio, _TARGET_EPSILON[level]),
        "line_mode": "none",
        "enable_face_primitives": False,
        "enable_rinka_macro_partition": True,
        "character_hand_max_shapes": 1,
        "cleanup_remove_duplicates": True,
        "cleanup_role_fragment_merge": True,
        "cleanup_thin_rectangle_short_side_ratio": max(
            base.cleanup_thin_rectangle_short_side_ratio, 0.018
        ),
        "cleanup_thin_rectangle_aspect_ratio": min(
            base.cleanup_thin_rectangle_aspect_ratio, 3.6
        ),
        "cleanup_thin_rectangle_max_area_ratio": max(
            base.cleanup_thin_rectangle_max_area_ratio, 0.010
        ),
        "cleanup_simplify_epsilon_ratio": max(
            base.cleanup_simplify_epsilon_ratio, 0.020
        ),
        "cleanup_simplify_max_area_error": max(
            base.cleanup_simplify_max_area_error, 0.070
        ),
        "cleanup_simplify_min_iou": min(base.cleanup_simplify_min_iou, 0.970),
        "enable_auto_retry": False,
        "enable_character_auto_retry": False,
    }
    profile.update(overrides)
    return base.with_overrides(**profile)


def _polygon_area(points: list[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    area = 0.0
    for i, (x0, y0) in enumerate(points):
        x1, y1 = points[(i + 1) % len(points)]
        area += x0 * y1 - x1 * y0
    return abs(area) * 0.5


def _shape_metrics(shape: Shape) -> tuple[float, float, float, float]:
    if shape.shape_type == "rectangle":
        w = max(float(shape.width or 0.0), 0.0)
        h = max(float(shape.height or 0.0), 0.0)
        short, long = sorted((w, h))
        return w * h, short, long, long / max(short, 1e-6)
    if shape.shape_type in {"circle", "ellipse"}:
        rx = max(float(shape.rx or 0.0), 0.0)
        ry = max(float(shape.ry if shape.ry is not None else rx), 0.0)
        short, long = sorted((2.0 * rx, 2.0 * ry))
        return pi * rx * ry, short, long, long / max(short, 1e-6)
    if shape.points:
        xs = [float(p[0]) for p in shape.points]
        ys = [float(p[1]) for p in shape.points]
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        short, long = sorted((max(w, 0.0), max(h, 0.0)))
        area = _polygon_area(shape.points) if len(shape.points) >= 3 else 0.0
        return area, short, long, long / max(short, 1e-6)
    return 0.0, 0.0, 0.0, 1.0


def _shape_bbox(shape: Shape) -> tuple[float, float, float, float]:
    if shape.shape_type == "rectangle":
        x = float(shape.x or 0.0)
        y = float(shape.y or 0.0)
        w = max(float(shape.width or 0.0), 0.0)
        h = max(float(shape.height or 0.0), 0.0)
        return x, y, x + w, y + h
    if shape.shape_type in {"circle", "ellipse"}:
        cx = float(shape.cx or 0.0)
        cy = float(shape.cy or 0.0)
        rx = max(float(shape.rx or 0.0), 0.0)
        ry = max(float(shape.ry if shape.ry is not None else rx), 0.0)
        return cx - rx, cy - ry, cx + rx, cy + ry
    if shape.points:
        xs = [float(p[0]) for p in shape.points]
        ys = [float(p[1]) for p in shape.points]
        return min(xs), min(ys), max(xs), max(ys)
    return 0.0, 0.0, 0.0, 0.0


def _bbox_distance(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0.0, max(ax0, bx0) - min(ax1, bx1))
    dy = max(0.0, max(ay0, by0) - min(ay1, by1))
    return float(np.hypot(dx, dy))


def _shape_center(shape: Shape) -> tuple[float, float]:
    x0, y0, x1, y1 = _shape_bbox(shape)
    return (x0 + x1) / 2.0, (y0 + y1) / 2.0


def _color_distance(a: tuple[int, int, int] | None, b: tuple[int, int, int] | None) -> float:
    if a is None or b is None:
        return 999.0
    return float(np.linalg.norm(np.asarray(a, dtype=float) - np.asarray(b, dtype=float)))


def _shape_polygon_points(shape: Shape, curve_sides: int = 8) -> np.ndarray | None:
    if shape.shape_type == "polygon" and len(shape.points) >= 3:
        return np.asarray(shape.points, dtype=np.float32)
    if shape.shape_type == "rectangle":
        x0, y0, x1, y1 = _shape_bbox(shape)
        return np.asarray([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], dtype=np.float32)
    if shape.shape_type in {"circle", "ellipse"}:
        cx = float(shape.cx or 0.0)
        cy = float(shape.cy or 0.0)
        rx = max(float(shape.rx or 0.0), 0.0)
        ry = max(float(shape.ry if shape.ry is not None else rx), 0.0)
        if rx <= 0.0 or ry <= 0.0:
            return None
        n = max(4, int(curve_sides))
        return np.asarray(
            [
                (
                    cx + rx * cos(-pi / 2.0 + 2.0 * pi * i / n),
                    cy + ry * sin(-pi / 2.0 + 2.0 * pi * i / n),
                )
                for i in range(n)
            ],
            dtype=np.float32,
        )
    return None


def _shape_tags(shape: Shape) -> str:
    return " ".join(
        (
            shape.semantic_type or "",
            shape.character_part or "",
            shape.source_role or "",
            shape.layer_name or "",
        )
    ).lower()


def _character_fragment_kind(shape: Shape) -> str | None:
    tags = _shape_tags(shape)
    if "face" in tags or "eye" in tags or "mouth" in tags:
        return None
    if "hand" in tags or "finger" in tags:
        return "hand"
    if "hair" in tags:
        return "hair"
    if any(token in tags for token in ("accessory", "ruffle", "lace", "trim")):
        return "outfit_detail"
    return None


def _target_mass_kind(shape: Shape) -> str:
    tags = _shape_tags(shape)
    if "opaque_zone:hair:" in tags or "target_zone_hair_" in tags:
        return "hair"
    if "opaque_zone:arm:" in tags or "target_zone_arm_" in tags:
        return "hand"
    if "opaque_zone:clothing:" in tags or "target_zone_clothing_" in tags:
        return "garment"
    if "hair" in tags:
        return "hair"
    if "hand" in tags or "finger" in tags:
        return "hand"
    if any(
        token in tags
        for token in (
            "outfit", "torso", "body", "dress", "skirt", "sleeve",
            "clothing", "ruffle", "lace", "trim", "accessory",
        )
    ):
        return "garment"
    if any(token in tags for token in ("prop", "weapon")):
        return "prop"
    if any(token in tags for token in ("background", "skyline", "water", "structure")):
        return "background"
    if (shape.layer_name or "").lower() in {"background", "midground"}:
        return "background"
    return "generic"


def _is_character_like(shape: Shape) -> bool:
    tags = _shape_tags(shape)
    return any(token in tags for token in _CHARACTER_TOKENS)


def _apply_opaque_hierarchy(
    shapes: list[Shape],
    hierarchy: OpaqueSubjectHierarchy | None,
) -> tuple[list[Shape], dict]:
    stats = {"subject_shapes": 0, "background_shapes": 0, "neutral_shapes": 0}
    if hierarchy is None or not hierarchy.enabled:
        stats["neutral_shapes"] = len(shapes)
        return shapes, stats
    out: list[Shape] = []
    for shape in shapes:
        overlap = shape_subject_overlap(shape, hierarchy)
        if shape.fill_color is not None and shape.shape_type != "line" and overlap >= 0.42:
            out.append(replace(
                shape,
                importance=max(float(shape.importance), 0.86),
                source_role=f"opaque_subject:{shape.source_role}",
                layer_name="foreground",
            ))
            stats["subject_shapes"] += 1
        elif shape.fill_color is not None and shape.shape_type != "line" and overlap <= 0.10:
            out.append(replace(
                shape,
                importance=min(float(shape.importance), 0.78),
                source_role=f"opaque_background:{shape.source_role}",
                layer_name="background",
            ))
            stats["background_shapes"] += 1
        else:
            out.append(shape)
            stats["neutral_shapes"] += 1
    return out, stats



def _strict_character_base(shape: Shape) -> bool:
    semantic = (shape.semantic_type or "").lower()
    role = (shape.source_role or "").lower()
    layer = (shape.layer_name or "").lower()
    return semantic.startswith("character_") or role.startswith("character_") or layer.startswith("character_")


def _structure_zone_from_shape(shape: Shape) -> str | None:
    part = (shape.character_part or "").lower()
    tags = _shape_tags(shape)
    if part == "hair" or "character_hair" in tags:
        return "hair"
    if part == "outfit" or any(token in tags for token in ("character_outfit", "character_shoe", "character_sleeve")):
        return "clothing"
    if part in {"left_hand", "left_arm"}:
        return "left_arm"
    if part in {"right_hand", "right_arm"}:
        return "right_arm"
    if part == "left_leg":
        return "left_leg"
    if part == "right_leg":
        return "right_leg"
    if part in {"head", "face"}:
        return "head"
    if part == "torso":
        return "torso"
    return None


def _opaque_zone_name(shape: Shape) -> str | None:
    role = shape.source_role or ""
    marker = "opaque_zone:"
    if marker in role:
        tail = role.split(marker, 1)[1]
        return tail.split(":", 1)[0] or None
    semantic = shape.semantic_type or ""
    prefix = "target_zone_"
    if semantic.startswith(prefix):
        for suffix in ("_fragment", "_candidate"):
            if semantic.endswith(suffix):
                return semantic[len(prefix):-len(suffix)]
    return None


def _weighted_shape_color(shapes: list[Shape]) -> tuple[int, int, int] | None:
    usable = [s for s in shapes if s.fill_color is not None]
    if not usable:
        return None
    weights = [max(_shape_metrics(s)[0], 1.0) for s in usable]
    total = max(sum(weights), 1.0)
    return tuple(
        int(round(sum(float(s.fill_color[i]) * w for s, w in zip(usable, weights)) / total))
        for i in range(3)
    )


def _color_luma(color: tuple[int, int, int] | None) -> float:
    if color is None:
        return 0.0
    r, g, b = [float(v) for v in color]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _infer_face_reference(
    assignments: list[tuple[Shape, str]],
    zones: OpaqueSubjectZones,
) -> tuple[tuple[int, int, int] | None, str, int | None]:
    by_zone: dict[str, list[Shape]] = {}
    for shape, zone in assignments:
        by_zone.setdefault(zone, []).append(shape)
    head = [s for s in by_zone.get("head", []) if s.fill_color is not None]
    head_box = zones.zone_bbox("head")
    if not head or head_box is None:
        return None, "none", None
    hx0, hy0, hx1, hy1 = head_box
    head_area = max(float((hx1 - hx0) * (hy1 - hy0)), 1.0)

    left = max(by_zone.get("left_arm", []), key=lambda s: _shape_metrics(s)[0], default=None)
    right = max(by_zone.get("right_arm", []), key=lambda s: _shape_metrics(s)[0], default=None)
    if left is not None and right is not None and left.fill_color is not None and right.fill_color is not None:
        if _color_distance(left.fill_color, right.fill_color) <= 24.0:
            arm_ref = _weighted_shape_color([left, right])
            carrier = min(head, key=lambda s: _color_distance(s.fill_color, arm_ref))
            if (
                arm_ref is not None
                and _color_distance(carrier.fill_color, arm_ref) <= 30.0
                and _shape_metrics(carrier)[0] >= head_area * 0.006
            ):
                return arm_ref, "bilateral_arms", carrier.id

    best_pair: tuple[Shape, Shape] | None = None
    best_area = 0.0
    for i, a in enumerate(head):
        for b in head[i + 1:]:
            if _color_distance(a.fill_color, b.fill_color) > 12.0:
                continue
            combined = _shape_metrics(a)[0] + _shape_metrics(b)[0]
            if combined >= head_area * 0.025 and combined > best_area:
                best_pair, best_area = (a, b), combined
    if best_pair is not None:
        ref = _weighted_shape_color(list(best_pair))
        carrier = max(best_pair, key=lambda s: _shape_metrics(s)[0])
        return ref, "head_consensus", carrier.id
    return None, "none", None


def _infer_zone_refinements(
    assignments: list[tuple[Shape, str]],
    zones: OpaqueSubjectZones,
) -> tuple[dict[int, str], dict]:
    refinements: dict[int, str] = {}
    reference, reference_source, face_carrier_id = _infer_face_reference(assignments, zones)
    stats = {
        "face_reference_rgb": list(reference) if reference is not None else None,
        "face_reference_source": reference_source,
        "face_carrier_shape_id": face_carrier_id,
        "inferred_hair_shapes": 0,
        "inferred_hair_mode": "none",
        "inferred_clothing_shapes": 0,
        "inferred_clothing_seed_id": None,
        "propagated_clothing_shapes": 0,
    }
    if reference is None:
        return refinements, stats

    head_box = zones.zone_bbox("head")
    if head_box is not None:
        hx0, _hy0, hx1, _hy1 = head_box
        head_w = max(float(hx1 - hx0), 1.0)
        head_area = max(float((hx1 - hx0) * (_hy1 - _hy0)), 1.0)
        ref_luma = _color_luma(reference)
        head_candidates: list[Shape] = []
        carrier = next((shape for shape, zone in assignments if zone == "head" and shape.id == face_carrier_id), None)
        carrier_box = _shape_bbox(carrier) if carrier is not None else None
        for shape, zone in assignments:
            if zone != "head" or shape.id == face_carrier_id or shape.fill_color is None:
                continue
            area = _shape_metrics(shape)[0]
            bx0, by0, bx1, by1 = _shape_bbox(shape)
            width_ratio = max(0.0, bx1 - bx0) / head_w
            if area < head_area * 0.020 or width_ratio > 0.72:
                continue
            if _color_distance(shape.fill_color, reference) < 42.0:
                continue
            head_candidates.append(shape)
            if ref_luma - _color_luma(shape.fill_color) >= 32.0:
                refinements[shape.id] = "hair"
                stats["inferred_hair_shapes"] += 1
        if stats["inferred_hair_shapes"]:
            stats["inferred_hair_mode"] = "dark_contrast"
        elif carrier_box is not None and head_candidates:
            cx0, cy0, cx1, cy1 = carrier_box
            carrier_h = max(cy1 - cy0, 1.0)
            carrier_cx = (cx0 + cx1) / 2.0
            geometric: list[tuple[float, Shape]] = []
            for shape in head_candidates:
                bx0, by0, bx1, by1 = _shape_bbox(shape)
                area = _shape_metrics(shape)[0]
                center_x = (bx0 + bx1) / 2.0
                extends_above = max(0.0, cy0 - by0) / carrier_h
                horizontal_offset = abs(center_x - carrier_cx) / head_w
                overlap_x = max(0.0, min(bx1, cx1) - max(bx0, cx0))
                overlap_ratio = overlap_x / max(min(bx1 - bx0, cx1 - cx0), 1.0)
                if extends_above < 0.18 or horizontal_offset > 0.36 or overlap_ratio < 0.22:
                    continue
                score = area / head_area + 0.10 * extends_above + 0.04 * overlap_ratio
                geometric.append((score, shape))
            if geometric:
                primary_hair = max(geometric, key=lambda item: item[0])[1]
                refinements[primary_hair.id] = "hair"
                stats["inferred_hair_shapes"] = 1
                stats["inferred_hair_mode"] = "geometry_contrast"

    clothing_candidates: list[tuple[float, Shape]] = []
    for shape, zone in assignments:
        if zone not in {"torso", "legs"} or shape.fill_color is None:
            continue
        box = zones.zone_bbox(zone)
        if box is None:
            continue
        zx0, zy0, zx1, zy1 = box
        zone_area = max(float((zx1 - zx0) * (zy1 - zy0)), 1.0)
        area = _shape_metrics(shape)[0]
        if area >= zone_area * 0.040 and _color_distance(shape.fill_color, reference) >= 34.0:
            clothing_candidates.append((area, shape))
    if clothing_candidates:
        primary = max(clothing_candidates, key=lambda item: item[0])[1]
        refinements[primary.id] = "clothing"
        stats["inferred_clothing_shapes"] = 1
        stats["inferred_clothing_seed_id"] = primary.id
        subject_box = zones.bbox or zones.zone_bbox("torso")
        subject_scale = 1.0
        if subject_box is not None:
            sx0, sy0, sx1, sy1 = subject_box
            subject_scale = max(1.0, min(float(sx1 - sx0), float(sy1 - sy0)))
        primary_area = max(_shape_metrics(primary)[0], 1.0)
        for area, shape in sorted(clothing_candidates, key=lambda item: item[0], reverse=True):
            if shape.id == primary.id:
                continue
            if area < primary_area * 0.08:
                continue
            if _color_distance(shape.fill_color, primary.fill_color) > 28.0:
                continue
            if _color_distance(shape.fill_color, reference) < 30.0:
                continue
            if _bbox_distance(_shape_bbox(shape), _shape_bbox(primary)) > max(2.0, subject_scale * 0.10):
                continue
            refinements[shape.id] = "clothing"
            stats["inferred_clothing_shapes"] += 1
            stats["propagated_clothing_shapes"] += 1
            if stats["propagated_clothing_shapes"] >= 3:
                break
    return refinements, stats


def _apply_opaque_zones(
    shapes: list[Shape],
    zones: OpaqueSubjectZones | None,
) -> tuple[list[Shape], dict]:
    stats = {
        "zone_shapes": 0,
        "head_shapes": 0,
        "torso_shapes": 0,
        "arm_shapes": 0,
        "leg_shapes": 0,
        "hair_shapes": 0,
        "clothing_shapes": 0,
        "neutral_shapes": 0,
        "face_reference_rgb": None,
        "face_reference_source": "none",
        "face_carrier_shape_id": None,
        "inferred_hair_shapes": 0,
        "inferred_hair_mode": "none",
        "inferred_clothing_shapes": 0,
        "inferred_clothing_seed_id": None,
        "propagated_clothing_shapes": 0,
    }
    if zones is None or not zones.enabled:
        stats["neutral_shapes"] = len(shapes)
        return shapes, stats

    structure_mode = zones.reason == "character_structure"
    stats["zone_source"] = zones.reason
    assignments: list[tuple[Shape, str]] = []
    for shape in shapes:
        zone = _structure_zone_from_shape(shape) if structure_mode else None
        if zone is None and structure_mode and _target_mass_kind(shape) == "background" and not _is_character_like(shape):
            continue
        if zone is None:
            zone = dominant_shape_zone(shape, zones, min_overlap=0.42 if structure_mode else 0.28)
        if zone is not None:
            assignments.append((shape, zone))
    if structure_mode:
        inferred, inference_stats = {}, {
            "face_reference_rgb": None,
            "face_reference_source": "structure_metadata",
            "face_carrier_shape_id": None,
            "inferred_hair_shapes": 0,
            "inferred_hair_mode": "structure_metadata",
            "inferred_clothing_shapes": 0,
            "inferred_clothing_seed_id": None,
            "propagated_clothing_shapes": 0,
        }
    else:
        inferred, inference_stats = _infer_zone_refinements(assignments, zones)
    stats.update(inference_stats)

    out: list[Shape] = []
    garment_tokens = ("outfit", "dress", "skirt", "sleeve", "clothing", "ruffle", "lace", "trim")
    assignment_map = {shape.id: zone for shape, zone in assignments}
    for shape in shapes:
        zone = assignment_map.get(shape.id)
        if zone is None:
            out.append(shape)
            stats["neutral_shapes"] += 1
            continue
        tags = _shape_tags(shape)
        if shape.id in inferred:
            refined = inferred[shape.id]
        elif zone == "hair" or (zone == "head" and "hair" in tags):
            refined = "hair"
        elif zone == "clothing" or (zone in {"torso", "legs", "left_leg", "right_leg"} and any(token in tags for token in garment_tokens)):
            refined = "clothing"
        elif zone in {"left_arm", "right_arm"}:
            refined = "arm"
        elif zone in {"legs", "left_leg", "right_leg"}:
            refined = "leg"
        else:
            refined = zone
        floor = {
            "head": 0.88,
            "hair": 0.92,
            "torso": 0.90,
            "clothing": 0.88,
            "arm": 0.84,
            "leg": 0.86,
        }[refined]
        side_hint = shape.side_hint
        if zone in {"left_arm", "left_leg"}:
            side_hint = "left"
        elif zone in {"right_arm", "right_leg"}:
            side_hint = "right"
        importance = float(shape.importance)
        canonical = _strict_character_base(shape)
        if structure_mode and shape.source_role == "phase10_gesture_plane":
            out.append(replace(shape, side_hint=side_hint, importance=max(importance, floor)))
        elif structure_mode and canonical:
            # Character Structure already produced a protected semantic base. Do
            # not rewrite its role/layer/importance; the zones are advisory here.
            out.append(replace(shape, side_hint=side_hint))
        elif structure_mode:
            out.append(replace(
                shape,
                semantic_type=f"target_zone_{refined}_candidate",
                side_hint=side_hint,
            ))
        else:
            out.append(replace(
                shape,
                importance=max(importance, floor),
                source_role=f"opaque_zone:{refined}:{shape.source_role}",
                layer_name="foreground",
                side_hint=side_hint,
            ))
        stats["zone_shapes"] += 1
        stats[f"{refined}_shapes"] += 1
    return out, stats

def _local_shape_cover_ratio(shape: Shape, carriers: list[Shape]) -> float:
    poly = _shape_polygon_points(shape)
    if poly is None or len(poly) < 3 or not carriers:
        return 0.0
    x0 = int(np.floor(poly[:, 0].min()))
    y0 = int(np.floor(poly[:, 1].min()))
    x1 = int(np.ceil(poly[:, 0].max())) + 1
    y1 = int(np.ceil(poly[:, 1].max())) + 1
    if x1 <= x0 or y1 <= y0:
        return 0.0
    local = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    pts = np.round(poly - np.asarray([x0, y0], dtype=np.float32)).astype(np.int32)
    cv2.fillPoly(local, [pts], 1)
    denom = int(local.sum())
    if denom <= 0:
        return 0.0
    covered = np.zeros_like(local)
    for carrier in carriers:
        cpoly = _shape_polygon_points(carrier)
        if cpoly is None or len(cpoly) < 3:
            continue
        cpts = np.round(cpoly - np.asarray([x0, y0], dtype=np.float32)).astype(np.int32)
        cv2.fillPoly(covered, [cpts], 1)
    return float((local * covered).sum()) / float(denom)


def _prune_render_inert_occluded_fragments(
    scene: Scene,
    shapes: list[Shape],
) -> tuple[list[Shape], int]:
    """Remove low-value generic fills that are fully hidden by later opaque fills.

    Process candidates from the top of the render stack downward so a removed
    candidate is never used as an occluding carrier for another removal.
    """
    if len(shapes) < 2:
        return shapes, 0
    canvas_area = max(float(scene.width * scene.height), 1.0)
    render_order = sorted(range(len(shapes)), key=lambda i: shapes[i].z_index)
    removed_indices: set[int] = set()

    for pos in range(len(render_order) - 1, -1, -1):
        idx = render_order[pos]
        shape = shapes[idx]
        if shape.shape_type not in {"polygon", "rectangle"}:
            continue
        if shape.fill_color is None or shape.stroke_color is not None or float(shape.stroke_width) > 0.0:
            continue
        if (shape.semantic_type or "").lower() not in {"subject_mass", "subject_organic"}:
            continue
        if (shape.source_role or "").lower() != "structure" or (shape.layer_name or "").lower() != "midground":
            continue
        if (shape.character_part or "unknown").lower() not in {"", "unknown", "none"}:
            continue
        if _strict_character_base(shape) or _macro_zone_kind(shape) is not None or _gesture_carrier_kind(shape) is not None:
            continue
        if _target_mass_kind(shape) != "background":
            continue
        area = _shape_metrics(shape)[0]
        if area <= 0.0 or area / canvas_area > 0.030 or float(shape.importance) >= 0.60:
            continue

        later = [
            shapes[j]
            for j in render_order[pos + 1 :]
            if j not in removed_indices and shapes[j].fill_color is not None
        ]
        if _local_shape_cover_ratio(shape, later) >= 0.999:
            removed_indices.add(idx)

    if not removed_indices:
        return shapes, 0
    return [shape for i, shape in enumerate(shapes) if i not in removed_indices], len(removed_indices)


def _prune_structure_redundant_fragments(
    shapes: list[Shape],
    scene: Scene,
    zones: OpaqueSubjectZones | None,
) -> tuple[list[Shape], int]:
    if zones is None or not zones.enabled or zones.reason != "character_structure":
        return shapes, 0
    canvas_area = max(float(scene.width * scene.height), 1.0)
    garment_carriers = [
        s for s in shapes
        if _strict_character_base(s) and _target_mass_kind(s) == "garment"
    ]
    if not garment_carriers:
        return shapes, 0
    remove_ids: set[int] = set()
    for shape in shapes:
        if shape.semantic_type != "target_zone_clothing_candidate":
            continue
        area = _shape_metrics(shape)[0]
        if area / canvas_area > 0.0045 or float(shape.importance) >= 0.66:
            continue
        if _local_shape_cover_ratio(shape, garment_carriers) >= 0.82:
            remove_ids.add(shape.id)
    if not remove_ids:
        return shapes, 0
    return [s for s in shapes if s.id not in remove_ids], len(remove_ids)


def _relax_low_value_zone_fragment(shape: Shape, canvas_area: float, min_side: float) -> Shape:
    zone = _opaque_zone_name(shape)
    if zone not in {"head", "arm", "clothing", "leg"}:
        return shape
    area, short, _long, aspect = _shape_metrics(shape)
    area_ratio = area / max(canvas_area, 1.0)
    thin = short <= max(1.5, min_side * 0.028) and aspect >= 3.0
    micro_limit = {"head": 0.0018, "arm": 0.0026, "clothing": 0.0030, "leg": 0.0018}[zone]
    importance_limit = {"head": 0.90, "arm": 0.87, "clothing": 0.90, "leg": 0.87}[zone]
    if float(shape.importance) >= importance_limit:
        return shape
    if not thin and area_ratio > micro_limit:
        return shape
    return replace(
        shape,
        semantic_type=f"target_zone_{zone}_fragment",
        character_part="unknown",
        source_role="target_fragment",
    )


def _relax_low_value_character_fragment(
    shape: Shape,
    canvas_area: float,
    min_side: float,
) -> Shape:
    kind = _character_fragment_kind(shape)
    if kind is None:
        return shape
    area, short, _long, aspect = _shape_metrics(shape)
    area_ratio = area / max(canvas_area, 1.0)
    short_limit = max(1.5, min_side * 0.030)
    thin = short <= short_limit and aspect >= 3.2
    micro_limit = {"hand": 0.0040, "hair": 0.0030, "outfit_detail": 0.0060}[kind]
    importance_limit = {"hand": 0.88, "hair": 0.86, "outfit_detail": 0.92}[kind]
    if float(shape.importance) >= importance_limit:
        return shape
    if not thin and area_ratio > micro_limit:
        return shape
    return replace(
        shape,
        semantic_type=f"target_{kind}_fragment",
        character_part="unknown",
        source_role="target_fragment",
    )


def _face_box_from_metadata(scene: Scene) -> tuple[float, float, float, float] | None:
    structure = scene.metadata.get("character", {}).get("structure", {})
    parts = structure.get("parts", []) if isinstance(structure, dict) else []
    face = next((p for p in parts if str(p.get("part_type", "")) == "face"), None)
    if face is not None and len(face.get("bbox", [])) == 4:
        x, y, w, h = [float(v) for v in face["bbox"]]
        return x, y, x + w, y + h
    head = next((p for p in parts if str(p.get("part_type", "")) == "head"), None)
    if head is not None and len(head.get("bbox", [])) == 4:
        x, y, w, h = [float(v) for v in head["bbox"]]
        return x + 0.18 * w, y + 0.18 * h, x + 0.82 * w, y + 0.86 * h
    return None


_FACE_FEATURE_TOKENS = (
    "eye", "iris", "pupil", "mouth", "lip", "eyebrow", "brow",
    "nose", "eyelash", "face_detail", "facial_detail",
)


def _is_explicit_face_feature(shape: Shape) -> bool:
    tags = _shape_tags(shape)
    if any(token in tags for token in ("hair", "prop", "hand", "finger")):
        return False
    return any(token in tags for token in _FACE_FEATURE_TOKENS)


def _suppress_face_fragments(
    scene: Scene,
    shapes: list[Shape],
    opaque_zones: OpaqueSubjectZones | None = None,
) -> tuple[list[Shape], int]:
    """Make the default Rinka face a single quiet skin plane.

    Phase 11 deliberately treats eyes, mouth, brows, nose and similar local
    marks as removable even when upstream analysis gave them high importance.
    The largest non-detail face carrier is retained so the head silhouette and
    skin block remain readable. Hair, hands and props crossing the face box are
    never consumed by this pass.
    """
    box = _face_box_from_metadata(scene)
    if box is None and opaque_zones is not None and opaque_zones.enabled:
        head = opaque_zones.zone_bbox("head")
        if head is not None:
            hx0, hy0, hx1, hy1 = head
            hw, hh = hx1 - hx0, hy1 - hy0
            box = (hx0 + 0.18 * hw, hy0 + 0.16 * hh, hx0 + 0.82 * hw, hy0 + 0.90 * hh)
    if box is None:
        return shapes, 0
    x0, y0, x1, y1 = box
    face_area = max((x1 - x0) * (y1 - y0), 1.0)
    inside: list[Shape] = []
    for shape in shapes:
        if shape.fill_color is None or shape.shape_type == "line":
            continue
        tags = _shape_tags(shape)
        if any(token in tags for token in ("hair", "prop", "hand", "finger")) or _opaque_zone_name(shape) == "hair":
            continue
        cx, cy = _shape_center(shape)
        if x0 <= cx <= x1 and y0 <= cy <= y1:
            inside.append(shape)
    if not inside:
        return shapes, 0

    explicit_ids = {shape.id for shape in inside if _is_explicit_face_feature(shape)}
    carrier_candidates = [shape for shape in inside if shape.id not in explicit_ids]
    remove_ids: set[int] = set(explicit_ids)
    if carrier_candidates:
        carrier = max(carrier_candidates, key=lambda s: _shape_metrics(s)[0])
        carrier_area = _shape_metrics(carrier)[0]
        if carrier_area >= face_area * 0.06:
            for shape in carrier_candidates:
                if shape.id == carrier.id:
                    continue
                area = _shape_metrics(shape)[0]
                # Faceless is the default target, so local interior marks are
                # removed by relative size rather than upstream importance.
                if area <= max(face_area * 0.24, carrier_area * 0.82):
                    remove_ids.add(shape.id)

    if not remove_ids:
        return shapes, 0
    return [s for s in shapes if s.id not in remove_ids], len(remove_ids)


def _merge_mass_pair(a: Shape, b: Shape, min_side: float) -> Shape | None:
    if a.fill_color is None or b.fill_color is None:
        return None
    if a.shape_type == "line" or b.shape_type == "line":
        return None
    if a.stroke_width > 0 or b.stroke_width > 0 or a.layer_name != b.layer_name:
        return None
    kind_a = _target_mass_kind(a)
    kind_b = _target_mass_kind(b)
    if any(
        token in _shape_tags(a) or token in _shape_tags(b)
        for token in ("phase12_face_anchor", "phase12_hair_anchor", "phase15_macro_", "phase15_face_fallback_anchor")
    ):
        return None
    if kind_a != kind_b or kind_a == "prop":
        return None
    if kind_a == "hand":
        side_a = (a.side_hint or "unknown").lower()
        side_b = (b.side_hint or "unknown").lower()
        if side_a in {"left", "right"} and side_b in {"left", "right"} and side_a != side_b:
            return None
    color_limit, gap_ratio, max_inflation = {
        "hair": (24.0, 0.020, 1.20),
        "hand": (30.0, 0.025, 1.28),
        "garment": (32.0, 0.032, 1.30),
        "background": (38.0, 0.050, 1.38),
        "generic": (20.0, 0.015, 1.16),
    }[kind_a]
    if _color_distance(a.fill_color, b.fill_color) > color_limit:
        return None
    if _bbox_distance(_shape_bbox(a), _shape_bbox(b)) > max(1.0, min_side * gap_ratio):
        return None
    pa = _shape_polygon_points(a)
    pb = _shape_polygon_points(b)
    if pa is None or pb is None:
        return None
    aa = max(_shape_metrics(a)[0], 0.0)
    ab = max(_shape_metrics(b)[0], 0.0)
    area_sum = aa + ab
    if area_sum <= 1e-6:
        return None
    hull = cv2.convexHull(np.vstack([pa, pb])).reshape(-1, 2)
    hull_area = abs(float(cv2.contourArea(hull)))
    if hull_area / area_sum > max_inflation:
        return None
    keep = a if (a.importance, aa) >= (b.importance, ab) else b
    weight = max(area_sum, 1e-6)
    fill = tuple(
        int(round((a.fill_color[i] * aa + b.fill_color[i] * ab) / weight))
        for i in range(3)
    )
    return replace(
        keep,
        shape_type="polygon",
        fill_color=fill,
        points=[(float(x), float(y)) for x, y in hull],
        x=None, y=None, width=None, height=None,
        cx=None, cy=None, rx=None, ry=None,
        z_index=max(a.z_index, b.z_index),
        importance=max(float(a.importance), float(b.importance)),
    )


def _consolidate_masses(shapes: list[Shape], min_side: float) -> tuple[list[Shape], int]:
    working = list(shapes)
    merged_count = 0
    changed = True
    while changed:
        changed = False
        for i, a in enumerate(working):
            for j in range(i + 1, len(working)):
                merged = _merge_mass_pair(a, working[j], min_side)
                if merged is None:
                    continue
                working = working[:i] + [merged] + working[i + 1:j] + working[j + 1:]
                merged_count += 1
                changed = True
                break
            if changed:
                break
    return working, merged_count


def _canonical_outfit_layer(shape: Shape) -> str | None:
    tags = _shape_tags(shape)
    if "character_outfit_base" in tags:
        return "base"
    if "character_outfit_detail" in tags:
        return "detail"
    return None


def _union_hull_iou(a: Shape, b: Shape) -> float:
    pa = _shape_polygon_points(a)
    pb = _shape_polygon_points(b)
    if pa is None or pb is None or len(pa) < 3 or len(pb) < 3:
        return 0.0
    pts = np.vstack([pa, pb])
    x0 = int(np.floor(pts[:, 0].min()))
    y0 = int(np.floor(pts[:, 1].min()))
    x1 = int(np.ceil(pts[:, 0].max())) + 1
    y1 = int(np.ceil(pts[:, 1].max())) + 1
    if x1 <= x0 or y1 <= y0:
        return 0.0
    union = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    for poly in (pa, pb):
        local = np.round(poly - np.asarray([x0, y0], dtype=np.float32)).astype(np.int32)
        cv2.fillPoly(union, [local], 1)
    hull = cv2.convexHull(pts).reshape(-1, 2)
    hull_mask = np.zeros_like(union)
    local_hull = np.round(hull - np.asarray([x0, y0], dtype=np.float32)).astype(np.int32)
    cv2.fillPoly(hull_mask, [local_hull], 1)
    denom = int(hull_mask.sum())
    if denom <= 0:
        return 0.0
    return float((union * hull_mask).sum()) / float(denom)


def _merge_outfit_layer_pair(base: Shape, detail: Shape) -> Shape:
    pa = _shape_polygon_points(base)
    pb = _shape_polygon_points(detail)
    assert pa is not None and pb is not None
    hull = cv2.convexHull(np.vstack([pa, pb])).reshape(-1, 2)
    return replace(
        base,
        shape_type="polygon",
        points=[(float(x), float(y)) for x, y in hull],
        x=None, y=None, width=None, height=None,
        cx=None, cy=None, rx=None, ry=None,
        z_index=max(base.z_index, detail.z_index),
        importance=max(float(base.importance), float(detail.importance)),
    )


def _consolidate_outfit_layers(shapes: list[Shape], min_side: float) -> tuple[list[Shape], int]:
    bases = [s for s in shapes if _canonical_outfit_layer(s) == "base"]
    details = [s for s in shapes if _canonical_outfit_layer(s) == "detail"]
    candidates: list[tuple[float, float, int, int]] = []
    for base in bases:
        if base.fill_color is None:
            continue
        base_area = max(_shape_metrics(base)[0], 1e-6)
        for detail in details:
            if detail.fill_color is None:
                continue
            side_base = (base.side_hint or "unknown").lower()
            side_detail = (detail.side_hint or "unknown").lower()
            if side_base in {"left", "right"} and side_detail in {"left", "right"} and side_base != side_detail:
                continue
            detail_area = max(_shape_metrics(detail)[0], 0.0)
            if detail_area / base_area > 0.18:
                continue
            color_distance = _color_distance(base.fill_color, detail.fill_color)
            if color_distance > 24.0:
                continue
            if _bbox_distance(_shape_bbox(base), _shape_bbox(detail)) > max(1.0, min_side * 0.018):
                continue
            union_iou = _union_hull_iou(base, detail)
            if union_iou < 0.94:
                continue
            candidates.append((union_iou, -color_distance, base.id, detail.id))
    if not candidates:
        return shapes, 0
    by_id = {s.id: s for s in shapes}
    used: set[int] = set()
    replacements: dict[int, Shape] = {}
    removed: set[int] = set()
    merged_count = 0
    for _, _, base_id, detail_id in sorted(candidates, reverse=True):
        if base_id in used or detail_id in used:
            continue
        base = by_id[base_id]
        detail = by_id[detail_id]
        replacements[base_id] = _merge_outfit_layer_pair(base, detail)
        removed.add(detail_id)
        used.update({base_id, detail_id})
        merged_count += 1
    if not merged_count:
        return shapes, 0
    out: list[Shape] = []
    for shape in shapes:
        if shape.id in removed:
            continue
        out.append(replacements.get(shape.id, shape))
    return out, merged_count



def _gesture_carrier_kind(shape: Shape) -> str | None:
    part = (shape.character_part or "unknown").lower()
    role = (shape.source_role or "").lower()
    semantic = (shape.semantic_type or "").lower()
    if part in {"left_hand", "right_hand"} or "character_hand" in role:
        return "hand"
    if part in {"left_arm", "right_arm"}:
        return "arm"
    if "character_limb_base" in role and "arm" in semantic:
        return "arm"
    if "opaque_zone:arm:" in role or semantic.startswith("target_zone_arm_"):
        return "opaque_arm"
    return None


def _polygon_raster_iou(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or len(b) < 3:
        return 0.0
    pts = np.vstack([a, b])
    x0 = int(np.floor(pts[:, 0].min()))
    y0 = int(np.floor(pts[:, 1].min()))
    x1 = int(np.ceil(pts[:, 0].max())) + 1
    y1 = int(np.ceil(pts[:, 1].max())) + 1
    if x1 <= x0 or y1 <= y0:
        return 0.0
    offset = np.asarray([x0, y0], dtype=np.float32)
    ma = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    mb = np.zeros_like(ma)
    cv2.fillPoly(ma, [np.round(a - offset).astype(np.int32)], 1)
    cv2.fillPoly(mb, [np.round(b - offset).astype(np.int32)], 1)
    union = int(np.logical_or(ma, mb).sum())
    if union <= 0:
        return 0.0
    return float(np.logical_and(ma, mb).sum()) / float(union)


def _polygon_major_axis_angle(points: np.ndarray) -> float:
    (_cx, _cy), (w, h), angle = cv2.minAreaRect(points.astype(np.float32))
    if w < h:
        angle += 90.0
    return float(angle % 180.0)


def _axis_angle_distance(a: float, b: float) -> float:
    delta = abs(a - b) % 180.0
    return min(delta, 180.0 - delta)


def _polygon_centroid(points: np.ndarray) -> np.ndarray:
    moments = cv2.moments(points.astype(np.float32))
    if abs(float(moments["m00"])) <= 1e-6:
        return points.mean(axis=0)
    return np.asarray(
        [moments["m10"] / moments["m00"], moments["m01"] / moments["m00"]],
        dtype=np.float32,
    )


def _hand_symbol_from_group(group: list[Shape], min_side: float) -> Shape | None:
    """Collapse one hand into a single fingerless geometric symbol."""
    polygons = [_shape_polygon_points(shape) for shape in group]
    polygons = [poly for poly in polygons if poly is not None and len(poly) >= 3]
    if not polygons:
        return None
    all_points = np.vstack(polygons).astype(np.float32)
    (cx, cy), (rect_w, rect_h), angle = cv2.minAreaRect(all_points)
    major = max(float(rect_w), float(rect_h))
    minor = min(float(rect_w), float(rect_h))
    if major <= 1e-6 or minor <= 1e-6:
        return None
    if rect_w < rect_h:
        angle += 90.0

    # A six-sided beveled block reads as a hand but cannot accidentally turn
    # into a three/four-finger silhouette. Keep it compact by matching the
    # source filled area rather than the spread-finger bounding hull.
    source_area = max(sum(_shape_metrics(shape)[0] for shape in group), 1.0)
    aspect = min(1.50, max(1.0, major / max(minor, 1e-6)))
    unit = np.asarray(
        [(-0.58, -1.0), (0.58, -1.0), (1.0, 0.0),
         (0.58, 1.0), (-0.58, 1.0), (-1.0, 0.0)],
        dtype=np.float32,
    )
    unit_area = max(abs(float(cv2.contourArea(unit))), 1e-6)
    half_major = float(np.sqrt(source_area * aspect / unit_area))
    half_minor = half_major / aspect
    half_major = min(half_major, major * 0.50)
    half_minor = min(half_minor, minor * 0.58)
    floor = max(0.75, min_side * 0.004)
    half_major = max(half_major, floor)
    half_minor = max(half_minor, floor * 0.72)

    local = unit * np.asarray([half_major, half_minor], dtype=np.float32)
    theta = np.deg2rad(float(angle))
    rotation = np.asarray(
        [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]],
        dtype=np.float32,
    )
    points = local @ rotation.T + np.asarray([cx, cy], dtype=np.float32)

    primary = max(group, key=lambda shape: (float(shape.importance), _shape_metrics(shape)[0]))
    weighted = [(shape, max(_shape_metrics(shape)[0], 1.0)) for shape in group if shape.fill_color is not None]
    fill = primary.fill_color
    if weighted:
        total = sum(weight for _, weight in weighted)
        fill = tuple(
            int(round(sum(shape.fill_color[channel] * weight for shape, weight in weighted) / total))
            for channel in range(3)
        )
    return replace(
        primary,
        shape_type="polygon",
        fill_color=fill,
        points=[(float(x), float(y)) for x, y in points],
        x=None, y=None, width=None, height=None,
        cx=None, cy=None, rx=None, ry=None,
        z_index=max(shape.z_index for shape in group),
        importance=max(0.985, max(float(shape.importance) for shape in group)),
        source_role="target_hand_symbol",
        semantic_type="target_hand_symbol",
    )


def _abstract_hand_symbols(shapes: list[Shape], min_side: float) -> tuple[list[Shape], dict]:
    """Replace anatomical hand contours with at most one block per known side."""
    hand_shapes = [shape for shape in shapes if _gesture_carrier_kind(shape) == "hand"]
    if not hand_shapes:
        return shapes, {
            "input_shapes": 0, "symbol_count": 0, "merged_shapes": 0,
            "vertices_before": 0, "vertices_after": 0, "vertices_removed": 0,
        }

    groups: dict[str, list[Shape]] = {}
    for shape in hand_shapes:
        side = (shape.side_hint or "unknown").lower()
        key = side if side in {"left", "right"} else f"unknown:{shape.id}"
        groups.setdefault(key, []).append(shape)

    replacements: dict[int, Shape] = {}
    removed_ids: set[int] = set()
    vertices_before = sum(len(shape.points) for shape in hand_shapes)
    symbol_count = 0
    for group in groups.values():
        symbol = _hand_symbol_from_group(group, min_side)
        if symbol is None:
            continue
        primary_id = symbol.id
        replacements[primary_id] = symbol
        removed_ids.update(shape.id for shape in group if shape.id != primary_id)
        symbol_count += 1

    out: list[Shape] = []
    for shape in shapes:
        if shape.id in removed_ids:
            continue
        out.append(replacements.get(shape.id, shape))
    vertices_after = sum(
        len(shape.points) for shape in out if (shape.source_role or "") == "target_hand_symbol"
    )
    return out, {
        "input_shapes": len(hand_shapes),
        "symbol_count": symbol_count,
        "merged_shapes": max(0, len(hand_shapes) - symbol_count),
        "vertices_before": vertices_before,
        "vertices_after": vertices_after,
        "vertices_removed": max(0, vertices_before - vertices_after),
    }


def _prune_target_microdetails(scene: Scene, shapes: list[Shape]) -> tuple[list[Shape], int]:
    """Drop explicit decorative crumbs after the identity-bearing masses exist."""
    canvas_area = max(float(scene.width * scene.height), 1.0)
    remove_ids: set[int] = set()
    micro_tokens = ("ruffle", "lace", "stitch", "seam", "nail", "finger")
    for shape in shapes:
        tags = _shape_tags(shape)
        if (shape.source_role or "") == "target_hand_symbol":
            continue
        if _target_mass_kind(shape) in {"prop", "hair"}:
            continue
        area_ratio = _shape_metrics(shape)[0] / canvas_area
        explicit_micro = any(token in tags for token in micro_tokens)
        target_fragment = "target_fragment" in tags or (
            (shape.semantic_type or "").startswith("target_")
            and (shape.semantic_type or "").endswith("_fragment")
        )
        if explicit_micro and area_ratio <= 0.0045:
            remove_ids.add(shape.id)
        elif target_fragment and area_ratio <= 0.0035 and float(shape.importance) < 0.90:
            remove_ids.add(shape.id)
    if not remove_ids:
        return shapes, 0
    return [shape for shape in shapes if shape.id not in remove_ids], len(remove_ids)



def _hair_line_length(shape: Shape) -> float:
    if shape.shape_type != "line" or len(shape.points) < 2:
        return 0.0
    points = np.asarray(shape.points, dtype=np.float32)
    return float(np.linalg.norm(points[-1] - points[0]))


def _simplify_hair_plane(shape: Shape, min_side: float) -> tuple[Shape, int]:
    """Reduce a filled hair contour to a calmer poster plane when raster-safe."""
    if _target_mass_kind(shape) != "hair" or shape.shape_type != "polygon" or len(shape.points) <= 8:
        return shape, 0
    points = np.asarray(shape.points, dtype=np.float32)
    contour = points.reshape(-1, 1, 2)
    perimeter = float(cv2.arcLength(contour, True))
    if perimeter <= 1e-6:
        return shape, 0
    original_area = max(abs(float(cv2.contourArea(points))), 1.0)
    original_centroid = _polygon_centroid(points)
    best: tuple[int, float, np.ndarray] | None = None
    for epsilon_ratio in (0.10, 0.08, 0.06, 0.05, 0.04, 0.03, 0.025, 0.020, 0.015, 0.010):
        candidate = cv2.approxPolyDP(contour, perimeter * epsilon_ratio, True).reshape(-1, 2)
        if len(candidate) < 4 or len(candidate) >= len(points):
            continue
        candidate_area = max(abs(float(cv2.contourArea(candidate))), 1.0)
        if abs(candidate_area - original_area) / original_area > 0.08:
            continue
        raster_iou = _polygon_raster_iou(points, candidate)
        if raster_iou < 0.93:
            continue
        centroid_shift = float(np.linalg.norm(original_centroid - _polygon_centroid(candidate)))
        if centroid_shift > max(1.0, min_side * 0.015):
            continue
        ranking = (len(candidate), -raster_iou)
        if best is None or ranking < (best[0], -best[1]):
            best = (len(candidate), raster_iou, candidate.copy())
    if best is None:
        return shape, 0
    candidate = best[2]
    return replace(shape, points=[(float(x), float(y)) for x, y in candidate]), len(points) - len(candidate)


def _abstract_hair_planes(shapes: list[Shape], min_side: float) -> tuple[list[Shape], dict]:
    """Prefer a few filled hair planes over repeated strand/bang line work."""
    hair_shapes = [shape for shape in shapes if _target_mass_kind(shape) == "hair"]
    filled = [shape for shape in hair_shapes if shape.fill_color is not None and shape.shape_type != "line"]
    if not hair_shapes:
        return shapes, {
            "input_shapes": 0,
            "filled_planes": 0,
            "line_cues_removed": 0,
            "major_flow_cues_preserved": 0,
            "simplified_planes": 0,
            "vertices_removed": 0,
        }

    remove_ids: set[int] = set()
    preserved_major = 0
    local_line_limit = max(1.0, min_side * 0.22)
    local_gap_limit = max(2.0, min_side * 0.15)
    if filled:
        for shape in hair_shapes:
            if shape.shape_type != "line":
                continue
            length = _hair_line_length(shape)
            if length >= local_line_limit:
                preserved_major += 1
                continue
            if min(_bbox_distance(_shape_bbox(shape), _shape_bbox(carrier)) for carrier in filled) <= local_gap_limit:
                remove_ids.add(shape.id)

    out: list[Shape] = []
    simplified_planes = 0
    vertices_removed = 0
    for shape in shapes:
        if shape.id in remove_ids:
            continue
        simplified, removed = _simplify_hair_plane(shape, min_side)
        out.append(simplified)
        if removed:
            simplified_planes += 1
            vertices_removed += removed
    return out, {
        "input_shapes": len(hair_shapes),
        "filled_planes": len(filled),
        "line_cues_removed": len(remove_ids),
        "major_flow_cues_preserved": preserved_major,
        "simplified_planes": simplified_planes,
        "vertices_removed": vertices_removed,
    }


def _outfit_block_candidate(shape: Shape) -> bool:
    if shape.fill_color is None or shape.shape_type == "line":
        return False
    part = (shape.character_part or "unknown").lower()
    semantic = (shape.semantic_type or "").lower()
    return part == "outfit" or semantic.startswith("target_zone_clothing_")


def _outfit_block_family(shape: Shape) -> str:
    tags = _shape_tags(shape)
    if any(token in tags for token in ("shoe", "boot", "footwear")):
        return "footwear"
    if any(token in tags for token in ("skirt", "short", "pants", "trouser", "lower_outfit")):
        return "lower"
    if (shape.semantic_type or "").lower().startswith("target_zone_clothing_"):
        return "generic_clothing"
    return "upper"


def _consolidate_outfit_color_blocks(shapes: list[Shape], min_side: float) -> tuple[list[Shape], dict]:
    """Flatten near-duplicate garment colors and merge only raster-safe small pieces."""
    working = list(shapes)
    candidates = [shape for shape in working if _outfit_block_candidate(shape)]
    if not candidates:
        return working, {
            "input_shapes": 0,
            "color_blocks_before": 0,
            "color_blocks_after": 0,
            "recolored_shapes": 0,
            "merged_shapes": 0,
        }

    before_colors = {shape.fill_color for shape in candidates if shape.fill_color is not None}
    by_id = {shape.id: shape for shape in working}
    recolored: dict[int, Shape] = {}
    used: set[int] = set()
    recolored_count = 0
    for family in sorted({_outfit_block_family(shape) for shape in candidates}):
        family_shapes = sorted(
            [shape for shape in candidates if _outfit_block_family(shape) == family],
            key=lambda shape: _shape_metrics(shape)[0],
            reverse=True,
        )
        for anchor in family_shapes:
            if anchor.id in used or anchor.fill_color is None:
                continue
            group = [anchor]
            used.add(anchor.id)
            for shape in family_shapes:
                if shape.id in used or shape.fill_color is None:
                    continue
                if _color_distance(anchor.fill_color, shape.fill_color) > 32.0:
                    continue
                if _bbox_distance(_shape_bbox(anchor), _shape_bbox(shape)) > max(2.0, min_side * 0.10):
                    continue
                group.append(shape)
                used.add(shape.id)
            if len(group) < 2:
                continue
            dominant = anchor.fill_color
            for shape in group[1:]:
                if shape.fill_color != dominant:
                    recolored[shape.id] = replace(shape, fill_color=dominant)
                    recolored_count += 1

    if recolored:
        working = [recolored.get(shape.id, shape) for shape in working]

    # After color flattening, absorb only a small adjacent piece into a larger
    # block when the convex hull remains a faithful representation of the union.
    merged_count = 0
    changed = True
    while changed:
        changed = False
        garment = [shape for shape in working if _outfit_block_candidate(shape)]
        for base in sorted(garment, key=lambda shape: _shape_metrics(shape)[0], reverse=True):
            base_area = max(_shape_metrics(base)[0], 1e-6)
            for detail in garment:
                if detail.id == base.id:
                    continue
                # Phase 5 deliberately limits canonical outfit-detail absorption
                # to one detail per base. Priority 2 may recolor a surviving
                # detail, but must not silently consume a second one here.
                if _canonical_outfit_layer(detail) == "detail":
                    continue
                if _outfit_block_family(base) != _outfit_block_family(detail):
                    continue
                if base.fill_color is None or detail.fill_color is None or base.fill_color != detail.fill_color:
                    continue
                detail_area = max(_shape_metrics(detail)[0], 0.0)
                if detail_area <= 0.0 or detail_area / base_area > 0.28:
                    continue
                side_base = (base.side_hint or "unknown").lower()
                side_detail = (detail.side_hint or "unknown").lower()
                if side_base in {"left", "right"} and side_detail in {"left", "right"} and side_base != side_detail:
                    continue
                if _bbox_distance(_shape_bbox(base), _shape_bbox(detail)) > max(1.0, min_side * 0.035):
                    continue
                if _union_hull_iou(base, detail) < 0.80:
                    continue
                merged = _merge_outfit_layer_pair(base, detail)
                working = [
                    merged if shape.id == base.id else shape
                    for shape in working
                    if shape.id != detail.id
                ]
                merged_count += 1
                changed = True
                break
            if changed:
                break

    after_candidates = [shape for shape in working if _outfit_block_candidate(shape)]
    after_colors = {shape.fill_color for shape in after_candidates if shape.fill_color is not None}
    return working, {
        "input_shapes": len(candidates),
        "color_blocks_before": len(before_colors),
        "color_blocks_after": len(after_colors),
        "recolored_shapes": recolored_count,
        "merged_shapes": merged_count,
    }


def _gesture_hand_anchors(shapes: list[Shape]) -> dict[str, Shape]:
    anchors: dict[str, Shape] = {}
    for shape in shapes:
        if _gesture_carrier_kind(shape) != "hand":
            continue
        side = (shape.side_hint or "unknown").lower()
        if side not in {"left", "right"}:
            continue
        current = anchors.get(side)
        if current is None or (_shape_metrics(shape)[0], shape.importance) > (_shape_metrics(current)[0], current.importance):
            anchors[side] = shape
    return anchors


def _simplify_gesture_arm(
    shape: Shape,
    *,
    min_side: float,
    hand_anchor: Shape | None,
) -> tuple[Shape, int, bool]:
    kind = _gesture_carrier_kind(shape)
    if kind not in {"arm", "opaque_arm"} or shape.shape_type != "polygon":
        return shape, 0, False
    points = _shape_polygon_points(shape)
    if points is None or len(points) <= 4:
        return shape, 0, False
    contour = points.astype(np.float32).reshape(-1, 1, 2)
    perimeter = float(cv2.arcLength(contour, True))
    if perimeter <= 1e-6:
        return shape, 0, False
    iou_limit = 0.955 if kind == "opaque_arm" else 0.950
    original_axis = _polygon_major_axis_angle(points)
    original_centroid = _polygon_centroid(points)
    original_anchor_gap = None
    if hand_anchor is not None:
        original_anchor_gap = _bbox_distance(_shape_bbox(shape), _shape_bbox(hand_anchor))
    best: tuple[int, float, np.ndarray] | None = None
    for epsilon_ratio in (0.070, 0.060, 0.050, 0.040, 0.030, 0.025, 0.020, 0.015):
        candidate = cv2.approxPolyDP(contour, perimeter * epsilon_ratio, True).reshape(-1, 2)
        if len(candidate) < 4 or len(candidate) >= len(points):
            continue
        raster_iou = _polygon_raster_iou(points, candidate)
        if raster_iou < iou_limit:
            continue
        if _axis_angle_distance(original_axis, _polygon_major_axis_angle(candidate)) > 8.0:
            continue
        centroid_shift = float(np.linalg.norm(original_centroid - _polygon_centroid(candidate)))
        if centroid_shift > max(1.0, min_side * 0.010):
            continue
        if hand_anchor is not None and original_anchor_gap is not None:
            candidate_shape = replace(shape, points=[(float(x), float(y)) for x, y in candidate])
            candidate_gap = _bbox_distance(_shape_bbox(candidate_shape), _shape_bbox(hand_anchor))
            allowed_gap = original_anchor_gap + max(0.75, min_side * 0.004)
            if candidate_gap > allowed_gap:
                continue
            if original_anchor_gap <= 1.0 and candidate_gap > 1.0:
                continue
        ranking = (len(candidate), -raster_iou)
        if best is None or ranking < (best[0], -best[1]):
            best = (len(candidate), raster_iou, candidate.copy())
    if best is None:
        return shape, 0, False
    candidate = best[2]
    removed = len(points) - len(candidate)
    return replace(shape, points=[(float(x), float(y)) for x, y in candidate]), removed, hand_anchor is not None


def _abstract_gesture_shapes(shapes: list[Shape], min_side: float) -> tuple[list[Shape], dict]:
    anchors = _gesture_hand_anchors(shapes)
    out: list[Shape] = []
    simplified_shapes = 0
    vertices_removed = 0
    anchored_simplifications = 0
    for shape in shapes:
        side = (shape.side_hint or "unknown").lower()
        anchor = anchors.get(side) if side in {"left", "right"} else None
        simplified, removed, anchored = _simplify_gesture_arm(
            shape,
            min_side=min_side,
            hand_anchor=anchor,
        )
        out.append(simplified)
        if removed > 0:
            simplified_shapes += 1
            vertices_removed += removed
            anchored_simplifications += int(anchored)
    return out, {
        "simplified_shapes": simplified_shapes,
        "vertices_removed": vertices_removed,
        "anchored_simplifications": anchored_simplifications,
        "hand_anchors": len(anchors),
    }


def _refine_outfit_layers_once(scene: Scene, shapes: list[Shape], min_side: float) -> tuple[list[Shape], int]:
    if not bool(scene.metadata.get("subject_mode")) or not ((scene.metadata.get("character") or {}).get("structure")):
        return shapes, 0
    bases = [s for s in shapes if _canonical_outfit_layer(s) == "base" and s.fill_color is not None]
    details = [s for s in shapes if _canonical_outfit_layer(s) == "detail" and s.fill_color is not None]
    candidates: list[tuple[float, float, float, int, int]] = []
    for base in bases:
        base_area = max(_shape_metrics(base)[0], 1e-6)
        for detail in details:
            side_base = (base.side_hint or "unknown").lower()
            side_detail = (detail.side_hint or "unknown").lower()
            if side_base in {"left", "right"} and side_detail in {"left", "right"} and side_base != side_detail:
                continue
            detail_area = max(_shape_metrics(detail)[0], 0.0)
            ratio = detail_area / base_area
            if ratio > 0.14:
                continue
            color_distance = _color_distance(base.fill_color, detail.fill_color)
            if color_distance > 16.0:
                continue
            gap = _bbox_distance(_shape_bbox(base), _shape_bbox(detail))
            if gap > max(0.75, min_side * 0.010):
                continue
            union_iou = _union_hull_iou(base, detail)
            if union_iou < 0.96:
                continue
            candidates.append((union_iou, -color_distance, -ratio, base.id, detail.id))
    if not candidates:
        return shapes, 0
    _, _, _, base_id, detail_id = max(candidates)
    by_id = {s.id: s for s in shapes}
    merged = _merge_outfit_layer_pair(by_id[base_id], by_id[detail_id])
    out = [merged if s.id == base_id else s for s in shapes if s.id != detail_id]
    return out, 1


def _compress_background(scene: Scene, shapes: list[Shape]) -> tuple[list[Shape], int]:
    canvas_area = max(float(scene.width * scene.height), 1.0)
    background = [
        s for s in shapes
        if _target_mass_kind(s) == "background"
        and not _is_character_like(s)
        and "opaque_subject" not in _shape_tags(s)
    ]
    if not background:
        return shapes, 0
    subject_mode = bool(scene.metadata.get("subject_mode"))
    opaque_mode = any("opaque_subject" in _shape_tags(s) for s in shapes)
    if subject_mode:
        cap = 8
    elif opaque_mode:
        cap = max(8, int(round(len(shapes) * 0.32)))
    else:
        cap = max(10, int(round(len(shapes) * 0.45)))
    remove_ids: set[int] = set()
    for shape in background:
        area_ratio = _shape_metrics(shape)[0] / canvas_area
        if area_ratio <= 0.0018 and float(shape.importance) < 0.58:
            remove_ids.add(shape.id)
    survivors = [s for s in background if s.id not in remove_ids]
    if len(survivors) > cap:
        ranked = sorted(
            survivors,
            key=lambda s: (
                min(1.0, (_shape_metrics(s)[0] / canvas_area) / 0.03) * 0.62
                + max(0.0, min(1.0, float(s.importance))) * 0.38
            ),
            reverse=True,
        )
        keep_ids = {s.id for s in ranked[:cap]}
        for shape in survivors:
            area_ratio = _shape_metrics(shape)[0] / canvas_area
            if shape.id not in keep_ids and area_ratio < 0.05 and float(shape.importance) < 0.93:
                remove_ids.add(shape.id)
    if not remove_ids:
        return shapes, 0
    return [s for s in shapes if s.id not in remove_ids], len(remove_ids)


def _rgb_saturation(color: tuple[int, int, int]) -> float:
    values = np.asarray(color, dtype=float) / 255.0
    maximum = float(np.max(values))
    minimum = float(np.min(values))
    if maximum <= 1e-6:
        return 0.0
    return (maximum - minimum) / maximum


def _mix_rgb(a: tuple[int, int, int], b: tuple[int, int, int], ratio: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, float(ratio)))
    return tuple(
        int(round(max(0.0, min(255.0, float(x) * (1.0 - t) + float(y) * t))))
        for x, y in zip(a, b)
    )


def _poster_subject_shapes(shapes: list[Shape]) -> list[Shape]:
    return [
        shape for shape in shapes
        if shape.fill_color is not None
        and (
            _strict_character_base(shape)
            or _macro_zone_kind(shape) is not None
            or _gesture_carrier_kind(shape) is not None
            or _target_mass_kind(shape) in {"hair", "garment", "hand", "prop"}
        )
    ]


def _has_poster_subject_evidence(scene: Scene, shapes: list[Shape]) -> bool:
    if bool(scene.metadata.get("subject_mode")):
        return True
    segmentation = scene.metadata.get("rinka_subject_segmentation") or {}
    if bool(segmentation.get("activated")):
        return True
    return len(_poster_subject_shapes(shapes)) >= 2


def _poster_anchor_color(shapes: list[Shape]) -> tuple[int, int, int] | None:
    candidates = []
    for shape in _poster_subject_shapes(shapes):
        color = shape.fill_color
        if color is None:
            continue
        area = _shape_metrics(shape)[0]
        saturation = _rgb_saturation(color)
        mass = _target_mass_kind(shape)
        mass_bonus = 1.25 if mass in {"garment", "hair"} else 1.0
        score = area * mass_bonus * (0.82 + 0.28 * saturation) * (0.80 + 0.20 * float(shape.importance))
        candidates.append((score, color))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _poster_base_color(
    scene: Scene,
    shapes: list[Shape],
) -> tuple[tuple[int, int, int], tuple[int, int, int] | None, str]:
    source = scene.background
    if source is not None:
        saturation = _rgb_saturation(source)
        brightness = sum(source) / (3.0 * 255.0)
        if saturation >= 0.08 or brightness <= 0.90:
            return source, _poster_anchor_color(shapes), "source"

    anchor = _poster_anchor_color(shapes)
    if anchor is None:
        return (232, 232, 230), None, "neutral_fallback"

    saturation = _rgb_saturation(anchor)
    brightness = sum(anchor) / (3.0 * 255.0)
    if saturation < 0.08:
        base = (226, 230, 236) if brightness < 0.62 else (58, 61, 68)
        return base, anchor, "neutral_contrast"

    red, green, blue = (channel / 255.0 for channel in anchor)
    hue, sat, value = rgb_to_hsv(red, green, blue)
    hue = (hue + 0.46) % 1.0
    sat = max(0.28, min(0.56, 0.20 + sat * 0.58))
    value = 0.34 if value >= 0.72 else 0.80
    rgb = hsv_to_rgb(hue, sat, value)
    base = tuple(int(round(channel * 255.0)) for channel in rgb)
    return base, anchor, "derived_contrast"


def _poster_panel_colors(
    base: tuple[int, int, int],
    anchor: tuple[int, int, int] | None,
) -> list[tuple[int, int, int]]:
    if anchor is None or _color_distance(base, anchor) < 18.0:
        brightness = sum(base) / 3.0
        anchor = (36, 39, 46) if brightness >= 150.0 else (232, 234, 238)
    contrast = (28, 31, 38) if sum(base) / 3.0 >= 150.0 else (238, 239, 242)
    return [
        _mix_rgb(base, anchor, 0.18),
        _mix_rgb(base, anchor, 0.34),
        _mix_rgb(base, contrast, 0.14),
    ]


def _subject_bbox_from_shapes(shapes: list[Shape]) -> tuple[float, float, float, float] | None:
    subject = _poster_subject_shapes(shapes)
    if not subject:
        return None
    boxes = [_shape_bbox(shape) for shape in subject]
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def _geometrize_background(
    scene: Scene,
    shapes: list[Shape],
    *,
    style: str = "source",
    preserve_large_generic_cues: bool = True,
    preserve_semantic_cues: bool = True,
) -> tuple[list[Shape], tuple[int, int, int] | None, dict]:
    stats = {
        "enabled": False,
        "style": style,
        "reason": "source_background",
        "generated_panels": 0,
        "surviving_panels": 0,
        "replaced_background_shapes": 0,
        "preserved_scene_cues": 0,
        "background_color_source": "source",
        "background_color": scene.background,
    }
    if style == "source":
        return shapes, scene.background, stats
    if style != "geometric":
        raise ValueError(f"Unsupported Rinka background style: {style}")
    if not _has_poster_subject_evidence(scene, shapes):
        stats["reason"] = "no_subject_evidence"
        return shapes, scene.background, stats

    canvas_area = max(float(scene.width * scene.height), 1.0)
    def definite_background(shape: Shape) -> bool:
        tags = _shape_tags(shape)
        layer = (shape.layer_name or "").lower()
        if _is_character_like(shape) or "opaque_subject" in tags:
            return False
        if "opaque_background" in tags or layer == "background":
            return True
        return any(token in tags for token in ("background", "skyline", "water", "horizon"))

    background_shapes = [shape for shape in shapes if definite_background(shape)]
    protected_ids: set[int] = set()
    ranked_cues: list[tuple[float, Shape]] = []
    for shape in background_shapes:
        tags = _shape_tags(shape)
        area_ratio = _shape_metrics(shape)[0] / canvas_area
        semantic_cue = any(token in tags for token in ("skyline", "water", "structure", "horizon"))
        if (
            preserve_semantic_cues
            and semantic_cue
            and area_ratio >= 0.045
            and float(shape.importance) >= 0.78
        ) or (
            preserve_large_generic_cues
            and area_ratio >= 0.18
            and float(shape.importance) >= 0.94
        ):
            ranked_cues.append((area_ratio * (0.5 + float(shape.importance)), shape))
    for _score, shape in sorted(ranked_cues, key=lambda item: item[0], reverse=True)[:2]:
        protected_ids.add(shape.id)

    remove_ids = {shape.id for shape in background_shapes if shape.id not in protected_ids}
    retained = [shape for shape in shapes if shape.id not in remove_ids]
    base, anchor, source = _poster_base_color(scene, retained)
    panel_colors = _poster_panel_colors(base, anchor)
    subject_bbox = _subject_bbox_from_shapes(retained)
    subject_center_x = (subject_bbox[0] + subject_bbox[2]) * 0.5 if subject_bbox else scene.width * 0.5
    mirror = subject_center_x < scene.width * 0.5

    templates = [
        [(0.00, 0.00), (0.64, 0.00), (0.53, 0.16), (0.34, 0.31), (0.00, 0.26)],
        [(1.00, 0.15), (1.00, 0.69), (0.80, 0.61), (0.64, 0.42), (0.78, 0.22)],
        [(0.00, 0.66), (0.19, 0.56), (0.43, 0.74), (0.34, 1.00), (0.00, 1.00)],
    ]
    if mirror:
        templates = [[(1.0 - x, y) for x, y in points] for points in templates]

    min_z = min((shape.z_index for shape in retained), default=0)
    next_id = max((shape.id for shape in retained), default=0) + 1001
    panels: list[Shape] = []
    for index, (points, color) in enumerate(zip(templates, panel_colors)):
        panels.append(Shape(
            id=next_id + index,
            shape_type="polygon",
            fill_color=color,
            points=[(x * scene.width, y * scene.height) for x, y in points],
            z_index=min_z - 100 + index,
            importance=0.88 - index * 0.03,
            source_role="target_geometric_background",
            layer_name="background",
            semantic_type="target_geometric_background",
            character_part="background",
        ))

    stats.update({
        "enabled": True,
        "reason": "geometric_poster",
        "generated_panels": len(panels),
        "replaced_background_shapes": len(remove_ids),
        "preserved_scene_cues": len(protected_ids),
        "background_color_source": source,
        "background_color": base,
    })
    return panels + retained, base, stats


def _curve_to_polygon(shape: Shape, sides: int = 6) -> Shape:
    if shape.shape_type not in {"circle", "ellipse"}:
        return shape
    pts = _shape_polygon_points(shape, curve_sides=sides)
    if pts is None:
        return shape
    return replace(
        shape,
        shape_type="polygon",
        points=[(float(x), float(y)) for x, y in pts],
        x=None, y=None, width=None, height=None,
        cx=None, cy=None, rx=None, ry=None,
    )


def _macro_zone_kind(shape: Shape) -> str | None:
    zone = _opaque_zone_name(shape)
    if zone is not None:
        return zone
    semantic = (shape.semantic_type or "").lower()
    part = (shape.character_part or "").lower()
    for token in ("hair", "head", "clothing", "torso", "arm", "leg"):
        if f"target_zone_{token}_" in semantic:
            return token
    if part in {"head", "face"}:
        return "head"
    if part == "hair":
        return "hair"
    if part in {"outfit", "torso"}:
        return "clothing" if part == "outfit" else "torso"
    if part in {"left_arm", "right_arm", "left_hand", "right_hand"}:
        return "arm"
    if part in {"left_leg", "right_leg"}:
        return "leg"
    return None


def _macro_shape_priority_score(scene: Scene, shape: Shape) -> float:
    canvas_area = max(float(scene.width * scene.height), 1.0)
    area_ratio = _shape_metrics(shape)[0] / canvas_area
    importance = max(0.0, min(1.0, float(shape.importance)))
    value = importance * 0.42
    value += min(1.0, area_ratio / 0.025) * 0.38
    if (shape.layer_name or "").lower() == "foreground":
        value += 0.06

    mass_kind = _target_mass_kind(shape)
    gesture_kind = _gesture_carrier_kind(shape)
    if _strict_character_base(shape):
        value += 0.18
    if gesture_kind in {"arm", "opaque_arm", "hand"}:
        value += 0.14
    elif mass_kind == "hair":
        value += 0.14
    elif mass_kind == "garment":
        value += 0.10
    elif mass_kind == "prop":
        value += 0.08

    zone = _macro_zone_kind(shape)
    if zone in {"head", "hair"}:
        value += 0.12
    elif zone in {"torso", "clothing"}:
        value += 0.10
    elif zone in {"arm", "leg"}:
        value += 0.08

    tags = _shape_tags(shape)
    if "opaque_subject" in tags:
        value += 0.12
    if mass_kind == "background" and not _is_character_like(shape):
        value -= 0.10
    if "opaque_background" in tags:
        value -= 0.06
    return value


def _bbox_overlap_ratio_with_subject(shape: Shape, subject_zones: OpaqueSubjectZones | None) -> float:
    if subject_zones is None or not subject_zones.enabled or subject_zones.bbox is None:
        return 0.0
    sx0, sy0, sx1, sy1 = _shape_bbox(shape)
    bx0, by0, bx1, by1 = [float(v) for v in subject_zones.bbox]
    area = max(0.0, sx1 - sx0) * max(0.0, sy1 - sy0)
    if area <= 1e-6:
        return 0.0
    ix0, iy0 = max(sx0, bx0), max(sy0, by0)
    ix1, iy1 = min(sx1, bx1), min(sy1, by1)
    inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    return inter / area


def _macro_subject_continuity(
    scene: Scene,
    shape: Shape,
    shapes: list[Shape],
    subject_zones: OpaqueSubjectZones | None,
) -> bool:
    if _bbox_overlap_ratio_with_subject(shape, subject_zones) < 0.25 or shape.fill_color is None:
        return False
    min_side = max(float(min(scene.width, scene.height)), 1.0)
    for other in shapes:
        if other.id == shape.id or other.fill_color is None:
            continue
        zone = _macro_zone_kind(other)
        definite_subject = (
            _strict_character_base(other)
            or zone is not None
            or _gesture_carrier_kind(other) is not None
            or _target_mass_kind(other) in {"hair", "garment", "hand", "prop"}
        )
        if not definite_subject:
            continue
        if _color_distance(shape.fill_color, other.fill_color) > 12.0:
            continue
        if _bbox_distance(_shape_bbox(shape), _shape_bbox(other)) <= max(1.0, min_side * 0.050):
            return True
    return False


def _global_shape_value(
    scene: Scene,
    shape: Shape,
    shapes: list[Shape],
    subject_zones: OpaqueSubjectZones | None,
) -> float:
    """Score global visual value before cleanup instead of trusting local detail alone."""
    canvas_area = max(float(scene.width * scene.height), 1.0)
    area, _short, _long, aspect = _shape_metrics(shape)
    area_ratio = max(0.0, area / canvas_area)
    importance = max(0.0, min(1.0, float(shape.importance)))
    macro_score = max(0.0, min(1.0, _macro_shape_priority_score(scene, shape) / 1.20))
    area_score = min(1.0, float(np.sqrt(area_ratio / 0.025))) if area_ratio > 0 else 0.0
    overlap_score = min(1.0, _bbox_overlap_ratio_with_subject(shape, subject_zones) / 0.45)

    mass_kind = _target_mass_kind(shape)
    zone = _macro_zone_kind(shape)
    gesture = _gesture_carrier_kind(shape)
    definite_subject = (
        _strict_character_base(shape)
        or zone is not None
        or gesture is not None
        or mass_kind in {"hair", "garment", "hand", "prop"}
    )
    if definite_subject:
        semantic_score = 1.0
    elif mass_kind == "background" and not _is_character_like(shape):
        semantic_score = 0.0
    else:
        semantic_score = 0.35

    score = (
        macro_score * 0.34
        + area_score * 0.24
        + importance * 0.18
        + overlap_score * 0.12
        + semantic_score * 0.12
    )
    if _macro_subject_continuity(scene, shape, shapes, subject_zones):
        score += 0.12
    if (shape.layer_name or "").lower() == "foreground":
        score += 0.04

    tags = _shape_tags(shape)
    if mass_kind == "background" and not _is_character_like(shape):
        score -= 0.12
    if "opaque_background" in tags:
        score -= 0.06

    if area_ratio <= 0.014 and aspect >= 2.8:
        sliver_severity = min(1.0, max(0.0, (aspect - 2.8) / 5.0))
        smallness = min(1.0, max(0.0, (0.014 - area_ratio) / 0.014))
        score -= 0.10 * (0.45 + 0.55 * sliver_severity) * smallness
    return max(0.0, min(1.0, score))


def _score_global_shapes(
    scene: Scene,
    shapes: list[Shape],
    subject_zones: OpaqueSubjectZones | None,
    *,
    low_value_threshold: float = 0.34,
) -> tuple[dict[int, float], dict]:
    scores = {
        shape.id: _global_shape_value(scene, shape, shapes, subject_zones)
        for shape in shapes
    }
    values = list(scores.values())
    low_ids = {shape_id for shape_id, score in scores.items() if score <= low_value_threshold}
    low_background = sum(
        1 for shape in shapes
        if shape.id in low_ids
        and _target_mass_kind(shape) == "background"
        and not _is_character_like(shape)
    )
    low_subject = sum(
        1 for shape in shapes
        if shape.id in low_ids
        and (
            _strict_character_base(shape)
            or _macro_zone_kind(shape) is not None
            or _gesture_carrier_kind(shape) is not None
            or _target_mass_kind(shape) in {"hair", "garment", "hand", "prop"}
        )
    )
    thin_candidates = 0
    canvas_area = max(float(scene.width * scene.height), 1.0)
    min_side = max(float(min(scene.width, scene.height)), 1.0)
    for shape in shapes:
        area, short, _long, aspect = _shape_metrics(shape)
        if (
            shape.id in low_ids
            and shape.shape_type != "line"
            and short <= max(1.6, min_side * 0.035)
            and aspect >= 2.8
            and area / canvas_area <= 0.014
        ):
            thin_candidates += 1
    return scores, {
        "enabled": True,
        "score_version": "v1",
        "count": len(scores),
        "min": min(values) if values else 0.0,
        "max": max(values) if values else 0.0,
        "mean": float(np.mean(values)) if values else 0.0,
        "low_value_threshold": low_value_threshold,
        "low_value_count": len(low_ids),
        "low_value_background_count": low_background,
        "low_value_subject_count": low_subject,
        "low_value_thin_candidates": thin_candidates,
    }


def _macro_priority_shadow(
    scene: Scene,
    shapes: list[Shape],
    subject_zones: OpaqueSubjectZones | None,
    *,
    budget: int | None,
) -> dict:
    stats = {
        "budget": budget,
        "would_remove": 0,
        "would_remove_background": 0,
        "would_remove_subject": 0,
        "would_remove_generic": 0,
        "would_remove_inside_subject_bbox": 0,
        "would_remove_subject_continuity": 0,
        "blocked_by_subject_bbox": False,
        "blocked_by_subject_continuity": False,
    }
    if budget is None or budget <= 0 or len(shapes) <= budget:
        return stats
    ranked = sorted(shapes, key=lambda s: _macro_shape_priority_score(scene, s), reverse=True)
    candidates = ranked[budget:]
    for shape in candidates:
        mass_kind = _target_mass_kind(shape)
        zone = _macro_zone_kind(shape)
        continuity = _macro_subject_continuity(scene, shape, shapes, subject_zones)
        if continuity:
            stats["would_remove_subject_continuity"] += 1
            stats["would_remove_subject"] += 1
        elif mass_kind == "background" and not _is_character_like(shape):
            stats["would_remove_background"] += 1
        elif _strict_character_base(shape) or zone is not None or _gesture_carrier_kind(shape) is not None or mass_kind in {"hair", "garment", "hand", "prop"}:
            stats["would_remove_subject"] += 1
        else:
            stats["would_remove_generic"] += 1
        if _bbox_overlap_ratio_with_subject(shape, subject_zones) >= 0.25:
            stats["would_remove_inside_subject_bbox"] += 1
    stats["would_remove"] = len(candidates)
    stats["blocked_by_subject_bbox"] = stats["would_remove_inside_subject_bbox"] > 0
    stats["blocked_by_subject_continuity"] = stats["would_remove_subject_continuity"] > 0
    return stats


def _final_shape_cap(
    scene: Scene,
    shapes: list[Shape],
    target_max_shapes: int | None,
) -> tuple[list[Shape], int, dict]:
    stats = {
        "budget": target_max_shapes,
        "removed": 0,
        "removed_background": 0,
        "removed_subject": 0,
        "removed_generic": 0,
    }
    if target_max_shapes is None or target_max_shapes <= 0 or len(shapes) <= target_max_shapes:
        return shapes, 0, stats
    ranked = sorted(shapes, key=lambda s: _macro_shape_priority_score(scene, s), reverse=True)
    keep_ids = {s.id for s in ranked[:target_max_shapes]}
    removed = [s for s in shapes if s.id not in keep_ids]
    for shape in removed:
        mass_kind = _target_mass_kind(shape)
        zone = _macro_zone_kind(shape)
        if mass_kind == "background" and not _is_character_like(shape):
            stats["removed_background"] += 1
        elif _strict_character_base(shape) or zone is not None or _gesture_carrier_kind(shape) is not None or mass_kind in {"hair", "garment", "hand", "prop"}:
            stats["removed_subject"] += 1
        else:
            stats["removed_generic"] += 1
    stats["removed"] = len(removed)
    capped = [s for s in shapes if s.id in keep_ids]
    return capped, len(removed), stats




def _promote_approved_reference_fringe(
    shapes: list[Shape],
    face_anchor: Shape | None,
    width: int,
    height: int,
    head_anchor: Shape | None = None,
) -> tuple[list[Shape], dict]:
    stats = {"candidate_count": 0, "promoted": 0, "promoted_ids": [], "clipped_fallback": False}
    if face_anchor is None or face_anchor.fill_color is None:
        return shapes, stats
    fx0, fy0, fx1, fy1 = _shape_bbox(face_anchor)
    fw, fh = max(fx1 - fx0, 1.0), max(fy1 - fy0, 1.0)
    face_area = fw * fh
    zx0, zy0, zx1, zy1 = fx0 - 0.22 * fw, fy0 - 0.34 * fh, fx1 + 0.22 * fw, fy0 + 0.60 * fh
    candidates: list[tuple[float, Shape]] = []
    oversized: list[tuple[float, Shape]] = []
    for shape in shapes:
        if shape.id == face_anchor.id or shape.fill_color is None:
            continue
        if shape.source_role not in {"phase10_subject_plane", "phase10_gesture_plane"}:
            continue
        sx0, sy0, sx1, sy1 = _shape_bbox(shape)
        area = _shape_metrics(shape)[0]
        if area <= 1.0:
            continue
        color_distance = _color_distance(shape.fill_color, face_anchor.fill_color)
        if color_distance < 24.0:
            continue
        if head_anchor is not None and head_anchor.fill_color is not None:
            head = np.asarray(head_anchor.fill_color, dtype=np.float32)
            candidate = np.asarray(shape.fill_color, dtype=np.float32)
            head_luma = float(0.2126 * head[0] + 0.7152 * head[1] + 0.0722 * head[2])
            candidate_luma = float(0.2126 * candidate[0] + 0.7152 * candidate[1] + 0.0722 * candidate[2])
            candidate_chroma = float(candidate.max() - candidate.min())
            if head_luma >= 215.0 and candidate_luma <= 205.0 and candidate_chroma <= 28.0:
                continue
        qx0, qy0 = max(sx0, zx0), max(sy0, zy0)
        qx1, qy1 = min(sx1, zx1), min(sy1, zy1)
        zone_area = max(0.0, qx1 - qx0) * max(0.0, qy1 - qy0)
        if area > face_area * 1.35:
            if area <= face_area * 6.0 and zone_area / max(face_area, 1.0) >= 0.18:
                oversized.append((zone_area / max(face_area, 1.0) + min(color_distance / 180.0, 1.0) * 0.12, shape))
            continue
        cx, cy = _shape_center(shape)
        if cy > fy0 + 0.62 * fh:
            continue
        ix0, iy0 = max(sx0, fx0), max(sy0, fy0)
        ix1, iy1 = min(sx1, fx1), min(sy1, fy1)
        face_overlap = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0) / max(face_area, 1.0)
        zone_overlap = zone_area / max(area, 1.0)
        if face_overlap < 0.025 and zone_overlap < 0.18:
            continue
        vertical_bonus = max(0.0, 1.0 - max(cy - fy0, 0.0) / max(fh, 1.0))
        score = face_overlap * 4.0 + zone_overlap * 0.75 + vertical_bonus * 0.25 + min(color_distance / 160.0, 1.0) * 0.10
        candidates.append((score, shape))
    stats["candidate_count"] = len(candidates)
    selected = [shape for _score, shape in sorted(candidates, key=lambda item: item[0], reverse=True)[:2]]
    selected_ids = {shape.id for shape in selected}
    promoted: list[Shape] = []
    rank = {shape.id: index for index, shape in enumerate(selected)}
    for shape in shapes:
        if shape.id in selected_ids:
            promoted.append(replace(shape, z_index=face_anchor.z_index + 20 + rank[shape.id], importance=max(float(shape.importance), 0.995)))
        else:
            promoted.append(shape)
    if not selected and oversized:
        _score, source = max(oversized, key=lambda item: item[0])
        points = _shape_polygon_points(source)
        if points is not None:
            mask = np.zeros((max(int(height), 1), max(int(width), 1)), dtype=np.uint8)
            cv2.fillPoly(mask, [np.round(points).astype(np.int32)], 1)
            clip = np.zeros_like(mask)
            cx0 = max(0, int(round(fx0 - 0.12 * fw)))
            cx1 = min(mask.shape[1], int(round(fx1 + 0.12 * fw)))
            cy0 = max(0, int(round(fy0 - 0.24 * fh)))
            cy1 = min(mask.shape[0], int(round(fy0 + 0.46 * fh)))
            clip[cy0:cy1, cx0:cx1] = 1
            clipped = mask & clip
            if int(clipped.sum()) >= max(18, int(round(face_area * 0.08))):
                contours, _ = cv2.findContours(clipped, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    contour = max(contours, key=cv2.contourArea)
                    perimeter = float(cv2.arcLength(contour, True))
                    polygon = None
                    for ratio in (0.035, 0.05, 0.07, 0.09):
                        approx = cv2.approxPolyDP(contour, max(1.0, perimeter * ratio), True).reshape(-1, 2)
                        if 3 <= len(approx) <= 8:
                            polygon = approx
                            break
                    if polygon is not None:
                        fringe = Shape(
                            id=max((shape.id for shape in promoted), default=949000) + 1000,
                            shape_type="polygon",
                            fill_color=source.fill_color,
                            points=[(float(x), float(y)) for x, y in polygon],
                            z_index=face_anchor.z_index + 20,
                            importance=0.995,
                            source_role="phase16_fringe_slice",
                            layer_name="foreground",
                            semantic_type="character_hair_fringe",
                            character_part="hair",
                            part_confidence=0.88,
                        )
                        promoted.append(fringe)
                        selected_ids.add(fringe.id)
                        stats["clipped_fallback"] = True
    stats["promoted"] = len(selected_ids)
    stats["promoted_ids"] = sorted(selected_ids)
    return promoted, stats

def _apply_approved_reference_direct_style(
    scene: Scene,
    *,
    curve_polygon_sides: int,
    target_max_shapes: int | None,
    protected_face_anchor: Shape | None,
    protected_macro_anchors: tuple[Shape, ...] | list[Shape] | None,
    macro_subject_guard_stats: dict | None,
    phase12_anchor_stats: dict | None,
    phase15_face_fallback_stats: dict | None,
) -> Scene:
    """Render the approved-reference preset from coarse subject planes directly.

    The approved 18 references favor large source-colored planes over the generic
    target-style cleanup stack. Re-running those planes through hierarchy, global
    scoring, mass merging, and gesture abstraction fragments good portrait masses.
    This path therefore keeps the deterministic subject planes intact, overlays one
    blank face carrier, and only adds the geometric background plus the final cap.
    """
    shapes = list(scene.shapes)
    macro_anchor_ids: set[int] = set()
    if protected_macro_anchors:
        macro_anchor_ids = {shape.id for shape in protected_macro_anchors}
        shapes = [shape for shape in shapes if shape.id not in macro_anchor_ids]
        shapes.extend(protected_macro_anchors)
    if protected_face_anchor is not None:
        shapes = [shape for shape in shapes if shape.id != protected_face_anchor.id]
        shapes.append(protected_face_anchor)
    macro_head = next((shape for shape in (protected_macro_anchors or []) if shape.character_part == "head"), None)
    shapes, fringe_promotion = _promote_approved_reference_fringe(
        shapes, protected_face_anchor, scene.width, scene.height, macro_head
    )

    background_styled, result_background, background_geometry = _geometrize_background(
        scene,
        shapes,
        style="geometric",
        preserve_large_generic_cues=False,
        preserve_semantic_cues=False,
    )
    straight = [_curve_to_polygon(shape, curve_polygon_sides) for shape in background_styled]
    capped, cap_removed, macro_priority = _final_shape_cap(scene, straight, target_max_shapes)

    metadata = dict(scene.metadata)
    metadata["shape_count_pre_target_style"] = len(scene.shapes)
    metadata["shape_count"] = len(capped)
    metadata["target_style"] = {
        "name": RINKA_REFERENCE_NAME,
        "version": RINKA_REFERENCE_VERSION,
        "curve_polygon_sides": max(4, int(curve_polygon_sides)),
        "target_max_shapes": target_max_shapes,
        "shape_count_before": len(scene.shapes),
        "shape_count_after": len(capped),
        "quality_metrics_scope": "pre_target_style",
        "preset": "approved_reference",
        "approved_reference_direct": True,
        "phase12_anchor_guard": phase12_anchor_stats or {"enabled": False, "reason": "not_requested"},
        "macro_subject_guard": macro_subject_guard_stats or {"enabled": False, "reason": "not_requested"},
        "phase15_face_fallback": phase15_face_fallback_stats or {"enabled": False, "reason": "not_requested"},
        "macro_anchor_injected": len(macro_anchor_ids),
        "fringe_promotion": fringe_promotion,
        "face_fragments_removed": 0,
        "mass_merges": 0,
        "outfit_layer_merges": 0,
        "microdetail_removed": 0,
        "render_inert_occluded_removed": 0,
        "background_removed": 0,
        "background_geometry": {
            **background_geometry,
            "surviving_panels": sum(
                1 for shape in capped if (shape.semantic_type or "") == "target_geometric_background"
            ),
        },
        "cap_removed": cap_removed,
        "macro_priority": macro_priority,
    }
    return Scene(
        width=scene.width,
        height=scene.height,
        background=result_background,
        shapes=sorted(capped, key=lambda shape: shape.z_index),
        metadata=metadata,
    )


def apply_rinka_reference_style(
    scene: Scene,
    *,
    curve_polygon_sides: int = 6,
    target_max_shapes: int | None = None,
    opaque_hierarchy: OpaqueSubjectHierarchy | None = None,
    opaque_zones: OpaqueSubjectZones | None = None,
    background_style: str = "source",
    preset: str | None = None,
    protected_face_anchor: Shape | None = None,
    protected_hair_anchor: Shape | None = None,
    phase12_anchor_stats: dict | None = None,
    protected_macro_anchors: tuple[Shape, ...] | list[Shape] | None = None,
    macro_subject_guard_stats: dict | None = None,
    phase15_face_fallback_stats: dict | None = None,
) -> Scene:
    canvas_area = max(float(scene.width * scene.height), 1.0)
    min_side = max(float(min(scene.width, scene.height)), 1.0)
    phase10_segmented = bool((scene.metadata.get("rinka_subject_segmentation") or {}).get("activated"))
    input_shapes = scene.shapes
    subject_base_removed = 0
    if phase10_segmented:
        input_shapes = [shape for shape in scene.shapes if "subject_base" not in _shape_tags(shape)]
        subject_base_removed = len(scene.shapes) - len(input_shapes)
    hierarchical, hierarchy_stats = _apply_opaque_hierarchy(input_shapes, opaque_hierarchy)
    zoned, zone_stats = _apply_opaque_zones(hierarchical, opaque_zones)
    pruned, structure_redundant_removed = _prune_structure_redundant_fragments(zoned, scene, opaque_zones)
    relaxed = [
        _relax_low_value_zone_fragment(
            _relax_low_value_character_fragment(shape, canvas_area, min_side),
            canvas_area,
            min_side,
        )
        for shape in pruned
    ]
    global_scores, global_scoring = _score_global_shapes(scene, relaxed, opaque_zones)
    cleaned, report = cleanup_minimal_shapes(
        relaxed,
        scene.width,
        scene.height,
        thin_aspect_ratio=5.0,
        thin_short_side_ratio=0.030,
        thin_max_area_ratio=0.010,
        thin_rectangle_short_side_ratio=0.020,
        thin_rectangle_aspect_ratio=3.2,
        thin_rectangle_max_area_ratio=0.012,
        thin_rectangle_max_importance=0.98,
        micro_area_ratio=0.00035,
        micro_max_importance=0.72,
        remove_duplicates=True,
        duplicate_overlap=0.94,
        duplicate_color_distance=7.0,
        merge_adjacent=True,
        merge_gap_ratio=0.010,
        merge_color_distance=9.0,
        merge_max_area_ratio=0.025,
        merge_max_hull_inflation=1.06,
        role_fragment_merge=True,
        role_fragment_gap_ratio=0.003,
        role_fragment_color_distance=5.0,
        role_fragment_max_area_ratio=0.014,
        role_fragment_max_combined_area_ratio=0.10,
        role_fragment_max_hull_inflation=1.06,
        simplify_polygons=True,
        simplify_epsilon_ratio=0.022,
        simplify_max_area_error=0.070,
        simplify_min_iou=0.965,
        promote_primitives=False,
        remove_isolated=True,
        isolated_max_area_ratio=0.0015,
        isolated_min_distance_ratio=0.060,
        isolated_max_importance=0.55,
        global_scores=global_scores,
        global_thin_enable=True,
        global_thin_max_score=global_scoring["low_value_threshold"],
        global_thin_short_side_ratio=0.035,
        global_thin_aspect_ratio=2.8,
        global_thin_max_area_ratio=0.014,
    )
    faceless, face_removed = _suppress_face_fragments(scene, cleaned, opaque_zones)
    anchored = faceless
    protected_anchors = [anchor for anchor in (protected_hair_anchor, protected_face_anchor) if anchor is not None]
    protected_anchors.extend(list(protected_macro_anchors or ()))
    if protected_anchors:
        protected_ids = {anchor.id for anchor in protected_anchors}
        anchored = [shape for shape in faceless if shape.id not in protected_ids] + protected_anchors
    consolidated, mass_merges = _consolidate_masses(anchored, min_side)
    outfit_consolidated, outfit_layer_merges = _consolidate_outfit_layers(consolidated, min_side)
    outfit_refined, outfit_refinement_merges = _refine_outfit_layers_once(scene, outfit_consolidated, min_side)
    outfit_layer_merges += outfit_refinement_merges
    hair_abstracted, hair_stats = _abstract_hair_planes(outfit_refined, min_side)
    outfit_blocked, outfit_block_stats = _consolidate_outfit_color_blocks(hair_abstracted, min_side)
    hand_abstracted, hand_stats = _abstract_hand_symbols(outfit_blocked, min_side)
    gesture_abstracted, gesture_stats = _abstract_gesture_shapes(hand_abstracted, min_side)
    micro_pruned, microdetail_removed = _prune_target_microdetails(scene, gesture_abstracted)
    compressed, background_removed = _compress_background(scene, micro_pruned)
    background_styled, result_background, background_geometry = _geometrize_background(
        scene,
        compressed,
        style=background_style,
        preserve_large_generic_cues=preset != "approved_reference",
        preserve_semantic_cues=preset != "approved_reference",
    )
    straight = [_curve_to_polygon(shape, curve_polygon_sides) for shape in background_styled]
    polished, render_inert_occluded_removed = _prune_render_inert_occluded_fragments(scene, straight)
    shadow_budget = 24 if target_max_shapes == 28 else None
    macro_shadow = _macro_priority_shadow(scene, polished, opaque_zones, budget=shadow_budget)
    capped, cap_removed, macro_priority = _final_shape_cap(scene, polished, target_max_shapes)
    macro_priority = {**macro_priority, "shadow": macro_shadow}

    metadata = dict(scene.metadata)
    metadata["shape_count_pre_target_style"] = len(scene.shapes)
    metadata["shape_count"] = len(capped)
    metadata["target_style"] = {
        "name": RINKA_REFERENCE_NAME,
        "version": RINKA_REFERENCE_VERSION,
        "curve_polygon_sides": max(4, int(curve_polygon_sides)),
        "target_max_shapes": target_max_shapes,
        "shape_count_before": len(scene.shapes),
        "shape_count_after": len(capped),
        "quality_metrics_scope": "pre_target_style",
        "opaque_hierarchy": {
            **(opaque_hierarchy.to_dict() if opaque_hierarchy is not None else {"enabled": False, "reason": "not_requested"}),
            **hierarchy_stats,
        },
        "opaque_zones": {
            **(opaque_zones.to_dict() if opaque_zones is not None else {"enabled": False, "reason": "not_requested"}),
            **zone_stats,
        },
        "phase10_subject_base_removed": subject_base_removed,
        "structure_redundant_removed": structure_redundant_removed,
        "global_scoring": global_scoring,
        "face_fragments_removed": face_removed,
        "phase12_anchor_guard": phase12_anchor_stats or {"enabled": False, "reason": "not_requested"},
        "macro_subject_guard": macro_subject_guard_stats or {"enabled": False, "reason": "not_requested"},
        "phase15_face_fallback": phase15_face_fallback_stats or {"enabled": False, "reason": "not_requested"},
        "mass_merges": mass_merges,
        "outfit_layer_merges": outfit_layer_merges,
        "hair_abstraction": hair_stats,
        "outfit_color_blocks": outfit_block_stats,
        "hand_abstraction": hand_stats,
        "microdetail_removed": microdetail_removed,
        "render_inert_occluded_removed": render_inert_occluded_removed,
        "gesture_abstraction": gesture_stats,
        "background_removed": background_removed,
        "background_geometry": {
            **background_geometry,
            "surviving_panels": sum(
                1 for shape in capped if (shape.semantic_type or "") == "target_geometric_background"
            ),
        },
        "preset": preset,
        "cap_removed": cap_removed,
        "macro_priority": macro_priority,
        "cleanup": report.to_dict(),
    }
    return Scene(
        width=scene.width,
        height=scene.height,
        background=result_background,
        shapes=capped,
        metadata=metadata,
    )



def _opaque_rescue_failure_gate(scene: Scene, rescue: OpaqueSubjectRescue) -> dict:
    canvas_area = max(float(scene.width * scene.height), 1.0)
    ratios = sorted(
        [
            _shape_metrics(shape)[0] / canvas_area
            for shape in scene.shapes
            if shape.fill_color is not None
        ],
        reverse=True,
    )
    largest = ratios[0] if ratios else 0.0
    second = ratios[1] if len(ratios) > 1 else 0.0
    accepted = (
        not bool(scene.metadata.get("subject_mode"))
        and float(rescue.border_dominant_fraction) >= 0.45
        and float(rescue.center_fill_ratio) >= 0.75
        and largest >= 0.25
        and second >= 0.22
    )
    return {
        "accepted": accepted,
        "largest_shape_ratio": round(float(largest), 6),
        "second_shape_ratio": round(float(second), 6),
        "center_fill_ratio": round(float(rescue.center_fill_ratio), 6),
        "border_dominant_fraction": round(float(rescue.border_dominant_fraction), 6),
    }

def _phase12_portrait_collapse_gate(segmentation: SubjectSegmentation, baseline_scene: Scene) -> dict:
    canvas_area = max(float(baseline_scene.width * baseline_scene.height), 1.0)
    ratios = sorted(
        [
            _shape_metrics(shape)[0] / canvas_area
            for shape in baseline_scene.shapes
            if shape.fill_color is not None and shape.shape_type != "line"
        ],
        reverse=True,
    )
    largest = ratios[0] if ratios else 0.0
    second = ratios[1] if len(ratios) > 1 else 0.0
    third = ratios[2] if len(ratios) > 2 else 0.0
    common = (
        segmentation.reason == "confidence_gate"
        and segmentation.rgba is not None
        and segmentation.mask is not None
        and not bool(baseline_scene.metadata.get("subject_mode"))
        and float(segmentation.confidence) >= 0.46
        and float(segmentation.border_dominant_fraction) >= 0.28
        and 0.50 <= float(segmentation.foreground_area_ratio) <= 0.78
        and float(segmentation.center_fill_ratio) >= 0.88
        and float(segmentation.border_leak_ratio) <= 0.45
    )
    three_slab = common and largest >= 0.22 and second >= 0.20 and third >= 0.14
    two_slab_poster = (
        common
        and float(segmentation.confidence) >= 0.50
        and float(segmentation.border_dominant_fraction) >= 0.35
        and 0.58 <= float(segmentation.foreground_area_ratio) <= 0.72
        and float(segmentation.center_fill_ratio) >= 0.92
        and float(segmentation.border_leak_ratio) <= 0.41
        and largest >= 0.235
        and second >= 0.235
    )
    accepted = three_slab or two_slab_poster
    variant = "three_slab" if three_slab else "two_slab_poster" if two_slab_poster else "none"
    return {
        "accepted": bool(accepted),
        "reason": "portrait_collapse_rescue" if accepted else "gate_rejected",
        "variant": variant,
        "largest_shape_ratio": round(float(largest), 6),
        "second_shape_ratio": round(float(second), 6),
        "third_shape_ratio": round(float(third), 6),
    }


def _phase13_lab_distance(color_a: tuple[int, int, int], color_b: tuple[int, int, int]) -> float:
    sample = np.asarray([[list(color_a), list(color_b)]], dtype=np.uint8)
    lab = cv2.cvtColor(sample, cv2.COLOR_RGB2LAB).astype(np.float32)[0]
    return float(np.linalg.norm(lab[0] - lab[1]))


def _phase13_rank_color_clusters(pixels: np.ndarray, *, bin_size: int = 16) -> list[dict]:
    if pixels.size == 0:
        return []
    values = np.asarray(pixels, dtype=np.uint8).reshape(-1, 3)
    quantized = (values // bin_size).astype(np.int16)
    keys, inverse, counts = np.unique(quantized, axis=0, return_inverse=True, return_counts=True)
    clusters: list[dict] = []
    for index, count in enumerate(counts):
        members = values[inverse == index]
        color = tuple(int(v) for v in np.median(members, axis=0))
        rgbf = np.asarray(color, dtype=np.float32)
        luma = float(0.2126 * rgbf[0] + 0.7152 * rgbf[1] + 0.0722 * rgbf[2])
        chroma = float(rgbf.max() - rgbf.min())
        clusters.append({
            "color": color,
            "count": int(count),
            "fraction": float(count / max(len(values), 1)),
            "luma": luma,
            "chroma": chroma,
        })
    clusters.sort(key=lambda item: item["count"], reverse=True)
    return clusters


def _phase13_pick_face_color(
    pixels: np.ndarray,
    background_rgb: tuple[int, int, int] | None,
) -> tuple[tuple[int, int, int], dict]:
    clusters = _phase13_rank_color_clusters(pixels)
    fallback = tuple(int(v) for v in np.median(pixels, axis=0))
    background = tuple(int(v) for v in (background_rgb or (255, 255, 255)))
    candidates = []
    for cluster in clusters:
        color = cluster["color"]
        sample = np.asarray([[list(color)]], dtype=np.uint8)
        ycrcb = cv2.cvtColor(sample, cv2.COLOR_RGB2YCrCb)[0, 0]
        yy, cr, cb = (int(v) for v in ycrcb)
        bg_distance = _phase13_lab_distance(color, background)
        warmth = float(color[0] - color[2])
        if not (88 <= yy and 136 <= cr <= 190 and 70 <= cb <= 150):
            continue
        if bg_distance < 12.0:
            continue
        score = cluster["fraction"] * 2.5 + max(warmth, 0.0) / 255.0 * 0.7
        candidates.append((score, cluster, bg_distance))
    if not candidates:
        return fallback, {"enabled": False, "reason": "face_cluster_fallback", "cluster_count": len(clusters)}
    _score, chosen, bg_distance = max(candidates, key=lambda item: item[0])
    return chosen["color"], {
        "enabled": True,
        "reason": "face_cluster",
        "cluster_count": len(clusters),
        "selected_fraction": round(float(chosen["fraction"]), 6),
        "background_distance": round(float(bg_distance), 3),
    }


def _phase13_pick_hair_colors(
    pixels: np.ndarray,
    background_rgb: tuple[int, int, int] | None,
    face_color: tuple[int, int, int] | None,
) -> tuple[tuple[int, int, int], tuple[int, int, int] | None, dict]:
    clusters = _phase13_rank_color_clusters(pixels)
    fallback = tuple(int(v) for v in np.median(pixels, axis=0))
    background = tuple(int(v) for v in (background_rgb or (255, 255, 255)))
    candidates = []
    for cluster in clusters:
        color = cluster["color"]
        bg_distance = _phase13_lab_distance(color, background)
        face_distance = _phase13_lab_distance(color, face_color) if face_color is not None else 99.0
        if cluster["luma"] < 132.0 or cluster["chroma"] > 92.0 or bg_distance < 18.0:
            continue
        neutrality = 1.0 - min(cluster["chroma"] / 92.0, 1.0)
        brightness = min(cluster["luma"] / 255.0, 1.0)
        separation = min(face_distance / 48.0, 1.0)
        score = cluster["fraction"] * 2.8 + neutrality * 0.55 + brightness * 0.25 + separation * 0.35
        candidates.append((score, cluster, face_distance, bg_distance))
    if not candidates:
        return fallback, None, {"enabled": False, "reason": "hair_cluster_fallback", "cluster_count": len(clusters)}
    candidates.sort(key=lambda item: item[0], reverse=True)
    primary_entry = candidates[0]
    if face_color is not None and primary_entry[2] < 13.0:
        separated = [item for item in candidates[1:] if item[2] >= 16.0 and item[1]["fraction"] >= 0.06]
        if separated:
            primary_entry = max(separated, key=lambda item: (item[1]["fraction"], item[2]))
    primary = primary_entry[1]["color"]
    secondary = None
    for _score, cluster, face_distance, _bg_distance in candidates:
        color = cluster["color"]
        if color == primary or cluster["fraction"] < 0.08:
            continue
        if _phase13_lab_distance(primary, color) < 10.0:
            continue
        if face_color is not None and face_distance < 10.0:
            continue
        secondary = color
        break
    return primary, secondary, {
        "enabled": True,
        "reason": "hair_cluster",
        "cluster_count": len(clusters),
        "primary_fraction": round(float(primary_entry[1]["fraction"]), 6),
        "face_distance": round(float(primary_entry[2]), 3),
        "background_distance": round(float(primary_entry[3]), 3),
        "secondary_color": list(secondary) if secondary is not None else None,
    }


def _phase12_face_anchor(
    segmentation: SubjectSegmentation,
    width: int,
    height: int,
) -> tuple[Shape | None, dict]:
    stats = {"enabled": False, "reason": "candidate_unavailable", "face_anchor_created": False}
    if segmentation.rgba is None or segmentation.mask is None:
        return None, stats
    rgb = cv2.resize(segmentation.rgba[:, :, :3], (width, height), interpolation=cv2.INTER_AREA)
    mask = cv2.resize(segmentation.mask.astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST) > 0
    ys, xs = np.where(mask)
    if xs.size < 64:
        stats["reason"] = "subject_too_small"
        return None, stats
    sx0, sy0, sx1, sy1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    sw, sh = max(sx1 - sx0, 1), max(sy1 - sy0, 1)
    # The face is expected near the central upper subject. Arms may touch the
    # image edges, so use a conservative central head window rather than the
    # whole subject bbox.
    hx0 = max(0, int(round(sx0 + sw * 0.22)))
    hx1 = min(width, int(round(sx0 + sw * 0.78)))
    hy0 = max(0, int(round(sy0 + sh * 0.03)))
    hy1 = min(height, int(round(sy0 + sh * 0.48)))
    if hx1 <= hx0 or hy1 <= hy0:
        stats["reason"] = "head_window_empty"
        return None, stats

    ycrcb = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    yy, cr, cb = cv2.split(ycrcb)
    skin = (yy >= 88) & (cr >= 138) & (cr <= 184) & (cb >= 72) & (cb <= 142) & mask
    window = np.zeros_like(mask, dtype=bool)
    window[hy0:hy1, hx0:hx1] = True
    skin &= window
    kernel = np.ones((3, 3), np.uint8)
    skin_u8 = cv2.morphologyEx(skin.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
    count, labels, comp_stats, centroids = cv2.connectedComponentsWithStats(skin_u8, 8)
    if count <= 1:
        stats["reason"] = "skin_component_missing"
        return None, stats

    expected = np.asarray([sx0 + sw * 0.50, sy0 + sh * 0.36], dtype=float)
    canvas_area = max(float(width * height), 1.0)
    candidates = []
    for index in range(1, count):
        area = int(comp_stats[index, cv2.CC_STAT_AREA])
        ratio = area / canvas_area
        if ratio < 0.0015 or ratio > 0.085:
            continue
        cx, cy = centroids[index]
        distance = float(np.linalg.norm(np.asarray([cx, cy]) - expected)) / max(float(min(width, height)), 1.0)
        if distance > 0.24:
            continue
        score = ratio * 3.0 - distance * 0.35
        candidates.append((score, area, index))
    if candidates:
        _score, area, index = max(candidates)
        component = labels == index
        cyx = np.argwhere(component)
        y0, x0 = cyx.min(axis=0)
        y1, x1 = cyx.max(axis=0) + 1
    else:
        # Some warm/blond poster portraits connect face, hair and arm into one
        # broad skin-like component. Under the already strict Phase 12 collapse
        # gate, synthesize a conservative central face slab from local warm
        # pixels instead of discarding the otherwise useful subject repair.
        fx0 = max(hx0, int(round(sx0 + sw * 0.39)))
        fx1 = min(hx1, int(round(sx0 + sw * 0.61)))
        fy0 = max(hy0, int(round(sy0 + sh * 0.18)))
        fy1 = min(hy1, int(round(sy0 + sh * 0.43)))
        fallback_window = np.zeros_like(mask, dtype=bool)
        fallback_window[fy0:fy1, fx0:fx1] = True
        loose_skin = (yy >= 88) & (cr >= 136) & (cr <= 190) & (cb >= 72) & (cb <= 148) & mask & fallback_window
        if int(loose_skin.sum()) < max(18, int(round(canvas_area * 0.0012))):
            stats["reason"] = "skin_component_gate"
            return None, stats
        component = loose_skin
        area = int(component.sum())
        y0, x0, y1, x1 = fy0, fx0, fy1, fx1
        stats["fallback_geometry"] = True
    bw, bh = max(int(x1 - x0), 1), max(int(y1 - y0), 1)
    if bw < 3 or bh < 3:
        stats["reason"] = "skin_component_too_thin"
        return None, stats
    pixels = rgb[component]
    fill, phase13_color_stats = _phase13_pick_face_color(pixels, segmentation.background_rgb)
    points = [
        (x0 + 0.18 * bw, y0),
        (x1 - 0.18 * bw, y0),
        (x1, y0 + 0.32 * bh),
        (x1 - 0.08 * bw, y1),
        (x0 + 0.08 * bw, y1),
        (x0, y0 + 0.32 * bh),
    ]
    shape = Shape(
        id=945001,
        shape_type="polygon",
        fill_color=fill,
        points=[(float(x), float(y)) for x, y in points],
        z_index=39950,
        importance=1.0,
        source_role="phase12_face_anchor",
        layer_name="foreground",
        semantic_type="character_face_anchor",
        character_part="face",
    )
    stats.update({
        "enabled": True,
        "reason": "face_anchor",
        "face_anchor_created": True,
        "face_anchor_area_ratio": round(float(area / canvas_area), 6),
        "face_anchor_color": list(fill),
        "face_anchor_bbox": [int(x0), int(y0), int(x1), int(y1)],
        "phase13_face_color": phase13_color_stats,
    })
    return shape, stats



def _phase12_hair_anchor(
    segmentation: SubjectSegmentation,
    width: int,
    height: int,
    face_anchor: Shape | None,
) -> tuple[Shape | None, dict]:
    stats = {"enabled": False, "reason": "candidate_unavailable", "hair_anchor_created": False}
    if segmentation.rgba is None or segmentation.mask is None:
        return None, stats
    rgb = cv2.resize(segmentation.rgba[:, :, :3], (width, height), interpolation=cv2.INTER_AREA)
    mask = cv2.resize(segmentation.mask.astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST) > 0
    ys, xs = np.where(mask)
    if xs.size < 64:
        stats["reason"] = "subject_too_small"
        return None, stats
    sx0, sy0, sx1, sy1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    sw, sh = max(sx1 - sx0, 1), max(sy1 - sy0, 1)
    hx0 = max(0, int(round(sx0 + sw * 0.28)))
    hx1 = min(width, int(round(sx0 + sw * 0.72)))
    hy0 = max(0, int(round(sy0 + sh * 0.01)))
    hy1 = min(height, int(round(sy0 + sh * 0.48)))
    window = np.zeros_like(mask, dtype=bool)
    window[hy0:hy1, hx0:hx1] = True

    rgbf = rgb.astype(np.float32)
    luma = 0.2126 * rgbf[:, :, 0] + 0.7152 * rgbf[:, :, 1] + 0.0722 * rgbf[:, :, 2]
    chroma = rgbf.max(axis=2) - rgbf.min(axis=2)
    background = np.asarray(segmentation.background_rgb or (255, 255, 255), dtype=np.float32)
    bg_distance = np.linalg.norm(rgbf - background[None, None, :], axis=2)
    candidate = mask & window & (luma >= 145.0) & (chroma <= 82.0) & (bg_distance >= 32.0)

    if face_anchor is not None:
        fx0, fy0, fx1, fy1 = _shape_bbox(face_anchor)
        pad_x = max(1, int(round((fx1 - fx0) * 0.08)))
        pad_y = max(1, int(round((fy1 - fy0) * 0.04)))
        candidate[max(0, int(fy0)-pad_y):min(height, int(fy1)+pad_y),
                  max(0, int(fx0)-pad_x):min(width, int(fx1)+pad_x)] = False

    candidate_u8 = cv2.morphologyEx(candidate.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    count, labels, comp_stats, centroids = cv2.connectedComponentsWithStats(candidate_u8, 8)
    canvas_area = max(float(width * height), 1.0)
    expected = np.asarray([sx0 + sw * 0.50, sy0 + sh * 0.24], dtype=float)
    selected: list[int] = []
    for index in range(1, count):
        area = int(comp_stats[index, cv2.CC_STAT_AREA])
        ratio = area / canvas_area
        if ratio < 0.0025 or ratio > 0.16:
            continue
        cx, cy = centroids[index]
        distance = float(np.linalg.norm(np.asarray([cx, cy]) - expected)) / max(float(min(width, height)), 1.0)
        if distance <= 0.30:
            selected.append(index)
    if not selected:
        stats["reason"] = "hair_component_gate"
        return None, stats

    combined = np.isin(labels, selected).astype(np.uint8)
    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        stats["reason"] = "hair_contour_missing"
        return None, stats
    points = np.vstack([contour.reshape(-1, 2) for contour in contours])
    hull = cv2.convexHull(points.astype(np.float32)).reshape(-1, 2)
    perimeter = cv2.arcLength(hull.reshape(-1, 1, 2), True)
    polygon = cv2.approxPolyDP(hull.reshape(-1, 1, 2), max(1.0, perimeter * 0.035), True).reshape(-1, 2)
    if len(polygon) < 4:
        polygon = hull
    hair_pixels = rgb[combined > 0]
    face_color = face_anchor.fill_color if face_anchor is not None else None
    fill, secondary_fill, phase13_color_stats = _phase13_pick_hair_colors(
        hair_pixels, segmentation.background_rgb, face_color
    )
    shape = Shape(
        id=945000,
        shape_type="polygon",
        fill_color=fill,
        points=[(float(x), float(y)) for x, y in polygon],
        z_index=39940,
        importance=1.0,
        source_role="phase12_hair_anchor",
        layer_name="foreground",
        semantic_type="character_hair_anchor",
        character_part="hair",
    )
    stats.update({
        "enabled": True,
        "reason": "hair_anchor",
        "hair_anchor_created": True,
        "hair_anchor_color": list(fill),
        "hair_anchor_secondary_color": list(secondary_fill) if secondary_fill is not None else None,
        "phase13_hair_color": phase13_color_stats,
        "hair_anchor_components": len(selected),
        "hair_anchor_vertices": len(shape.points),
    })
    return shape, stats


def _phase12_repair_quality_gate(
    subject_planes: SubjectPlaneResult,
    face_anchor: Shape | None,
    hair_anchor: Shape | None,
    width: int,
    height: int,
) -> dict:
    stats = {
        "accepted": False,
        "reason": "planes_disabled",
        "torso_anchor_count": 0,
        "subject_coverage_ratio": float(subject_planes.subject_coverage_ratio),
        "outside_subject_ratio": float(subject_planes.outside_subject_ratio),
    }
    if not subject_planes.enabled:
        return stats
    if face_anchor is None:
        stats["reason"] = "face_anchor_missing"
        return stats
    if hair_anchor is None:
        stats["reason"] = "hair_anchor_missing"
        return stats
    if subject_planes.subject_coverage_ratio < 0.64:
        stats["reason"] = "subject_coverage_low"
        return stats
    if subject_planes.outside_subject_ratio > 0.04:
        stats["reason"] = "outside_subject_high"
        return stats

    canvas_area = max(float(width * height), 1.0)
    torso_anchor_count = 0
    for shape in subject_planes.shapes:
        if shape.fill_color is None or shape.shape_type == "line":
            continue
        x0, y0, x1, y1 = _shape_bbox(shape)
        cx, cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
        area_ratio = _shape_metrics(shape)[0] / canvas_area
        if (
            width * 0.20 <= cx <= width * 0.80
            and height * 0.40 <= cy <= height * 0.90
            and area_ratio >= 0.015
        ):
            torso_anchor_count += 1
    stats["torso_anchor_count"] = torso_anchor_count
    if torso_anchor_count < 1:
        stats["reason"] = "torso_anchor_missing"
        return stats

    stats["accepted"] = True
    stats["reason"] = "anchors_present"
    return stats

def _phase10_segmentation_activation_gate(segmentation: SubjectSegmentation, legacy_gate: dict) -> dict:
    if not segmentation.enabled:
        return {"accepted": False, "reason": "segmentation_disabled"}
    if bool(legacy_gate.get("accepted")):
        return {"accepted": True, "reason": "legacy_failure_gate"}
    confident_subject = (
        float(segmentation.confidence) >= 0.62
        and float(segmentation.border_dominant_fraction) >= 0.55
        and float(segmentation.center_fill_ratio) >= 0.60
        and float(segmentation.border_leak_ratio) <= 0.20
    )
    dense_subject = (
        float(segmentation.confidence) >= 0.58
        and float(segmentation.border_dominant_fraction) >= 0.46
        and float(segmentation.foreground_area_ratio) >= 0.55
        and float(segmentation.center_fill_ratio) >= 0.90
        and float(segmentation.border_leak_ratio) <= 0.31
    )
    accepted = confident_subject or dense_subject
    reason = "confident_subject" if confident_subject else "dense_subject" if dense_subject else "gate_rejected"
    return {"accepted": accepted, "reason": reason}


def _phase10_protected_structure_shapes(shapes: list[Shape]) -> list[Shape]:
    protected: list[Shape] = []
    for shape in shapes:
        part = (shape.character_part or "unknown").lower()
        tags = _shape_tags(shape)
        if part in {"left_hand", "right_hand"}:
            protected.append(shape)
            continue
        if any(token in tags for token in ("prop", "sword", "weapon")):
            protected.append(shape)
    return protected


def minimalize_rinka_reference(
    image_or_path,
    level: int = 4,
    *,
    curve_polygon_sides: int = 6,
    enable_ai_free_subject_segmentation: bool = True,
    enable_macro_subject_guard: bool = False,
    preset: str = DEFAULT_RINKA_REFERENCE_PRESET,
    **config_overrides,
) -> Scene:
    preset = normalize_rinka_reference_preset(preset)
    enable_macro_subject_guard = bool(enable_macro_subject_guard or preset == "approved_reference")
    config = rinka_reference_config(level, **config_overrides)
    rescue = prepare_rinka_opaque_subject_input(image_or_path)
    segmentation = segment_subject_without_ai(image_or_path) if enable_ai_free_subject_segmentation else SubjectSegmentation(False, "disabled")
    rescue_gate = {"accepted": False, "reason": "candidate_disabled"}
    segmentation_gate = {"accepted": False, "reason": "candidate_disabled"}
    engine_input = image_or_path
    engine_config = config
    segmentation_activated = False
    rescue_activated = False
    phase12_rescue_activated = False

    candidate = segmentation if segmentation.enabled else rescue
    phase12_candidate_available = (
        segmentation.reason == "confidence_gate"
        and segmentation.rgba is not None
        and segmentation.mask is not None
    )
    phase12_rescue_gate = {"accepted": False, "reason": "candidate_disabled"}
    if (candidate.enabled and candidate.rgba is not None) or phase12_candidate_available:
        baseline_config = config.with_overrides(
            enable_rinka_macro_partition=False,
            rinka_macro_rescue_active=False,
        )
        baseline_scene = minimalize(image_or_path, baseline_config)
        if candidate.enabled and candidate.rgba is not None:
            gate_probe = OpaqueSubjectRescue(
                True,
                "phase10_subject_segmentation" if segmentation.enabled else rescue.reason,
                rgba=candidate.rgba,
                background_rgb=candidate.background_rgb,
                border_dominant_fraction=candidate.border_dominant_fraction,
                foreground_area_ratio=candidate.foreground_area_ratio,
                center_fill_ratio=candidate.center_fill_ratio,
            )
            rescue_gate = _opaque_rescue_failure_gate(baseline_scene, gate_probe)
        segmentation_gate = _phase10_segmentation_activation_gate(segmentation, rescue_gate)
        if phase12_candidate_available:
            phase12_rescue_gate = _phase12_portrait_collapse_gate(segmentation, baseline_scene)
        if segmentation_gate["accepted"] and segmentation.enabled:
            engine_input = segmentation.rgba
            engine_config = config.with_overrides(
                background_mode=("custom" if config.background_mode == "source" else config.background_mode),
                background_color=(segmentation.background_rgb if config.background_mode == "source" else config.background_color),
                enable_rinka_macro_partition=False,
                rinka_macro_rescue_active=False,
            )
            scene = minimalize(engine_input, engine_config)
            segmentation_activated = True
        elif phase12_rescue_gate["accepted"]:
            engine_input = segmentation.rgba
            engine_config = config.with_overrides(
                background_mode=("custom" if config.background_mode == "source" else config.background_mode),
                background_color=(segmentation.background_rgb if config.background_mode == "source" else config.background_color),
                enable_rinka_macro_partition=False,
                rinka_macro_rescue_active=False,
            )
            scene = minimalize(engine_input, engine_config)
            segmentation_activated = True
            phase12_rescue_activated = True
        elif rescue_gate["accepted"] and rescue.enabled and rescue.rgba is not None:
            engine_input = rescue.rgba
            engine_config = config.with_overrides(
                background_mode=("custom" if config.background_mode == "source" else config.background_mode),
                background_color=(rescue.background_rgb if config.background_mode == "source" else config.background_color),
                rinka_macro_rescue_active=True,
            )
            scene = minimalize(engine_input, engine_config)
            rescue_activated = True
        else:
            scene = baseline_scene
    else:
        scene = minimalize(engine_input, engine_config)

    subject_planes = SubjectPlaneResult(False, "segmentation_not_activated")
    protected_structure_shapes: list[Shape] = []
    replaced_structure_shapes = 0
    if segmentation_activated and segmentation.rgba is not None:
        subject_planes = build_subject_color_planes(
            segmentation.rgba,
            scene.width,
            scene.height,
            segmentation.background_rgb,
            max_colors=min(6, max(4, int(config.palette_colors))),
        )
        if subject_planes.enabled:
            protected_structure_shapes = _phase10_protected_structure_shapes(scene.shapes)
            replaced_structure_shapes = len(scene.shapes) - len(protected_structure_shapes)
            scene = Scene(
                width=scene.width,
                height=scene.height,
                background=scene.background,
                shapes=[*subject_planes.shapes, *protected_structure_shapes],
                metadata=dict(scene.metadata),
            )

    phase12_face_anchor = None
    phase12_hair_anchor = None
    phase12_anchor_stats = {"enabled": False, "reason": "rescue_not_activated", "face_anchor_created": False, "hair_anchor_created": False}
    phase12_quality_gate = {"accepted": False, "reason": "rescue_not_activated", "torso_anchor_count": 0}
    if phase12_rescue_activated:
        phase12_face_anchor, face_anchor_stats = _phase12_face_anchor(
            segmentation, scene.width, scene.height
        )
        phase12_hair_anchor, hair_anchor_stats = _phase12_hair_anchor(
            segmentation, scene.width, scene.height, phase12_face_anchor
        )
        phase12_quality_gate = _phase12_repair_quality_gate(
            subject_planes, phase12_face_anchor, phase12_hair_anchor, scene.width, scene.height
        )
        phase12_anchor_stats = {
            **face_anchor_stats,
            "hair": hair_anchor_stats,
            "hair_anchor_created": bool(hair_anchor_stats.get("hair_anchor_created")),
            "repair_quality_gate": phase12_quality_gate,
        }
        if not phase12_quality_gate["accepted"]:
            scene = baseline_scene
            engine_input = image_or_path
            engine_config = baseline_config
            segmentation_activated = False
            phase12_rescue_activated = False
            subject_planes = SubjectPlaneResult(False, "phase12_quality_fallback")
            protected_structure_shapes = []
            replaced_structure_shapes = 0
            phase12_face_anchor = None
            phase12_hair_anchor = None

    macro_segmentation = (
        phase15_subject_candidate(image_or_path, segmentation, rescue)
        if enable_macro_subject_guard
        else segmentation
    )
    approved_reference_planes = SubjectPlaneResult(False, "not_requested")
    if preset == "approved_reference" and macro_segmentation.rgba is not None:
        approved_reference_planes = build_subject_color_planes(
            macro_segmentation.rgba,
            scene.width,
            scene.height,
            macro_segmentation.background_rgb,
            max_colors=6,
            max_total_planes=10,
            fragment_area_ratio=0.0035,
            simplify_epsilon_ratio=0.052,
            preserve_light_component_tones=True,
            preserve_color_representatives=True,
            preserve_upper_gesture_representatives=True,
        )
        if approved_reference_planes.enabled:
            approved_protected = _phase10_protected_structure_shapes(scene.shapes)
            scene = Scene(
                width=scene.width,
                height=scene.height,
                background=scene.background,
                shapes=[*approved_reference_planes.shapes, *approved_protected],
                metadata=dict(scene.metadata),
            )

    macro_subject_guard = (
        build_macro_subject_guard(macro_segmentation, scene.width, scene.height)
        if enable_macro_subject_guard
        else MacroSubjectGuardResult(False, "not_requested")
    )
    if enable_macro_subject_guard and (phase12_face_anchor is None or preset == "approved_reference"):
        phase15_face_fallback = build_face_plane_fallback(
            macro_segmentation, macro_subject_guard, scene.width, scene.height
        )
    elif phase12_face_anchor is not None:
        phase15_face_fallback = FacePlaneFallbackResult(False, "phase12_face_anchor_active")
    else:
        phase15_face_fallback = FacePlaneFallbackResult(False, "not_requested")

    structure_reference_scene = scene
    scene.metadata["rinka_subject_segmentation"] = {
        **segmentation.to_dict(),
        "activated": segmentation_activated,
        "baseline_gate": rescue_gate,
        "activation_gate": segmentation_gate,
        "phase12_rescue_gate": phase12_rescue_gate,
        "phase12_repair_quality_gate": phase12_quality_gate,
        "phase12_rescue_activated": phase12_rescue_activated,
    }
    scene.metadata["rinka_subject_planes"] = {
        **subject_planes.to_dict(),
        "protected_structure_shapes": len(protected_structure_shapes),
        "replaced_structure_shapes": replaced_structure_shapes,
    }
    scene.metadata["rinka_approved_reference_planes"] = approved_reference_planes.to_dict()
    scene.metadata["rinka_opaque_subject_rescue"] = {
        **rescue.to_dict(),
        "activated": rescue_activated,
        "baseline_gate": rescue_gate,
        "superseded_by_subject_segmentation": segmentation_activated,
    }
    opaque_hierarchy = estimate_opaque_subject_hierarchy(engine_input, structure_reference_scene)
    opaque_zones = estimate_opaque_subject_zones(opaque_hierarchy, structure_reference_scene)
    structure_zones = estimate_structure_subject_zones(structure_reference_scene)
    subject_zones = opaque_zones if opaque_zones.enabled else structure_zones
    if preset == "approved_reference" and approved_reference_planes.enabled:
        return _apply_approved_reference_direct_style(
            scene,
            curve_polygon_sides=curve_polygon_sides,
            target_max_shapes=min(config.target_max_shapes, 22),
            protected_face_anchor=phase15_face_fallback.shape or phase12_face_anchor,
            protected_macro_anchors=macro_subject_guard.shapes,
            macro_subject_guard_stats={
                **macro_subject_guard.to_dict(),
                "candidate_reason": macro_segmentation.reason,
            },
            phase12_anchor_stats=phase12_anchor_stats,
            phase15_face_fallback_stats=phase15_face_fallback.to_dict(),
        )
    return apply_rinka_reference_style(
        scene,
        curve_polygon_sides=curve_polygon_sides,
        target_max_shapes=(min(config.target_max_shapes, 22) if preset == "approved_reference" else config.target_max_shapes),
        opaque_hierarchy=opaque_hierarchy,
        opaque_zones=subject_zones,
        background_style="geometric" if preset in {"geometric_poster", "approved_reference"} else "source",
        preset=preset,
        protected_face_anchor=phase12_face_anchor or phase15_face_fallback.shape,
        protected_hair_anchor=phase12_hair_anchor,
        phase12_anchor_stats=phase12_anchor_stats,
        protected_macro_anchors=macro_subject_guard.shapes,
        macro_subject_guard_stats={
            **macro_subject_guard.to_dict(),
            "candidate_reason": macro_segmentation.reason if enable_macro_subject_guard else "not_requested",
        },
        phase15_face_fallback_stats=phase15_face_fallback.to_dict(),
    )
