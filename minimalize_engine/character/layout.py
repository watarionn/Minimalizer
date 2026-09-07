from __future__ import annotations

from dataclasses import dataclass
import math

import cv2
import numpy as np

from ..models import Shape
from .models import CharacterStructure
from .part_types import CharacterPartType


@dataclass
class CharacterLayoutPlan:
    enabled: bool
    preset: str
    scale: float
    translate_x: float
    translate_y: float
    source_subject_bbox: tuple[float, float, float, float]
    source_shape_bbox: tuple[float, float, float, float]
    transformed_shape_bbox: tuple[float, float, float, float]
    visual_center_before: tuple[float, float]
    visual_center_after: tuple[float, float]
    target_visual_center: tuple[float, float]
    top_anchor_before: float
    top_anchor_after: float
    target_top_y: float
    bottom_anchor_before: float
    bottom_anchor_after: float
    target_bottom_y: float
    head_top_before: float
    head_top_after: float
    ground_before: float
    ground_after: float
    pose_bias_x: float
    headroom_ratio: float
    footroom_ratio: float
    left_margin_ratio: float
    right_margin_ratio: float
    fit_limited: bool
    confidence: float

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "preset": self.preset,
            "source_coordinate_space": "analysis_pre_layout",
            "output_coordinate_space": "scene",
            "scale": self.scale,
            "translate_x": self.translate_x,
            "translate_y": self.translate_y,
            "source_subject_bbox": list(self.source_subject_bbox),
            "source_shape_bbox": list(self.source_shape_bbox),
            "transformed_shape_bbox": list(self.transformed_shape_bbox),
            "visual_center_before": list(self.visual_center_before),
            "visual_center_after": list(self.visual_center_after),
            "target_visual_center": list(self.target_visual_center),
            "top_anchor_before": self.top_anchor_before,
            "top_anchor_after": self.top_anchor_after,
            "target_top_y": self.target_top_y,
            "bottom_anchor_before": self.bottom_anchor_before,
            "bottom_anchor_after": self.bottom_anchor_after,
            "target_bottom_y": self.target_bottom_y,
            "head_top_before": self.head_top_before,
            "head_top_after": self.head_top_after,
            "ground_before": self.ground_before,
            "ground_after": self.ground_after,
            "pose_bias_x": self.pose_bias_x,
            "headroom_ratio": self.headroom_ratio,
            "footroom_ratio": self.footroom_ratio,
            "left_margin_ratio": self.left_margin_ratio,
            "right_margin_ratio": self.right_margin_ratio,
            "fit_limited": self.fit_limited,
            "confidence": self.confidence,
        }


def _shape_bounds(shape: Shape) -> tuple[float, float, float, float] | None:
    if shape.shape_type == "rectangle":
        if None in {shape.x, shape.y, shape.width, shape.height}:
            return None
        return (
            float(shape.x),
            float(shape.y),
            float(shape.x + shape.width),
            float(shape.y + shape.height),
        )

    if shape.shape_type in {"circle", "ellipse"}:
        if None in {shape.cx, shape.cy, shape.rx, shape.ry}:
            return None
        return (
            float(shape.cx - shape.rx),
            float(shape.cy - shape.ry),
            float(shape.cx + shape.rx),
            float(shape.cy + shape.ry),
        )

    if not shape.points:
        return None

    xs = [p[0] for p in shape.points]
    ys = [p[1] for p in shape.points]
    half = max(0.0, shape.stroke_width * 0.5)
    return (
        float(min(xs) - half),
        float(min(ys) - half),
        float(max(xs) + half),
        float(max(ys) + half),
    )


def shapes_bounds(
    shapes: list[Shape],
) -> tuple[float, float, float, float]:
    bounds = [b for s in shapes if (b := _shape_bounds(s)) is not None]
    if not bounds:
        return (0.0, 0.0, 1.0, 1.0)
    return (
        min(b[0] for b in bounds),
        min(b[1] for b in bounds),
        max(b[2] for b in bounds),
        max(b[3] for b in bounds),
    )


