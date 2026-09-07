from __future__ import annotations

import cv2
import numpy as np

from ..models import Region, Shape
from .simplify import simplify_contour
from .design_primitives import design_primitive_for_region
from .regularize import (
    snap_axis_aligned,
    flatten_lower_edge,
    simplify_collinear,
    fit_boat_polygon,
)


def _mask_iou(a: np.ndarray, b: np.ndarray) -> float:
    aa = a > 0
    bb = b > 0
    union = np.count_nonzero(aa | bb)
    return 1.0 if union == 0 else float(np.count_nonzero(aa & bb) / union)


def _circularity(contour: np.ndarray) -> float:
    area = max(float(cv2.contourArea(contour)), 1.0)
    perimeter = max(float(cv2.arcLength(contour, True)), 1.0)
    return min(1.0, float(4.0 * np.pi * area / (perimeter * perimeter)))


def _rectangle_candidate(region: Region):
    x, y, w, h = cv2.boundingRect(region.contour)
    candidate = np.zeros_like(region.mask)
    cv2.rectangle(candidate, (x, y), (x + w - 1, y + h - 1), 255, -1)
    return _mask_iou(region.mask, candidate), (x, y, w, h)


def _circle_candidate(region: Region):
    (cx, cy), radius = cv2.minEnclosingCircle(region.contour)
    candidate = np.zeros_like(region.mask)
    cv2.circle(candidate, (int(round(cx)), int(round(cy))), max(1, int(round(radius))), 255, -1)
    return _mask_iou(region.mask, candidate), (cx, cy, radius)


def _ellipse_candidate(region: Region):
    if region.contour is None or len(region.contour) < 5:
        return 0.0, None

    (cx, cy), (ew, eh), angle = cv2.fitEllipse(region.contour)
    vals = np.asarray([cx, cy, ew, eh, angle], dtype=np.float64)
    if not np.all(np.isfinite(vals)) or ew <= 0 or eh <= 0:
        return 0.0, None
    candidate = np.zeros_like(region.mask)
    cv2.ellipse(
        candidate,
        (int(round(cx)), int(round(cy))),
        (max(1, int(round(ew / 2))), max(1, int(round(eh / 2)))),
        float(angle),
        0,
        360,
        255,
        -1,
    )
    return _mask_iou(region.mask, candidate), (cx, cy, ew, eh, angle)


def _regularize_polygon(region: Region, contour) -> list[tuple[float, float]]:
    pts = [(float(p[0][0]), float(p[0][1])) for p in contour]
    if len(pts) < 3:
        return pts

    x, y, w, h = region.bbox

    if region.role in {"structure", "vertical"}:
        pts = snap_axis_aligned(pts, angle_threshold_deg=17.0, merge_tol=2.0)
    elif region.role == "water":
        pts = snap_axis_aligned(pts, angle_threshold_deg=14.0, merge_tol=2.0)
        pts = flatten_lower_edge(pts, y + h - 1, y_blend=0.74)
    elif region.role == "boat":
        pts = fit_boat_polygon(region.bbox)
    elif region.role == "misc":
        pts = simplify_collinear(pts, tolerance=1.8)

    return pts


