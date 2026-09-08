from __future__ import annotations

from dataclasses import replace
from math import cos, pi, sin

from .analysis.shape_cleanup import cleanup_minimal_shapes
from .config import MinimalizeConfig
from .models import Scene, Shape
from .pipeline import minimalize


RINKA_REFERENCE_NAME = "rinka_reference"
RINKA_REFERENCE_VERSION = "phase1"


_TARGET_MAX_SHAPES = {
    1: 90,
    2: 70,
    3: 55,
    4: 38,
    5: 24,
}

_TARGET_EPSILON = {
    1: 0.010,
    2: 0.014,
    3: 0.020,
    4: 0.032,
    5: 0.050,
}


def rinka_reference_config(level: int = 4, **overrides) -> MinimalizeConfig:
    """Return an opt-in config aimed at the formal Rinka Reference target.

    The stable ``from_level`` presets remain unchanged. This profile deliberately
    spends fewer shapes on local detail, disables structural line extraction,
    keeps dedicated face primitives off, and prevents quality retry from adding
    detail back after the target-style simplification decisions.
    """
    base = MinimalizeConfig.from_level(level)
    profile = {
        "palette_colors": min(base.palette_colors, 6),
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
            base.cleanup_simplify_epsilon_ratio, 0.018
        ),
        "cleanup_simplify_max_area_error": max(
            base.cleanup_simplify_max_area_error, 0.060
        ),
        "cleanup_simplify_min_iou": min(base.cleanup_simplify_min_iou, 0.975),
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
    """Return area, short side, long side and aspect ratio without raster work."""
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


def _character_fragment_kind(shape: Shape) -> str | None:
    tags = " ".join(
        (
            shape.semantic_type or "",
            shape.character_part or "",
            shape.source_role or "",
        )
    ).lower()
    if "face" in tags or "eye" in tags or "mouth" in tags:
        return None
    if "hand" in tags or "finger" in tags:
        return "hand"
    if "hair" in tags:
        return "hair"
    if any(token in tags for token in ("accessory", "ruffle", "lace", "trim")):
        return "outfit_detail"
    return None


def _relax_low_value_character_fragment(
    shape: Shape,
    canvas_area: float,
    min_side: float,
) -> Shape:
    """Let only small target-style character fragments enter generic cleanup.

    Stable cleanup intentionally blanket-protects hair and hands. The Rinka
    target wants major hair flow / gesture preserved while fine strands,
    fingers, lace and similar fragments can disappear. We therefore remove the
    protection metadata only from small/low-value fragments. Large or important
    character geometry stays protected exactly as before.
    """
    kind = _character_fragment_kind(shape)
    if kind is None:
        return shape

    area, short, _long, aspect = _shape_metrics(shape)
    area_ratio = area / max(canvas_area, 1.0)
    short_limit = max(1.5, min_side * 0.030)
    thin = short <= short_limit and aspect >= 3.2

    micro_limit = {
        "hand": 0.0040,
        "hair": 0.0030,
        "outfit_detail": 0.0060,
    }[kind]
    importance_limit = {
        "hand": 0.88,
        "hair": 0.86,
        "outfit_detail": 0.92,
    }[kind]

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


def _curve_to_polygon(shape: Shape, sides: int = 8) -> Shape:
    """Replace circles/ellipses with straight-edged polygons for target style."""
    if shape.shape_type not in {"circle", "ellipse"}:
        return shape
    cx = float(shape.cx or 0.0)
    cy = float(shape.cy or 0.0)
    rx = max(float(shape.rx or 0.0), 0.0)
    ry = max(float(shape.ry if shape.ry is not None else rx), 0.0)
    if rx <= 0.0 or ry <= 0.0:
        return shape
    n = max(4, int(sides))
    points = [
        (
            cx + rx * cos(-pi / 2.0 + 2.0 * pi * i / n),
            cy + ry * sin(-pi / 2.0 + 2.0 * pi * i / n),
        )
        for i in range(n)
    ]
    return replace(
        shape,
        shape_type="polygon",
        points=points,
        x=None,
        y=None,
        width=None,
        height=None,
        cx=None,
        cy=None,
        rx=None,
        ry=None,
    )


def apply_rinka_reference_style(
    scene: Scene,
    *,
    curve_polygon_sides: int = 8,
) -> Scene:
    """Apply Phase-1 Rinka Reference simplification to an existing scene.

    This is intentionally an opt-in post-process. It preserves the stable engine
    baseline while allowing target-style work to be tested and tightened
    independently.
    """
    canvas_area = max(float(scene.width * scene.height), 1.0)
    min_side = max(float(min(scene.width, scene.height)), 1.0)
    relaxed = [
        _relax_low_value_character_fragment(shape, canvas_area, min_side)
        for shape in scene.shapes
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
        simplify_epsilon_ratio=0.020,
        simplify_max_area_error=0.060,
        simplify_min_iou=0.970,
        promote_primitives=False,
        remove_isolated=True,
        isolated_max_area_ratio=0.0015,
        isolated_min_distance_ratio=0.060,
        isolated_max_importance=0.55,
    )
    straight = [_curve_to_polygon(shape, curve_polygon_sides) for shape in cleaned]

    metadata = dict(scene.metadata)
    metadata["shape_count_pre_target_style"] = len(scene.shapes)
    metadata["shape_count"] = len(straight)
    metadata["target_style"] = {
        "name": RINKA_REFERENCE_NAME,
        "version": RINKA_REFERENCE_VERSION,
        "curve_polygon_sides": max(4, int(curve_polygon_sides)),
        "shape_count_before": len(scene.shapes),
        "shape_count_after": len(straight),
        "quality_metrics_scope": "pre_target_style",
        "cleanup": report.to_dict(),
    }
    return Scene(
        width=scene.width,
        height=scene.height,
        background=scene.background,
        shapes=straight,
        metadata=metadata,
    )


def minimalize_rinka_reference(
    image_or_path,
    level: int = 4,
    *,
    curve_polygon_sides: int = 8,
    **config_overrides,
) -> Scene:
    """Minimalize an image with the opt-in Rinka Reference Phase-1 profile."""
    config = rinka_reference_config(level, **config_overrides)
    scene = minimalize(image_or_path, config)
    return apply_rinka_reference_style(
        scene,
        curve_polygon_sides=curve_polygon_sides,
    )
