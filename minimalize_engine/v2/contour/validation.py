from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

import cv2
import numpy as np

from minimalize_engine.v2.contour.types import (
    BoundaryGraph,
    ContourSimplificationConfig,
    OrientedChainRef,
    PointArray,
)
from minimalize_engine.v2.region_merge.types import RegionMergeResult, RegionSelection
from minimalize_engine.v2.types import RegionId


@dataclass(frozen=True, slots=True)
class RegionContourMetrics:
    iou: float
    area_change: float
    centroid_shift_ratio: float
    directional_loss: float
    topology_ok: bool
    self_intersection_free: bool

    @property
    def valid(self) -> bool:
        return self.topology_ok and self.self_intersection_free


def oriented_chain_points(
    graph: BoundaryGraph,
    ref: OrientedChainRef,
    points_by_chain: Mapping[int, PointArray] | None = None,
) -> np.ndarray:
    points = (
        graph.chains[ref.chain_id].points
        if points_by_chain is None
        else points_by_chain[ref.chain_id]
    )
    return points[::-1] if ref.reversed else points


def _directed_endpoints(graph: BoundaryGraph, ref: OrientedChainRef) -> tuple[int, int]:
    chain = graph.chains[ref.chain_id]
    if ref.reversed:
        return chain.end_vertex, chain.start_vertex
    return chain.start_vertex, chain.end_vertex


def _turn_priority(incoming: np.ndarray, outgoing: np.ndarray) -> tuple[int, float]:
    angle_in = math.atan2(float(incoming[1]), float(incoming[0]))
    angle_out = math.atan2(float(outgoing[1]), float(outgoing[0]))
    delta = (angle_out - angle_in) % (2.0 * math.pi)
    eps = 1e-9
    if eps < delta < math.pi - eps:
        return (0, delta)
    if delta <= eps or abs(delta - 2.0 * math.pi) <= eps:
        return (1, 0.0)
    if math.pi + eps < delta < 2.0 * math.pi - eps:
        return (2, 2.0 * math.pi - delta)
    return (3, 0.0)


def assemble_region_loops(
    graph: BoundaryGraph,
    region_id: RegionId,
    points_by_chain: Mapping[int, PointArray] | None = None,
) -> tuple[np.ndarray, ...]:
    refs = list(graph.region_chains[region_id])
    unused = {index for index in range(len(refs))}
    starts: dict[int, list[int]] = {}
    for index, ref in enumerate(refs):
        start, _ = _directed_endpoints(graph, ref)
        starts.setdefault(start, []).append(index)
    loops: list[np.ndarray] = []

    while unused:
        index = min(unused, key=lambda item: (refs[item].chain_id, refs[item].reversed))
        first_ref = refs[index]
        start_vertex, end_vertex = _directed_endpoints(graph, first_ref)
        points = oriented_chain_points(graph, first_ref, points_by_chain).astype(np.float32, copy=True)
        unused.remove(index)
        current_vertex = end_vertex
        incoming = points[-1] - points[-2]

        while current_vertex != start_vertex:
            candidates = [item for item in starts.get(current_vertex, []) if item in unused]
            if not candidates:
                raise ValueError(f"region {region_id} boundary does not close")
            if len(candidates) > 1:
                def key(item: int):
                    candidate_points = oriented_chain_points(graph, refs[item], points_by_chain)
                    outgoing = candidate_points[1] - candidate_points[0]
                    return (*_turn_priority(incoming, outgoing), refs[item].chain_id)
                next_index = min(candidates, key=key)
            else:
                next_index = candidates[0]
            next_ref = refs[next_index]
            _, current_vertex = _directed_endpoints(graph, next_ref)
            next_points = oriented_chain_points(graph, next_ref, points_by_chain)
            incoming = next_points[-1] - next_points[-2]
            points = np.vstack([points, next_points[1:]])
            unused.remove(next_index)

        if np.allclose(points[0], points[-1]):
            points = points[:-1]
        if len(points) < 3:
            raise ValueError(f"region {region_id} boundary loop has fewer than 3 points")
        loops.append(points.astype(np.float32, copy=False))
    return tuple(loops)


def rasterize_loops(
    loops: tuple[np.ndarray, ...],
    shape: tuple[int, int],
    *,
    scale: int,
    origin: tuple[int, int] = (0, 0),
) -> np.ndarray:
    height, width = shape
    high = np.zeros((height * scale + 1, width * scale + 1), dtype=np.uint8)
    for loop in loops:
        local = np.zeros_like(high)
        shifted = loop - np.asarray(origin, dtype=np.float32)
        polygon = np.rint(shifted * float(scale)).astype(np.int32)
        cv2.fillPoly(local, [polygon], 1)
        high ^= local
    offset = scale // 2
    sampled = high[offset:height * scale:scale, offset:width * scale:scale]
    if sampled.shape != shape:
        raise ValueError("contour rasterization produced unexpected shape")
    return sampled.astype(bool, copy=False)