def regions_to_shapes(
    regions: list[Region],
    epsilon_ratio: float,
    rectangle_threshold: float,
    circle_threshold: float,
    *,
    major_iou_target: float = 0.80,
    medium_iou_target: float = 0.72,
    small_iou_target: float = 0.62,
    max_major_epsilon_ratio: float = 0.015,
    enable_design_primitives: bool = True,
) -> list[Shape]:
    shapes = []
    sid = 0

    for r in regions:
        if r.contour is None or len(r.contour) < 3:
            continue

        if enable_design_primitives:
            semantic_shapes = design_primitive_for_region(r, sid)
            if semantic_shapes:
                shapes.extend(semantic_shapes)
                sid += len(semantic_shapes)
                continue

        contour = simplify_contour(
            r.contour,
            epsilon_ratio,
            mask=r.mask,
            area_ratio=r.area_ratio,
            major_iou_target=major_iou_target,
            medium_iou_target=medium_iou_target,
            small_iou_target=small_iou_target,
            max_major_epsilon_ratio=max_major_epsilon_ratio,
        )

        rect_iou, rect = _rectangle_candidate(r)
        circle_iou, circle = _circle_candidate(r)
        ellipse_iou, ellipse = _ellipse_candidate(r)

        x, y, w, h = rect
        compactness = min(w, h) / max(w, h)
        circularity = _circularity(r.contour)

        size_penalty = 0.06 if r.area_ratio >= 0.05 else 0.0
        rect_required = min(0.97, rectangle_threshold + size_penalty)
        circle_required = min(0.95, max(0.72, circle_threshold - 0.03) + size_penalty)
        ellipse_required = min(0.93, max(0.70, circle_threshold - 0.08) + size_penalty)

        if r.role == "vertical":
            rect_required = min(rect_required, 0.76)
        if r.role == "accent":
            circle_required = min(circle_required, 0.70)
            ellipse_required = min(ellipse_required, 0.66)
        if r.role == "water":
            rect_required = max(rect_required, 0.88)

        candidates = [
            ("rectangle", rect_iou if compactness >= 0.12 else 0.0),
            ("circle", circle_iou if compactness >= 0.68 and circularity >= 0.68 else 0.0),
            ("ellipse", ellipse_iou if ellipse is not None and compactness >= 0.30 and circularity >= 0.48 else 0.0),
        ]
        candidates.sort(key=lambda t: t[1], reverse=True)
        best_type, best_score = candidates[0]

        if r.role == "boat":
            best_type, best_score = "polygon", 1.0
        elif r.role == "vertical" and rect_iou >= rect_required:
            best_type, best_score = "rectangle", rect_iou

        if best_type == "rectangle" and best_score >= rect_required:
            s = Shape(
                id=sid,
                shape_type="rectangle",
                fill_color=r.color_rgb,
                x=float(x),
                y=float(y),
                width=float(w),
                height=float(h),
                source_region_id=r.id,
                importance=r.importance_score,
                source_role=r.role,
                layer_name=r.composition_layer,
                semantic_type=r.semantic_type,
                pattern_group=r.pattern_group,
                character_part=r.character_part_hint,
                part_confidence=r.part_confidence,
                side_hint=r.side_hint,
            )
        elif best_type == "circle" and best_score >= circle_required:
            cx, cy, radius = circle
            area_radius = float(np.sqrt(max(r.area, 1) / np.pi))
            radius = min(float(radius), area_radius * 1.12)
            s = Shape(
                id=sid,
                shape_type="circle",
                fill_color=r.color_rgb,
                cx=float(cx),
                cy=float(cy),
                rx=float(radius),
                ry=float(radius),
                source_region_id=r.id,
                importance=r.importance_score,
                source_role=r.role,
                layer_name=r.composition_layer,
                semantic_type=r.semantic_type,
                pattern_group=r.pattern_group,
                character_part=r.character_part_hint,
                part_confidence=r.part_confidence,
                side_hint=r.side_hint,
            )
        elif best_type == "ellipse" and best_score >= ellipse_required:
            cx, cy, ew, eh, _ = ellipse
            s = Shape(
                id=sid,
                shape_type="ellipse",
                fill_color=r.color_rgb,
                cx=float(cx),
                cy=float(cy),
                rx=float(ew / 2),
                ry=float(eh / 2),
                source_region_id=r.id,
                importance=r.importance_score,
                source_role=r.role,
                layer_name=r.composition_layer,
                semantic_type=r.semantic_type,
                pattern_group=r.pattern_group,
                character_part=r.character_part_hint,
                part_confidence=r.part_confidence,
                side_hint=r.side_hint,
            )
        else:
            pts = _regularize_polygon(r, contour)
            if len(pts) < 3:
                continue
            s = Shape(
                id=sid,
                shape_type="polygon",
                fill_color=r.color_rgb,
                points=pts,
                source_region_id=r.id,
                importance=r.importance_score,
                source_role=r.role,
                layer_name=r.composition_layer,
                semantic_type=r.semantic_type,
                pattern_group=r.pattern_group,
                character_part=r.character_part_hint,
                part_confidence=r.part_confidence,
                side_hint=r.side_hint,
            )

        shapes.append(s)
        sid += 1

    return shapes
