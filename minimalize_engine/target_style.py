from __future__ import annotations

from dataclasses import replace
from math import cos, pi, sin

import cv2
import numpy as np

from .analysis.shape_cleanup import cleanup_minimal_shapes
from .config import MinimalizeConfig
from .models import Scene, Shape
from .pipeline import minimalize
from .target_hierarchy import (
    OpaqueSubjectHierarchy,
    OpaqueSubjectZones,
    dominant_shape_zone,
    estimate_opaque_subject_hierarchy,
    estimate_opaque_subject_zones,
    shape_subject_overlap,
)


RINKA_REFERENCE_NAME = "rinka_reference"
RINKA_REFERENCE_VERSION = "phase4"


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
    if "opaque_zone:hair:" in tags or "target_zone_hair_fragment" in tags:
        return "hair"
    if "opaque_zone:arm:" in tags or "target_zone_arm_fragment" in tags:
        return "hand"
    if "opaque_zone:clothing:" in tags or "target_zone_clothing_fragment" in tags:
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



def _opaque_zone_name(shape: Shape) -> str | None:
    role = shape.source_role or ""
    marker = "opaque_zone:"
    if marker in role:
        tail = role.split(marker, 1)[1]
        return tail.split(":", 1)[0] or None
    semantic = shape.semantic_type or ""
    prefix = "target_zone_"
    if semantic.startswith(prefix) and semantic.endswith("_fragment"):
        return semantic[len(prefix):-len("_fragment")]
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
        "inferred_clothing_shapes": 0,
    }
    if reference is None:
        return refinements, stats

    head_box = zones.zone_bbox("head")
    if head_box is not None:
        hx0, _hy0, hx1, _hy1 = head_box
        head_w = max(float(hx1 - hx0), 1.0)
        head_area = max(float((hx1 - hx0) * (_hy1 - _hy0)), 1.0)
        ref_luma = _color_luma(reference)
        for shape, zone in assignments:
            if zone != "head" or shape.id == face_carrier_id or shape.fill_color is None:
                continue
            area = _shape_metrics(shape)[0]
            bx0, _by0, bx1, _by1 = _shape_bbox(shape)
            width_ratio = max(0.0, bx1 - bx0) / head_w
            if (
                area >= head_area * 0.020
                and width_ratio <= 0.72
                and _color_distance(shape.fill_color, reference) >= 42.0
                and ref_luma - _color_luma(shape.fill_color) >= 32.0
            ):
                refinements[shape.id] = "hair"
                stats["inferred_hair_shapes"] += 1

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
        "inferred_clothing_shapes": 0,
    }
    if zones is None or not zones.enabled:
        stats["neutral_shapes"] = len(shapes)
        return shapes, stats

    assignments: list[tuple[Shape, str]] = []
    for shape in shapes:
        zone = dominant_shape_zone(shape, zones)
        if zone is not None:
            assignments.append((shape, zone))
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
        elif zone == "head" and "hair" in tags:
            refined = "hair"
        elif zone in {"torso", "legs"} and any(token in tags for token in garment_tokens):
            refined = "clothing"
        elif zone in {"left_arm", "right_arm"}:
            refined = "arm"
        elif zone == "legs":
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
        out.append(replace(
            shape,
            importance=max(float(shape.importance), floor),
            source_role=f"opaque_zone:{refined}:{shape.source_role}",
            layer_name="foreground",
        ))
        stats["zone_shapes"] += 1
        stats[f"{refined}_shapes"] += 1
    return out, stats

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


def _suppress_face_fragments(
    scene: Scene,
    shapes: list[Shape],
    opaque_zones: OpaqueSubjectZones | None = None,
) -> tuple[list[Shape], int]:
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
    if len(inside) < 2:
        return shapes, 0
    carrier = max(inside, key=lambda s: _shape_metrics(s)[0])
    carrier_area = _shape_metrics(carrier)[0]
    if carrier_area < face_area * 0.08:
        return shapes, 0
    remove_ids: set[int] = set()
    for shape in inside:
        if shape.id == carrier.id or float(shape.importance) >= 0.90:
            continue
        area = _shape_metrics(shape)[0]
        if area <= max(face_area * 0.16, carrier_area * 0.65):
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
    if kind_a != kind_b or kind_a == "prop":
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


