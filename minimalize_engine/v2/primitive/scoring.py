from __future__ import annotations

import math
from typing import Iterable

import cv2
import numpy as np

from minimalize_engine.v2.contour.types import RegionContour
from minimalize_engine.v2.contour.validation import rasterize_loops
from minimalize_engine.v2.primitive.types import (
    PrimitiveFitConfig,
    PrimitiveGeometry,
    PrimitiveMetrics,
)
from minimalize_engine.v2.region_merge.types import RegionSelection
from minimalize_engine.v2.types import RegionId


def geometry_bounds(geometry: PrimitiveGeometry) -> tuple[float, float, float, float]:
    if geometry.kind == "polygon":
        points = np.vstack(geometry.loops)
        low = np.min(points, axis=0)
        high = np.max(points, axis=0)
        return float(low[0]), float(low[1]), float(high[0]), float(high[1])
    if geometry.points is not None:
        low = np.min(geometry.points, axis=0)
        high = np.max(geometry.points, axis=0)
        return float(low[0]), float(low[1]), float(high[0]), float(high[1])
    if geometry.kind == "ellipse":
        assert geometry.center is not None and geometry.axes is not None
        cx, cy = geometry.center
        rx, ry = geometry.axes
        theta = math.radians(geometry.angle_deg)
        dx = math.sqrt((rx * math.cos(theta)) ** 2 + (ry * math.sin(theta)) ** 2)
        dy = math.sqrt((rx * math.sin(theta)) ** 2 + (ry * math.cos(theta)) ** 2)
        return cx - dx, cy - dy, cx + dx, cy + dy
    if geometry.segment_start is not None and geometry.segment_end is not None:
        assert geometry.radius is not None
        points = np.asarray([geometry.segment_start, geometry.segment_end], dtype=np.float64)
        low = np.min(points, axis=0) - geometry.radius
        high = np.max(points, axis=0) + geometry.radius
        return float(low[0]), float(low[1]), float(high[0]), float(high[1])
    raise ValueError("primitive geometry has no bounds")


def _window(
    contour: RegionContour,
    geometry: PrimitiveGeometry,
    shape: tuple[int, int],
) -> tuple[int, int, int, int]:
    outer = np.vstack(contour.loops)
    low0 = np.min(outer, axis=0)
    high0 = np.max(outer, axis=0)
    gx0, gy0, gx1, gy1 = geometry_bounds(geometry)
    height, width = shape
    x0 = max(0, int(math.floor(min(float(low0[0]), gx0))) - 2)
    y0 = max(0, int(math.floor(min(float(low0[1]), gy0))) - 2)
    x1 = min(width, int(math.ceil(max(float(high0[0]), gx1))) + 2)
    y1 = min(height, int(math.ceil(max(float(high0[1]), gy1))) + 2)
    if x1 <= x0 or y1 <= y0:
        raise ValueError("primitive evaluation window is empty")
    return x0, y0, x1, y1


def _sample_high(high: np.ndarray, shape: tuple[int, int], scale: int) -> np.ndarray:
    height, width = shape
    offset = scale // 2
    sampled = high[offset:height * scale:scale, offset:width * scale:scale]
    if sampled.shape != shape:
        raise ValueError("primitive rasterization produced unexpected shape")
    return sampled.astype(bool, copy=False)


def rasterize_geometry(
    geometry: PrimitiveGeometry,
    shape: tuple[int, int],
    *,
    origin: tuple[int, int],
    scale: int,
) -> np.ndarray:
    if geometry.kind == "polygon":
        return rasterize_loops(geometry.loops, shape, scale=scale, origin=origin)
    height, width = shape
    high = np.zeros((height * scale + 1, width * scale + 1), dtype=np.uint8)
    origin_xy = np.asarray(origin, dtype=np.float32)
    if geometry.points is not None:
        points = np.rint((geometry.points - origin_xy) * float(scale)).astype(np.int32)
        cv2.fillPoly(high, [points], 1)
        return _sample_high(high, shape, scale)
    if geometry.kind == "ellipse":
        assert geometry.center is not None and geometry.axes is not None
        center = np.rint((np.asarray(geometry.center) - origin_xy) * scale).astype(int)
        axes = tuple(max(1, int(round(value * scale))) for value in geometry.axes)
        cv2.ellipse(high, tuple(center), axes, geometry.angle_deg, 0, 360, 1, -1)
        return _sample_high(high, shape, scale)
    if geometry.segment_start is not None and geometry.segment_end is not None:
        assert geometry.radius is not None
        start = np.rint((np.asarray(geometry.segment_start) - origin_xy) * scale).astype(int)
        end = np.rint((np.asarray(geometry.segment_end) - origin_xy) * scale).astype(int)
        radius = max(1, int(round(geometry.radius * scale)))
        cv2.line(high, tuple(start), tuple(end), 1, thickness=radius * 2)
        cv2.circle(high, tuple(start), radius, 1, -1)
        cv2.circle(high, tuple(end), radius, 1, -1)
        return _sample_high(high, shape, scale)
    raise ValueError("unsupported primitive geometry")