def _weighted_visual_center(
    structure: CharacterStructure,
) -> tuple[float, float]:
    weights = {
        CharacterPartType.FACE: 3.1,
        CharacterPartType.HEAD: 2.4,
        CharacterPartType.TORSO: 2.8,
        CharacterPartType.OUTFIT: 1.4,
        CharacterPartType.LEFT_ARM: 0.85,
        CharacterPartType.RIGHT_ARM: 0.85,
        CharacterPartType.LEFT_LEG: 0.90,
        CharacterPartType.RIGHT_LEG: 0.90,
        CharacterPartType.PROP: 1.15,
        CharacterPartType.HAIR: 1.05,
    }

    points = []
    for part in structure.parts:
        weight = weights.get(part.part_type, 0.0)
        if weight <= 0.0:
            continue
        weight *= max(0.25, part.confidence)
        points.append((part.centroid[0], part.centroid[1], weight))

    if not points:
        x, y, w, h = structure.subject_bbox
        return (x + w / 2.0, y + h * 0.45)

    total = sum(p[2] for p in points)
    return (
        float(sum(p[0] * p[2] for p in points) / total),
        float(sum(p[1] * p[2] for p in points) / total),
    )


def _head_top(structure: CharacterStructure) -> float:
    face = structure.first_part(CharacterPartType.FACE)
    head = structure.first_part(CharacterPartType.HEAD)
    if head is not None:
        return float(head.bbox[1])
    if face is not None:
        return float(face.bbox[1] - face.bbox[3] * 0.20)
    return float(structure.subject_bbox[1])


def _ground_anchor(structure: CharacterStructure) -> float:
    candidates = []
    for part_type in [
        CharacterPartType.LEFT_LEG,
        CharacterPartType.RIGHT_LEG,
        CharacterPartType.LEFT_SHOE,
        CharacterPartType.RIGHT_SHOE,
    ]:
        for part in structure.get_parts(part_type):
            x, y, w, h = part.bbox
            candidates.append(float(y + h))

    if candidates:
        return max(candidates)
    x, y, w, h = structure.subject_bbox
    return float(y + h)


def _pose_reach_bias(
    structure: CharacterStructure,
) -> float:
    """
    Positive output means "give more room on the left", so the visual core
    should move slightly right. Raised hands and props are weighted more than
    long hair because they define the reading direction of the pose.
    """
    sx, sy, sw, sh = structure.subject_bbox
    torso = structure.first_part(CharacterPartType.TORSO)
    core_x = (
        torso.centroid[0]
        if torso is not None
        else float(structure.metadata.get("body_axis_x", sx + sw / 2.0))
    )

    left_reach = 0.0
    right_reach = 0.0
    for part_type, weight in [
        (CharacterPartType.LEFT_ARM, 1.0),
        (CharacterPartType.RIGHT_ARM, 1.0),
        (CharacterPartType.PROP, 1.25),
        (CharacterPartType.HAIR, 0.28),
    ]:
        for part in structure.get_parts(part_type):
            x, y, w, h = part.bbox
            left_reach = max(left_reach, max(0.0, core_x - x) * weight)
            right_reach = max(
                right_reach,
                max(0.0, (x + w) - core_x) * weight,
            )

    denom = max(sw, 1.0)
    return float(np.clip((left_reach - right_reach) / denom, -0.60, 0.60))


def _clamp(value: float, low: float, high: float) -> float:
    if low > high:
        return (low + high) / 2.0
    return min(max(value, low), high)


