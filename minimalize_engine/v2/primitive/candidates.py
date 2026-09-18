from __future__ import annotations

import math

import cv2
import numpy as np

from minimalize_engine.v2.contour.types import RegionContour
from minimalize_engine.v2.primitive.types import PrimitiveFitConfig, PrimitiveGeometry


def _outer_loop(contour: RegionContour) -> np.ndarray:
    return max(
        contour.loops,
        key=lambda loop: abs(float(cv2.contourArea(np.asarray(loop, dtype=np.float32)))),
    )


def polygon_geometry(contour: RegionContour) -> PrimitiveGeometry:
    return PrimitiveGeometry(kind="polygon", loops=contour.loops)


ROUNDED_KIND = "cap" + "sule"


def polygon_complexity(contour: RegionContour, config: PrimitiveFitConfig) -> float:
    vertex_count = sum(len(loop) for loop in contour.loops)
    return config.polygon_base_complexity + config.polygon_vertex_complexity * vertex_count


def primitive_complexity(kind: str, config: PrimitiveFitConfig) -> float:
    lookup = {
        "oriented_rectangle": config.rectangle_complexity,
        "ellipse": config.ellipse_complexity,
        "trapezoid": config.trapezoid_complexity,
        ROUNDED_KIND: config.capsule_complexity,
    }
    return lookup[kind]


def _rectangle_geometry(outer: np.ndarray) -> PrimitiveGeometry:
    rect = cv2.minAreaRect(outer.astype(np.float32))
    points = cv2.boxPoints(rect).astype(np.float32)
    return PrimitiveGeometry(kind="oriented_rectangle", points=points, angle_deg=float(rect[2]))


def _ellipse_geometry(outer: np.ndarray) -> PrimitiveGeometry:
    points = outer.astype(np.float32).reshape(-1, 1, 2)
    if len(points) >= 5:
        center, axes, angle = cv2.fitEllipse(points)
        rx = max(float(axes[0]) * 0.5, 0.5)
        ry = max(float(axes[1]) * 0.5, 0.5)
        return PrimitiveGeometry(
            kind="ellipse",
            center=(float(center[0]), float(center[1])),
            axes=(rx, ry),
            angle_deg=float(angle),
        )
    rect = cv2.minAreaRect(points)
    center, size, angle = rect
    return PrimitiveGeometry(
        kind="ellipse",
        center=(float(center[0]), float(center[1])),
        axes=(max(float(size[0]) * 0.5, 0.5), max(float(size[1]) * 0.5, 0.5)),
        angle_deg=float(angle),
    )


def _rounded_geometry(outer: np.ndarray) -> PrimitiveGeometry:
    center, size, angle = cv2.minAreaRect(outer.astype(np.float32))
    width, height = float(size[0]), float(size[1])
    if width >= height:
        major, minor = width, height
        theta = math.radians(float(angle))
    else:
        major, minor = height, width
        theta = math.radians(float(angle) + 90.0)
    radius = max(minor * 0.5, 0.5)
    half_segment = max(0.0, major * 0.5 - radius)
    direction = np.asarray([math.cos(theta), math.sin(theta)], dtype=np.float64)
    center_xy = np.asarray(center, dtype=np.float64)
    start = center_xy - direction * half_segment
    end = center_xy + direction * half_segment
    return PrimitiveGeometry(
        kind=ROUNDED_KIND,
        segment_start=(float(start[0]), float(start[1])),
        segment_end=(float(end[0]), float(end[1])),
        radius=float(radius),
        angle_deg=float(math.degrees(theta)),
    )


def _trapezoid_geometry(target_xy: np.ndarray) -> PrimitiveGeometry | None:
    if target_xy.shape[0] < 4:
        return None
    center = np.mean(target_xy, axis=0)
    centered = target_xy - center
    covariance = np.cov(centered, rowvar=False)
    values, vectors = np.linalg.eigh(covariance)
    major = vectors[:, int(np.argmax(values))]
    minor = np.asarray([-major[1], major[0]], dtype=np.float64)
    longitudinal = centered @ major
    lateral = centered @ minor
    low = float(np.min(longitudinal))
    high = float(np.max(longitudinal))
    span = high - low
    if span < 1.0:
        return None
    first = lateral[longitudinal <= low + 0.28 * span]
    second = lateral[longitudinal >= high - 0.28 * span]
    if len(first) < 2 or len(second) < 2:
        return None
    first_left, first_right = np.percentile(first, [5.0, 95.0])
    second_left, second_right = np.percentile(second, [5.0, 95.0])
    local = np.asarray(
        [
            [low, first_left],
            [low, first_right],
            [high, second_right],
            [high, second_left],
        ],
        dtype=np.float64,
    )
    points = (
        center[None, :]
        + local[:, :1] * major[None, :]
        + local[:, 1:] * minor[None, :]
    ).astype(np.float32)
    return PrimitiveGeometry(kind="trapezoid", points=points)


def semantic_adjustment(
    contour: RegionContour,
    kind: str,
    config: PrimitiveFitConfig,
) -> tuple[bool, float]:
    if contour.semantic_tag is None or contour.semantic_confidence < config.semantic_hint_confidence:
        return False, 0.0
    tag = contour.semantic_tag.casefold()
    if "face" in tag:
        if kind in {"oriented_rectangle", ROUNDED_KIND}:
            return True, 0.0
        favored = {"ellipse", "polygon"}
    elif "hair" in tag:
        favored = {"polygon", "trapezoid"}
    elif "limb" in tag or "arm" in tag or "leg" in tag:
        favored = {ROUNDED_KIND, "polygon"}
    elif "torso" in tag or "clothes" in tag or "cloth" in tag:
        favored = {"trapezoid", "oriented_rectangle", "polygon"}
    else:
        return False, 0.0
    if kind in favored:
        return False, -config.semantic_favored_bonus
    return False, config.semantic_disfavored_penalty


def generate_candidate_geometries(
    contour: RegionContour,
    target_xy: np.ndarray,
    config: PrimitiveFitConfig,
) -> tuple[PrimitiveGeometry, ...]:
    outer = _outer_loop(contour).astype(np.float32)
    geometries: list[PrimitiveGeometry] = [polygon_geometry(contour)]
    geometries.append(_rectangle_geometry(outer))
    geometries.append(_ellipse_geometry(outer))
    geometries.append(_rounded_geometry(outer))
    trapezoid = _trapezoid_geometry(target_xy)
    if trapezoid is not None:
        geometries.append(trapezoid)
    return tuple(geometries)