def _topology_signature(mask: np.ndarray) -> tuple[int, int]:
    binary = mask.astype(np.uint8)
    count, _ = cv2.connectedComponents(binary, connectivity=4)
    components = max(0, int(count) - 1)
    contours, hierarchy = cv2.findContours(
        binary * 255, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
    )
    holes = 0
    if hierarchy is not None:
        hierarchy = hierarchy[0]
        holes = sum(1 for item in hierarchy if int(item[3]) >= 0)
    return components, holes


def _centroid(mask: np.ndarray) -> tuple[float, float]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise ValueError("contour candidate removed an entire region")
    return float(np.mean(xs + 0.5)), float(np.mean(ys + 0.5))


def _bbox_diagonal(mask: np.ndarray) -> float:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return 1.0
    width = float(xs.max() - xs.min() + 1)
    height = float(ys.max() - ys.min() + 1)
    return max(1.0, math.hypot(width, height))


def _directional_extents(mask: np.ndarray, centroid: tuple[float, float]) -> np.ndarray:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return np.zeros(8, dtype=np.float64)
    dx = xs.astype(np.float64) + 0.5 - centroid[0]
    dy = ys.astype(np.float64) + 0.5 - centroid[1]
    angles = np.deg2rad(np.arange(0.0, 360.0, 45.0))
    extents = np.empty(8, dtype=np.float64)
    for index, angle in enumerate(angles):
        projection = dx * math.cos(float(angle)) + dy * math.sin(float(angle))
        extents[index] = max(0.0, float(np.max(projection)))
    return extents


def _directional_loss(original: np.ndarray, candidate: np.ndarray) -> float:
    center = _centroid(original)
    original_extents = _directional_extents(original, center)
    candidate_extents = _directional_extents(candidate, center)
    denominator = np.maximum(original_extents, 1.0)
    losses = np.maximum(original_extents - candidate_extents, 0.0) / denominator
    return float(np.max(losses))