def plan_character_layout(
    structure: CharacterStructure,
    shapes: list[Shape],
    width: int,
    height: int,
    *,
    headroom_ratio: float = 0.055,
    footroom_ratio: float = 0.040,
    side_margin_ratio: float = 0.050,
    visual_center_strength: float = 0.72,
    pose_bias_strength: float = 0.060,
    max_scale_up: float = 1.10,
    safety_margin_ratio: float = 0.012,
) -> CharacterLayoutPlan:
    width = max(1, int(width))
    height = max(1, int(height))

    sx, sy, sw, sh = structure.subject_bbox
    source_subject_bbox = (float(sx), float(sy), float(sx + sw), float(sy + sh))
    shape_bbox = shapes_bounds(shapes)
    bx0, by0, bx1, by1 = shape_bbox
    bw = max(1.0, bx1 - bx0)
    bh = max(1.0, by1 - by0)

    visual_before = _weighted_visual_center(structure)
    head_before = _head_top(structure)
    ground_before = _ground_anchor(structure)
    pose_reach = _pose_reach_bias(structure)

    preset = structure.preset
    full_body = preset in {"full_body", "chibi"} and (
        structure.first_part(CharacterPartType.LEFT_LEG) is not None
        or structure.first_part(CharacterPartType.RIGHT_LEG) is not None
    )

    if preset == "portrait":
        target_top_ratio = max(0.035, headroom_ratio * 0.85)
        target_bottom_ratio = max(0.035, footroom_ratio * 0.90)
        side_ratio = side_margin_ratio * 0.90
    elif preset == "upper_body":
        target_top_ratio = headroom_ratio
        target_bottom_ratio = max(0.035, footroom_ratio)
        side_ratio = side_margin_ratio
    else:
        target_top_ratio = headroom_ratio
        target_bottom_ratio = footroom_ratio
        side_ratio = side_margin_ratio

    target_top_y = target_top_ratio * height
    target_bottom_y = height * (1.0 - target_bottom_ratio)

    # "Headroom" is the breathing room above the whole pose, not literally the
    # anatomical head. Raised hands, hats, ears and weapons should stay inside
    # the same deliberate top margin instead of forcing the head itself to 5%.
    top_anchor_before = by0
    bottom_anchor_before = by1

    safety = safety_margin_ratio
    left_safety = width * max(safety, side_ratio * 0.42)
    right_safety = width * max(safety, side_ratio * 0.42)
    top_safety = height * safety
    bottom_safety = height * safety

    scale_w = (width * (1.0 - side_ratio * 2.0)) / bw
    scale_h_fit = (height * (1.0 - safety * 2.0)) / bh
    scale_v = (
        target_bottom_y - target_top_y
    ) / max(bottom_anchor_before - top_anchor_before, 1.0)

    requested_scale = min(scale_w, scale_h_fit, scale_v, max_scale_up)
    scale = float(np.clip(requested_scale, 0.45, max_scale_up))
    fit_limited = scale < scale_v - 1e-4

    # Pose-aware horizontal breathing room. A left-reaching arm/prop shifts the
    # visual core right, and vice versa.
    pose_bias_px = (
        float(np.clip(pose_reach * pose_bias_strength, -0.045, 0.045))
        * width
    )
    target_visual_x = width * 0.5 + pose_bias_px

    # Blend between preserving the original visual-center position and
    # normalization. Strength 1.0 fully recenters the weighted body core.
    original_visual_x = visual_before[0]
    desired_x = (
        original_visual_x * (1.0 - visual_center_strength)
        + target_visual_x * visual_center_strength
    )
    tx_desired = desired_x - visual_before[0] * scale

    tx_low = left_safety - bx0 * scale
    tx_high = (width - right_safety) - bx1 * scale
    tx = _clamp(tx_desired, tx_low, tx_high)

    ty_top = target_top_y - top_anchor_before * scale
    ty_bottom = target_bottom_y - bottom_anchor_before * scale
    # When width limits scale, distribute the extra vertical breathing room
    # instead of pinning the pose to the top edge. Full-body poses slightly
    # favor ground contact.
    if full_body:
        ty_desired = ty_top * 0.44 + ty_bottom * 0.56
    else:
        ty_desired = ty_top * 0.58 + ty_bottom * 0.42

    ty_low = top_safety - by0 * scale
    ty_high = (height - bottom_safety) - by1 * scale
    ty = _clamp(ty_desired, ty_low, ty_high)

    transformed = (
        bx0 * scale + tx,
        by0 * scale + ty,
        bx1 * scale + tx,
        by1 * scale + ty,
    )
    visual_after = (
        visual_before[0] * scale + tx,
        visual_before[1] * scale + ty,
    )
    top_anchor_after = top_anchor_before * scale + ty
    bottom_anchor_after = bottom_anchor_before * scale + ty
    head_after = head_before * scale + ty
    ground_after = ground_before * scale + ty

    left_margin = transformed[0] / width
    right_margin = 1.0 - transformed[2] / width

    # Confidence reflects whether the anchors existed and how little clamping
    # was needed. It is diagnostic, not a quality gate.
    anchors = 0.55
    if structure.first_part(CharacterPartType.HEAD) is not None:
        anchors += 0.15
    if structure.first_part(CharacterPartType.TORSO) is not None:
        anchors += 0.15
    if full_body:
        anchors += 0.10
    if not fit_limited:
        anchors += 0.05

    return CharacterLayoutPlan(
        enabled=True,
        preset=preset,
        scale=scale,
        translate_x=float(tx),
        translate_y=float(ty),
        source_subject_bbox=source_subject_bbox,
        source_shape_bbox=shape_bbox,
        transformed_shape_bbox=transformed,
        visual_center_before=visual_before,
        visual_center_after=visual_after,
        target_visual_center=(target_visual_x, height * 0.48),
        top_anchor_before=top_anchor_before,
        top_anchor_after=top_anchor_after,
        target_top_y=target_top_y,
        bottom_anchor_before=bottom_anchor_before,
        bottom_anchor_after=bottom_anchor_after,
        target_bottom_y=target_bottom_y,
        head_top_before=head_before,
        head_top_after=head_after,
        ground_before=ground_before,
        ground_after=ground_after,
        pose_bias_x=pose_bias_px,
        headroom_ratio=top_anchor_after / height,
        footroom_ratio=1.0 - bottom_anchor_after / height,
        left_margin_ratio=left_margin,
        right_margin_ratio=right_margin,
        fit_limited=fit_limited,
        confidence=float(np.clip(anchors, 0.0, 1.0)),
    )