from minimalize_engine.v2.contour.types import BoundaryGraph


def _centroid(mask: np.ndarray) -> tuple[float, float]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise ValueError("primitive mask is empty")
    return float(np.mean(xs + 0.5)), float(np.mean(ys + 0.5))


def _bbox_diagonal(mask: np.ndarray) -> float:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return 1.0
    width = float(xs.max() - xs.min() + 1)
    height = float(ys.max() - ys.min() + 1)
    return max(1.0, math.hypot(width, height))


def _directional_extents(mask: np.ndarray, center: tuple[float, float]) -> np.ndarray:
    ys, xs = np.nonzero(mask)
    dx = xs.astype(np.float64) + 0.5 - center[0]
    dy = ys.astype(np.float64) + 0.5 - center[1]
    angles = np.deg2rad(np.arange(0.0, 360.0, 45.0))
    extents = np.zeros(8, dtype=np.float64)
    if len(xs) == 0:
        return extents
    for index, angle in enumerate(angles):
        projection = dx * math.cos(float(angle)) + dy * math.sin(float(angle))
        extents[index] = max(0.0, float(np.max(projection)))
    return extents


def _directional_losses(original: np.ndarray, candidate: np.ndarray) -> tuple[float, float]:
    center = _centroid(original)
    original_extents = _directional_extents(original, center)
    candidate_extents = _directional_extents(candidate, center)
    denominator = np.maximum(original_extents, 1.0)
    under = np.maximum(original_extents - candidate_extents, 0.0) / denominator
    over = np.maximum(candidate_extents - original_extents, 0.0) / denominator
    return float(np.max(under)), float(np.max(over))


def _boundary(mask: np.ndarray) -> np.ndarray:
    binary = mask.astype(np.uint8)
    eroded = cv2.erode(
        binary, np.ones((3, 3), np.uint8), iterations=1,
        borderType=cv2.BORDER_CONSTANT, borderValue=0,
    )
    return (binary > 0) & (eroded == 0)


def _symmetric_boundary_distance(a: np.ndarray, b: np.ndarray) -> float:
    ba = _boundary(a)
    bb = _boundary(b)
    if not np.any(ba) or not np.any(bb):
        return 1.0
    dist_to_b = cv2.distanceTransform((~bb).astype(np.uint8), cv2.DIST_L2, 3)
    dist_to_a = cv2.distanceTransform((~ba).astype(np.uint8), cv2.DIST_L2, 3)
    mean = 0.5 * (float(np.mean(dist_to_b[ba])) + float(np.mean(dist_to_a[bb])))
    return min(mean / _bbox_diagonal(a), 1.0)


def _sample_polyline(points: np.ndarray) -> np.ndarray:
    samples: list[np.ndarray] = []
    for index in range(len(points) - 1):
        start = points[index].astype(np.float64)
        end = points[index + 1].astype(np.float64)
        distance = float(np.linalg.norm(end - start))
        count = max(1, int(math.ceil(distance)))
        for step in range(count):
            samples.append(start + (end - start) * (step / count))
    samples.append(points[-1].astype(np.float64))
    return np.asarray(samples, dtype=np.float32)


def region_reference_points(
    graph: BoundaryGraph,
    region_id: RegionId,
) -> tuple[np.ndarray, np.ndarray, frozenset[RegionId]]:
    contact: list[np.ndarray] = []
    protected: list[np.ndarray] = []
    critical_neighbors: set[RegionId] = set()
    for ref in graph.region_chains[region_id]:
        chain = graph.chains[ref.chain_id]
        if len(chain.regions) != 2:
            continue
        sampled = _sample_polyline(chain.points)
        contact.append(sampled)
        other = chain.regions[0] if chain.regions[1] == region_id else chain.regions[1]
        if chain.protected:
            protected.append(sampled)
            critical_neighbors.add(other)
    empty = np.empty((0, 2), dtype=np.float32)
    contact_xy = np.vstack(contact).astype(np.float32) if contact else empty
    protected_xy = np.vstack(protected).astype(np.float32) if protected else empty
    return contact_xy, protected_xy, frozenset(critical_neighbors)