def _orientation(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    return float((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))


def _on_segment(a: np.ndarray, b: np.ndarray, p: np.ndarray) -> bool:
    eps = 1e-6
    return (
        min(a[0], b[0]) - eps <= p[0] <= max(a[0], b[0]) + eps
        and min(a[1], b[1]) - eps <= p[1] <= max(a[1], b[1]) + eps
        and abs(_orientation(a, b, p)) <= eps
    )


def _segments_intersect(a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray) -> bool:
    eps = 1e-6
    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    if ((o1 > eps and o2 < -eps) or (o1 < -eps and o2 > eps)) and (
        (o3 > eps and o4 < -eps) or (o3 < -eps and o4 > eps)
    ):
        return True
    return (
        (abs(o1) <= eps and _on_segment(a, b, c))
        or (abs(o2) <= eps and _on_segment(a, b, d))
        or (abs(o3) <= eps and _on_segment(c, d, a))
        or (abs(o4) <= eps and _on_segment(c, d, b))
    )


def loops_have_self_intersection(loops: tuple[np.ndarray, ...]) -> bool:
    starts_list: list[np.ndarray] = []
    ends_list: list[np.ndarray] = []
    loop_ids: list[int] = []
    edge_ids: list[int] = []
    loop_counts = [len(loop) for loop in loops]
    for loop_index, loop in enumerate(loops):
        points = np.asarray(loop, dtype=np.float32)
        count = len(points)
        starts_list.extend(points[index] for index in range(count))
        ends_list.extend(points[(index + 1) % count] for index in range(count))
        loop_ids.extend([loop_index] * count)
        edge_ids.extend(range(count))
    if len(starts_list) < 2:
        return False
    starts = np.asarray(starts_list, dtype=np.float32)
    ends = np.asarray(ends_list, dtype=np.float32)
    loop_ids_array = np.asarray(loop_ids, dtype=np.int32)
    edge_ids_array = np.asarray(edge_ids, dtype=np.int32)
    low = np.minimum(starts, ends)
    high = np.maximum(starts, ends)
    eps = 1e-6
    for index in range(len(starts) - 1):
        candidates = np.arange(index + 1, len(starts), dtype=np.int32)
        overlap = (
            (high[candidates, 0] + eps >= low[index, 0])
            & (low[candidates, 0] - eps <= high[index, 0])
            & (high[candidates, 1] + eps >= low[index, 1])
            & (low[candidates, 1] - eps <= high[index, 1])
        )
        candidates = candidates[overlap]
        if candidates.size == 0:
            continue
        same_loop = loop_ids_array[candidates] == loop_ids_array[index]
        if np.any(same_loop):
            count = loop_counts[int(loop_ids_array[index])]
            delta = (edge_ids_array[candidates] - edge_ids_array[index]) % count
            adjacent = same_loop & ((delta == 1) | (delta == count - 1))
            candidates = candidates[~adjacent]
        if candidates.size == 0:
            continue
        a, b = starts[index], ends[index]
        shared = (
            np.all(starts[candidates] == a, axis=1)
            | np.all(ends[candidates] == a, axis=1)
            | np.all(starts[candidates] == b, axis=1)
            | np.all(ends[candidates] == b, axis=1)
        )
        candidates = candidates[~shared]
        for other_index in candidates:
            if _segments_intersect(a, b, starts[other_index], ends[other_index]):
                return True
    return False


def directional_limit_for_region(
    merge_result: RegionMergeResult,
    region_id: RegionId,
    total_pixels: int,
    config: ContourSimplificationConfig,
) -> float:
    stats = merge_result.tree.nodes[region_id].stats
    factor = 1.0
    semantic = (stats.semantic_tag or "").casefold()
    if "face" in semantic and stats.semantic_confidence >= 0.80:
        factor = min(factor, config.face_directional_factor)
    if stats.pixel_count / max(total_pixels, 1) >= config.major_mass_ratio:
        factor = min(factor, config.major_mass_directional_factor)
    return config.max_directional_loss * factor


def evaluate_region_candidate(
    original_mask: np.ndarray,
    candidate_mask: np.ndarray,
    loops: tuple[np.ndarray, ...],
    *,
    directional_limit: float,
    config: ContourSimplificationConfig,
    check_self_intersection: bool = True,
) -> RegionContourMetrics:
    original_area = int(np.count_nonzero(original_mask))
    candidate_area = int(np.count_nonzero(candidate_mask))
    if original_area <= 0 or candidate_area <= 0:
        return RegionContourMetrics(0.0, 1.0, 1.0, 1.0, False, False)
    intersection = int(np.count_nonzero(original_mask & candidate_mask))
    union = int(np.count_nonzero(original_mask | candidate_mask))
    iou = intersection / max(union, 1)
    area_change = abs(candidate_area - original_area) / float(original_area)
    c0 = _centroid(original_mask)
    c1 = _centroid(candidate_mask)
    centroid_shift = math.hypot(c1[0] - c0[0], c1[1] - c0[1]) / _bbox_diagonal(original_mask)
    directional_loss = _directional_loss(original_mask, candidate_mask)
    topology_ok = _topology_signature(original_mask) == _topology_signature(candidate_mask)
    self_free = True if not check_self_intersection else not loops_have_self_intersection(loops)
    metrics = RegionContourMetrics(
        iou=float(iou),
        area_change=float(min(area_change, 1.0)),
        centroid_shift_ratio=float(min(centroid_shift, 1.0)),
        directional_loss=float(min(directional_loss, 1.0)),
        topology_ok=topology_ok,
        self_intersection_free=self_free,
    )
    return metrics


def candidate_passes_guards(
    metrics: RegionContourMetrics,
    *,
    directional_limit: float,
    config: ContourSimplificationConfig,
) -> bool:
    return (
        metrics.valid
        and metrics.area_change <= config.max_area_change
        and metrics.iou >= config.min_iou
        and metrics.centroid_shift_ratio <= config.max_centroid_shift_ratio
        and metrics.directional_loss <= directional_limit
    )


def candidate_chain_intersection_free(
    graph: BoundaryGraph,
    region_id: RegionId,
    chain_id: int,
    points_by_chain: Mapping[int, PointArray],
) -> bool:
    candidate = np.asarray(points_by_chain[chain_id], dtype=np.float32)
    segments = [(candidate[i], candidate[i + 1]) for i in range(len(candidate) - 1)]
    for left_index, (a, b) in enumerate(segments):
        for c, d in segments[left_index + 2:]:
            if _segments_intersect(a, b, c, d):
                return False
    other_segments: list[tuple[np.ndarray, np.ndarray]] = []
    for ref in graph.region_chains[region_id]:
        if ref.chain_id == chain_id:
            continue
        other = oriented_chain_points(graph, ref, points_by_chain)
        other_segments.extend(
            (other[index], other[index + 1])
            for index in range(len(other) - 1)
        )
    if not other_segments:
        return True
    starts = np.asarray([item[0] for item in other_segments], dtype=np.float32)
    ends = np.asarray([item[1] for item in other_segments], dtype=np.float32)
    other_min = np.minimum(starts, ends)
    other_max = np.maximum(starts, ends)
    eps = 1e-6
    for a, b in segments:
        low = np.minimum(a, b)
        high = np.maximum(a, b)
        overlap = (
            (other_max[:, 0] + eps >= low[0])
            & (other_min[:, 0] - eps <= high[0])
            & (other_max[:, 1] + eps >= low[1])
            & (other_min[:, 1] - eps <= high[1])
        )
        for index in np.flatnonzero(overlap):
            c, d = starts[index], ends[index]
            shared_points = [
                first for first in (a, b)
                for second in (c, d) if np.array_equal(first, second)
            ]
            if shared_points:
                if len(shared_points) > 1:
                    return False
                point = shared_points[0]
                other_a = b if np.array_equal(a, point) else a
                other_b = d if np.array_equal(c, point) else c
                if abs(_orientation(point, other_a, other_b)) <= eps:
                    if float(np.dot(other_a - point, other_b - point)) > eps:
                        return False
                continue
            if _segments_intersect(a, b, c, d):
                return False
    return True