def transform_shape(
    shape: Shape,
    scale: float,
    translate_x: float,
    translate_y: float,
) -> Shape:
    if shape.shape_type == "rectangle":
        shape.x = translate_x + float(shape.x or 0.0) * scale
        shape.y = translate_y + float(shape.y or 0.0) * scale
        shape.width = float(shape.width or 0.0) * scale
        shape.height = float(shape.height or 0.0) * scale
    elif shape.shape_type in {"circle", "ellipse"}:
        shape.cx = translate_x + float(shape.cx or 0.0) * scale
        shape.cy = translate_y + float(shape.cy or 0.0) * scale
        shape.rx = float(shape.rx or 0.0) * scale
        shape.ry = float(shape.ry or 0.0) * scale
    else:
        shape.points = [
            (
                translate_x + x * scale,
                translate_y + y * scale,
            )
            for x, y in shape.points
        ]

    shape.stroke_width *= scale
    return shape


def apply_character_layout(
    shapes: list[Shape],
    plan: CharacterLayoutPlan,
) -> list[Shape]:
    if not plan.enabled:
        return shapes
    for shape in shapes:
        transform_shape(
            shape,
            plan.scale,
            plan.translate_x,
            plan.translate_y,
        )
    return shapes


def layout_metrics(
    plan: CharacterLayoutPlan,
    width: int,
    height: int,
) -> dict:
    center_error = abs(
        plan.visual_center_after[0] - plan.target_visual_center[0]
    ) / max(width, 1)
    top_error = abs(
        plan.top_anchor_after - plan.target_top_y
    ) / max(height, 1)
    bottom_error = abs(
        plan.bottom_anchor_after - plan.target_bottom_y
    ) / max(height, 1)
    bx0, by0, bx1, by1 = plan.transformed_shape_bbox
    clipped = (
        bx0 < -1e-3
        or by0 < -1e-3
        or bx1 > width + 1e-3
        or by1 > height + 1e-3
    )
    return {
        "center_error": float(center_error),
        "top_error": float(top_error),
        "bottom_error": float(bottom_error),
        "head_error": float(top_error),
        "ground_error": float(bottom_error),
        "clipped": bool(clipped),
        "headroom_ratio": float(plan.headroom_ratio),
        "footroom_ratio": float(plan.footroom_ratio),
        "left_margin_ratio": float(plan.left_margin_ratio),
        "right_margin_ratio": float(plan.right_margin_ratio),
        "scale": float(plan.scale),
    }