def _final_shape_cap(scene: Scene, shapes: list[Shape], target_max_shapes: int | None) -> tuple[list[Shape], int]:
    if target_max_shapes is None or target_max_shapes <= 0 or len(shapes) <= target_max_shapes:
        return shapes, 0
    canvas_area = max(float(scene.width * scene.height), 1.0)
    def score(shape: Shape) -> float:
        area_ratio = _shape_metrics(shape)[0] / canvas_area
        value = max(0.0, min(1.0, float(shape.importance))) * 0.58
        value += min(1.0, area_ratio / 0.025) * 0.32
        if (shape.layer_name or "").lower() == "foreground":
            value += 0.08
        if _target_mass_kind(shape) in {"hair", "hand", "garment", "prop"}:
            value += 0.08
        tags = _shape_tags(shape)
        if "opaque_subject" in tags:
            value += 0.14
        elif "opaque_background" in tags:
            value -= 0.04
        zone = _opaque_zone_name(shape)
        if zone in {"head", "hair", "torso", "clothing"}:
            value += 0.06
        elif zone in {"arm", "leg"}:
            value += 0.03
        return value
    ranked = sorted(shapes, key=score, reverse=True)
    keep_ids = {s.id for s in ranked[:target_max_shapes]}
    capped = [s for s in shapes if s.id in keep_ids]
    return capped, len(shapes) - len(capped)


def apply_rinka_reference_style(
    scene: Scene,
    *,
    curve_polygon_sides: int = 6,
    target_max_shapes: int | None = None,
    opaque_hierarchy: OpaqueSubjectHierarchy | None = None,
    opaque_zones: OpaqueSubjectZones | None = None,
) -> Scene:
    canvas_area = max(float(scene.width * scene.height), 1.0)
    min_side = max(float(min(scene.width, scene.height)), 1.0)
    hierarchical, hierarchy_stats = _apply_opaque_hierarchy(scene.shapes, opaque_hierarchy)
    zoned, zone_stats = _apply_opaque_zones(hierarchical, opaque_zones)
    relaxed = [
        _relax_low_value_zone_fragment(
            _relax_low_value_character_fragment(shape, canvas_area, min_side),
            canvas_area,
            min_side,
        )
        for shape in zoned
    ]
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
    )
    faceless, face_removed = _suppress_face_fragments(scene, cleaned, opaque_zones)
    consolidated, mass_merges = _consolidate_masses(faceless, min_side)
    compressed, background_removed = _compress_background(scene, consolidated)
    straight = [_curve_to_polygon(shape, curve_polygon_sides) for shape in compressed]
    capped, cap_removed = _final_shape_cap(scene, straight, target_max_shapes)

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
        "face_fragments_removed": face_removed,
        "mass_merges": mass_merges,
        "background_removed": background_removed,
        "cap_removed": cap_removed,
        "cleanup": report.to_dict(),
    }
    return Scene(
        width=scene.width,
        height=scene.height,
        background=scene.background,
        shapes=capped,
        metadata=metadata,
    )


def minimalize_rinka_reference(
    image_or_path,
    level: int = 4,
    *,
    curve_polygon_sides: int = 6,
    **config_overrides,
) -> Scene:
    config = rinka_reference_config(level, **config_overrides)
    scene = minimalize(image_or_path, config)
    opaque_hierarchy = estimate_opaque_subject_hierarchy(image_or_path, scene)
    opaque_zones = estimate_opaque_subject_zones(opaque_hierarchy, scene)
    return apply_rinka_reference_style(
        scene,
        curve_polygon_sides=curve_polygon_sides,
        target_max_shapes=config.target_max_shapes,
        opaque_hierarchy=opaque_hierarchy,
        opaque_zones=opaque_zones,
    )