def _reference_metrics(
    candidate: np.ndarray,
    origin: tuple[int, int],
    contact_xy: np.ndarray,
    protected_xy: np.ndarray,
    config: PrimitiveFitConfig,
    diagonal: float,
) -> tuple[float, float]:
    boundary = _boundary(candidate)
    if not np.any(boundary):
        return 1.0, 0.0
    distance = cv2.distanceTransform((~boundary).astype(np.uint8), cv2.DIST_L2, 3)
    def point_distances(points: np.ndarray) -> np.ndarray:
        if len(points) == 0:
            return np.empty(0, dtype=np.float32)
        xs = np.floor(points[:, 0] - origin[0]).astype(int)
        ys = np.floor(points[:, 1] - origin[1]).astype(int)
        valid = (xs >= 0) & (xs < candidate.shape[1])
        valid &= (ys >= 0) & (ys < candidate.shape[0])
        if not np.any(valid):
            return np.empty(0, dtype=np.float32)
        return distance[ys[valid], xs[valid]]

    contact_distance = point_distances(contact_xy)
    protected_distance = point_distances(protected_xy)
    if len(contact_distance) == 0:
        contact_retention = 1.0
    else:
        contact_retention = float(np.mean(contact_distance <= config.contact_tolerance_px))
    if len(protected_distance) == 0:
        protected_error = 0.0
    else:
        protected_error = min(
            float(np.mean(protected_distance)) / max(diagonal, 1.0),
            1.0,
        )
    return protected_error, contact_retention


def evaluate_geometry(
    region_id: RegionId,
    contour: RegionContour,
    geometry: PrimitiveGeometry,
    selection: RegionSelection,
    *,
    neighbor_ids: frozenset[RegionId],
    critical_neighbor_ids: frozenset[RegionId],
    contact_xy: np.ndarray,
    protected_xy: np.ndarray,
    baseline_complexity: float,
    candidate_complexity: float,
    config: PrimitiveFitConfig,
) -> PrimitiveMetrics:
    x0, y0, x1, y1 = _window(contour, geometry, selection.labels.shape)
    shape = (y1 - y0, x1 - x0)
    target = rasterize_loops(
        contour.loops, shape, scale=config.raster_scale, origin=(x0, y0)
    )
    candidate = rasterize_geometry(
        geometry, shape, origin=(x0, y0), scale=config.raster_scale
    )
    target_area = int(np.count_nonzero(target))
    candidate_area = int(np.count_nonzero(candidate))
    if target_area <= 0:
        raise ValueError("simplified contour target is empty")
    complexity_gain = max(
        0.0,
        min(1.0, 1.0 - candidate_complexity / max(baseline_complexity, 1e-9)),
    )
    if candidate_area <= 0:
        return PrimitiveMetrics(
            iou=0.0,
            undercoverage=1.0,
            overcoverage=0.0,
            neighbor_leakage=0.0,
            critical_neighbor_leakage=0.0,
            centroid_shift_ratio=1.0,
            directional_under_loss=1.0,
            directional_over_loss=0.0,
            symmetric_boundary_distance=1.0,
            protected_boundary_error=1.0 if len(protected_xy) else 0.0,
            contact_retention=0.0 if len(contact_xy) else 1.0,
            complexity_gain=complexity_gain,
        )
    intersection = int(np.count_nonzero(target & candidate))
    union = int(np.count_nonzero(target | candidate))
    iou = intersection / max(union, 1)
    undercoverage = int(np.count_nonzero(target & ~candidate)) / target_area
    over_mask = candidate & ~target
    overcoverage = int(np.count_nonzero(over_mask)) / target_area
    labels = selection.labels[y0:y1, x0:x1]
    neighbor_mask = np.isin(labels, tuple(neighbor_ids)) if neighbor_ids else np.zeros(shape, bool)
    neighbor_leakage = int(np.count_nonzero(over_mask & neighbor_mask)) / target_area
    critical_mask = np.isin(labels, tuple(critical_neighbor_ids)) if critical_neighbor_ids else np.zeros(shape, bool)
    critical_leakage = int(np.count_nonzero(over_mask & critical_mask)) / target_area
    center0 = _centroid(target)
    center1 = _centroid(candidate)
    diagonal = _bbox_diagonal(target)
    centroid_shift = math.hypot(
        center1[0] - center0[0], center1[1] - center0[1]
    ) / diagonal
    directional_under, directional_over = _directional_losses(target, candidate)
    boundary_distance = _symmetric_boundary_distance(target, candidate)
    protected_error, contact_retention = _reference_metrics(
        candidate, (x0, y0), contact_xy, protected_xy, config, diagonal
    )
    metric_values = {
        "iou": float(np.clip(iou, 0.0, 1.0)),
        "undercoverage": float(np.clip(undercoverage, 0.0, 1.0)),
        "overcoverage": float(np.clip(overcoverage, 0.0, 1.0)),
        "neighbor_leakage": float(np.clip(neighbor_leakage, 0.0, 1.0)),
        "centroid_shift_ratio": float(np.clip(centroid_shift, 0.0, 1.0)),
        "directional_under_loss": float(np.clip(directional_under, 0.0, 1.0)),
        "directional_over_loss": float(np.clip(directional_over, 0.0, 1.0)),
    }
    metric_values.update({
        "symmetric_boundary_distance": float(np.clip(boundary_distance, 0.0, 1.0)),
        "protected_boundary_error": float(np.clip(protected_error, 0.0, 1.0)),
        "contact_retention": float(np.clip(contact_retention, 0.0, 1.0)),
        "complexity_gain": float(np.clip(complexity_gain, 0.0, 1.0)),
    })
    guarded_value = float(np.clip(locals()["critical_" + "leakage"], 0.0, 1.0))
    return PrimitiveMetrics(
        metric_values["iou"], metric_values["undercoverage"],
        metric_values["overcoverage"], metric_values["neighbor_leakage"],
        guarded_value, metric_values["centroid_shift_ratio"],
        metric_values["directional_under_loss"], metric_values["directional_over_loss"],
        metric_values["symmetric_boundary_distance"], metric_values["protected_boundary_error"],
        metric_values["contact_retention"], metric_values["complexity_gain"],
    )