def render_character_layout_preview(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
    plan: CharacterLayoutPlan,
) -> np.ndarray:
    """
    Warp the source subject itself for a debug-only preview.

    This does not affect the SVG output. It lets corpus inspection verify
    headroom, ground contact and pose-aware horizontal breathing room.
    """
    h, w = image_rgb.shape[:2]
    matrix = np.asarray(
        [
            [plan.scale, 0.0, plan.translate_x],
            [0.0, plan.scale, plan.translate_y],
        ],
        dtype=np.float32,
    )

    warped_rgb = cv2.warpAffine(
        image_rgb,
        matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(245, 245, 245),
    )
    warped_mask = cv2.warpAffine(
        (structure.subject_mask > 0).astype(np.uint8) * 255,
        matrix,
        (w, h),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )

    preview = np.full_like(image_rgb, 245)
    preview[warped_mask > 0] = warped_rgb[warped_mask > 0]

    # Target guides.
    cv2.line(
        preview,
        (0, int(round(plan.target_top_y))),
        (w - 1, int(round(plan.target_top_y))),
        (130, 130, 130),
        1,
        cv2.LINE_AA,
    )
    cv2.line(
        preview,
        (0, int(round(plan.target_bottom_y))),
        (w - 1, int(round(plan.target_bottom_y))),
        (110, 110, 110),
        1,
        cv2.LINE_AA,
    )
    cv2.line(
        preview,
        (int(round(plan.target_visual_center[0])), 0),
        (int(round(plan.target_visual_center[0])), h - 1),
        (160, 160, 160),
        1,
        cv2.LINE_AA,
    )

    bx0, by0, bx1, by1 = plan.transformed_shape_bbox
    cv2.rectangle(
        preview,
        (int(round(bx0)), int(round(by0))),
        (int(round(bx1)), int(round(by1))),
        (90, 210, 120),
        1,
    )
    cv2.circle(
        preview,
        (
            int(round(plan.visual_center_after[0])),
            int(round(plan.visual_center_after[1])),
        ),
        4,
        (70, 130, 255),
        -1,
    )

    text = (
        f"s={plan.scale:.3f} "
        f"dx={plan.translate_x:.1f} dy={plan.translate_y:.1f} "
        f"top={plan.headroom_ratio:.3f} foot={plan.footroom_ratio:.3f}"
    )
    cv2.putText(
        preview,
        text,
        (8, max(14, int(round(h * 0.035)))),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.35,
        (40, 40, 40),
        1,
        cv2.LINE_AA,
    )
    return preview



def transform_layout_reference(
    image_rgb: np.ndarray,
    subject_mask: np.ndarray,
    plan: CharacterLayoutPlan,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Transform the quality-reference subject into final layout coordinates.

    The background remains flat so generic edge metrics do not punish a valid
    Character Layout translation merely because the source pose started at a
    different position on the canvas.
    """
    h, w = image_rgb.shape[:2]
    matrix = np.asarray(
        [
            [plan.scale, 0.0, plan.translate_x],
            [0.0, plan.scale, plan.translate_y],
        ],
        dtype=np.float32,
    )

    mask = (subject_mask > 0).astype(np.uint8) * 255
    bg_pixels = image_rgb[mask == 0]
    if len(bg_pixels) >= 8:
        bg = np.median(bg_pixels.astype(np.float32), axis=0)
        bg_color = tuple(int(np.clip(round(v), 0, 255)) for v in bg)
    else:
        bg_color = (245, 245, 245)

    warped_rgb = cv2.warpAffine(
        image_rgb,
        matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=bg_color,
    )
    warped_mask = cv2.warpAffine(
        mask,
        matrix,
        (w, h),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )

    out = np.empty_like(image_rgb)
    out[:] = bg_color
    out[warped_mask > 0] = warped_rgb[warped_mask > 0]
    return out, warped_mask