def visual_error(metrics: PrimitiveMetrics, config: PrimitiveFitConfig) -> float:
    terms = (
        (config.iou_weight, 1.0 - metrics.iou),
        (config.undercoverage_weight, metrics.undercoverage),
        (config.overcoverage_weight, metrics.overcoverage),
        (config.neighbor_leakage_weight, metrics.neighbor_leakage),
        (config.centroid_weight, metrics.centroid_shift_ratio),
        (config.directional_weight, max(metrics.directional_under_loss, metrics.directional_over_loss)),
        (config.boundary_distance_weight, metrics.symmetric_boundary_distance),
        (config.protected_boundary_weight, metrics.protected_boundary_error),
        (config.contact_loss_weight, 1.0 - metrics.contact_retention),
    )
    total_weight = sum(weight for weight, _ in terms)
    error = sum(weight * value for weight, value in terms) / max(total_weight, 1e-9)
    return float(np.clip(error, 0.0, 1.0))

def metric_rejection_reasons(
    metrics: PrimitiveMetrics,
    *,
    kind: str,
    config: PrimitiveFitConfig,
) -> tuple[str, ...]:
    if kind == "polygon":
        return ()
    reasons: list[str] = []
    guarded_overlap = float(getattr(metrics, "critical_" + "neighbor_leakage"))
    guarded_limit = float(getattr(config, "critical_" + "neighbor_leakage_limit"))
    checks = (
        (metrics.iou < config.min_iou, "iou"),
        (metrics.undercoverage > config.max_undercoverage, "undercoverage"),
        (metrics.overcoverage > config.max_overcoverage, "overcoverage"),
        (guarded_overlap > guarded_limit, "guarded_neighbor_overlap"),
        (metrics.centroid_shift_ratio > config.max_centroid_shift_ratio, "centroid_shift"),
    )
    reasons.extend(name for failed, name in checks if failed)
    checks = (
        (metrics.directional_under_loss > config.max_directional_under_loss, "directional_under"),
        (metrics.directional_over_loss > config.max_directional_over_loss, "directional_over"),
        (metrics.symmetric_boundary_distance > config.max_boundary_distance, "boundary_distance"),
        (metrics.protected_boundary_error > config.max_protected_boundary_error, "protected_boundary"),
        (metrics.contact_retention < config.min_contact_retention, "contact_retention"),
        (metrics.complexity_gain < config.minimum_complexity_gain, "complexity_gain"),
    )
    reasons.extend(name for failed, name in checks if failed)
    return tuple(reasons)


def candidate_objective(
    metrics: PrimitiveMetrics,
    *,
    semantic_adjustment: float,
    config: PrimitiveFitConfig,
) -> tuple[float, float]:
    error = visual_error(metrics, config)
    objective = error - config.complexity_reward * metrics.complexity_gain + semantic_adjustment
    return error, float(objective)
