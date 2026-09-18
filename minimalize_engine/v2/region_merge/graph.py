from __future__ import annotations

from collections.abc import Mapping, Sequence

import cv2
import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.types import (
    CharacteristicSupport,
    EdgeKey,
    ImageBundle,
    LabelMap,
    RegionAnnotation,
    RegionId,
)
from minimalize_engine.v2.region_merge.types import (
    MergeTreeNode,
    RegionEdge,
    RegionGraph,
    RegionMergeTree,
    RegionStats,
)

DEFAULT_GRADIENT_BINS = 32
_ALPHA_EDGE_DELTA = 0.5


def edge_key(a: RegionId, b: RegionId) -> EdgeKey:
    if a == b:
        raise ValueError("edge endpoints must differ")
    return (a, b) if a < b else (b, a)


def _validate_analysis_inputs(
    labels: NDArray[np.integer],
    analysis_lab: NDArray[np.floating],
    edge_raw: NDArray[np.floating],
    edge_structural: NDArray[np.floating],
) -> tuple[int, int]:
    if labels.ndim != 2:
        raise ValueError("labels must be a 2D array")
    height, width = labels.shape
    if analysis_lab.shape != (height, width, 3):
        raise ValueError("analysis_lab must have shape (H, W, 3)")
    if edge_raw.shape != (height, width) or edge_structural.shape != (height, width):
        raise ValueError("edge maps must have shape (H, W)")
    if labels.size == 0:
        raise ValueError("labels must not be empty")
    if np.any(labels < 0):
        raise ValueError("labels must be non-negative")
    return height, width


def _validate_optional_map(
    name: str,
    value: NDArray[np.floating] | None,
    shape: tuple[int, int],
) -> None:
    if value is not None and value.shape != shape:
        raise ValueError(f"{name} must have shape {shape}")


def _pixel_hull(
    xs: NDArray[np.int64],
    ys: NDArray[np.int64],
) -> tuple[NDArray[np.float32], float]:
    # Use pixel-cell corners so even one-pixel-wide regions have meaningful area.
    x0 = xs.astype(np.float32)
    y0 = ys.astype(np.float32)
    corners = np.concatenate(
        (
            np.column_stack((x0, y0)),
            np.column_stack((x0 + 1.0, y0)),
            np.column_stack((x0 + 1.0, y0 + 1.0)),
            np.column_stack((x0, y0 + 1.0)),
        ),
        axis=0,
    )
    hull = (
        cv2.convexHull(corners, returnPoints=True)
        .reshape(-1, 2)
        .astype(np.float32, copy=False)
    )
    return hull, float(cv2.contourArea(hull))


def _region_perimeters(
    labels: NDArray[np.int32],
    region_ids: NDArray[np.int64],
) -> dict[int, float]:
    flat = labels.ravel()
    counts = np.bincount(flat, minlength=int(region_ids[-1]) + 1).astype(np.float64)
    perimeter = counts * 4.0

    left = labels[:, :-1]
    right = labels[:, 1:]
    same = left == right
    if np.any(same):
        perimeter -= 2.0 * np.bincount(left[same], minlength=perimeter.size)

    top = labels[:-1, :]
    bottom = labels[1:, :]
    same = top == bottom
    if np.any(same):
        perimeter -= 2.0 * np.bincount(top[same], minlength=perimeter.size)

    return {int(region_id): float(perimeter[region_id]) for region_id in region_ids}


def build_region_stats(
    labels: NDArray[np.integer],
    analysis_lab: NDArray[np.floating],
    *,
    subject_prob: NDArray[np.floating] | None = None,
    subject_confidence: NDArray[np.floating] | None = None,
    annotations: Mapping[RegionId, RegionAnnotation] | None = None,
) -> dict[RegionId, RegionStats]:
    labels32 = np.asarray(labels, dtype=np.int32)
    if labels32.ndim != 2 or labels32.size == 0:
        raise ValueError("labels must be a non-empty 2D array")
    if np.any(labels32 < 0):
        raise ValueError("labels must be non-negative")

    height, width = labels32.shape
    if analysis_lab.shape != (height, width, 3):
        raise ValueError("analysis_lab must have shape (H, W, 3)")
    _validate_optional_map("subject_prob", subject_prob, labels32.shape)
    _validate_optional_map("subject_confidence", subject_confidence, labels32.shape)

    flat_labels = labels32.ravel()
    region_ids = np.unique(flat_labels).astype(np.int64)
    max_id = int(region_ids[-1])
    minlength = max_id + 1
    pixel_count = np.bincount(flat_labels, minlength=minlength).astype(np.int64)

    yy, xx = np.indices(labels32.shape, dtype=np.float64)
    px = (xx + 0.5).ravel()
    py = (yy + 0.5).ravel()
    sum_x = np.bincount(flat_labels, weights=px, minlength=minlength)
    sum_y = np.bincount(flat_labels, weights=py, minlength=minlength)
    sum_xx = np.bincount(flat_labels, weights=px * px, minlength=minlength)
    sum_yy = np.bincount(flat_labels, weights=py * py, minlength=minlength)
    sum_xy = np.bincount(flat_labels, weights=px * py, minlength=minlength)

    lab = np.asarray(analysis_lab, dtype=np.float64).reshape(-1, 3)
    sum_lab = np.column_stack(
        [
            np.bincount(flat_labels, weights=lab[:, channel], minlength=minlength)
            for channel in range(3)
        ]
    )
    sum_sq_lab = np.column_stack(
        [
            np.bincount(
                flat_labels,
                weights=lab[:, channel] * lab[:, channel],
                minlength=minlength,
            )
            for channel in range(3)
        ]
    )

    if subject_prob is None:
        subject_prob_sum = np.zeros(minlength, dtype=np.float64)
    else:
        subject_prob_sum = np.bincount(
            flat_labels,
            weights=np.asarray(subject_prob, dtype=np.float64).ravel(),
            minlength=minlength,
        )

    if subject_confidence is None:
        subject_confidence_sum = np.zeros(minlength, dtype=np.float64)
    else:
        subject_confidence_sum = np.bincount(
            flat_labels,
            weights=np.asarray(subject_confidence, dtype=np.float64).ravel(),
            minlength=minlength,
        )

    x_min = np.full(minlength, width, dtype=np.int64)
    y_min = np.full(minlength, height, dtype=np.int64)
    x_max = np.full(minlength, -1, dtype=np.int64)
    y_max = np.full(minlength, -1, dtype=np.int64)
    x_int = xx.astype(np.int64, copy=False).ravel()
    y_int = yy.astype(np.int64, copy=False).ravel()
    np.minimum.at(x_min, flat_labels, x_int)
    np.minimum.at(y_min, flat_labels, y_int)
    np.maximum.at(x_max, flat_labels, x_int)
    np.maximum.at(y_max, flat_labels, y_int)

    perimeters = _region_perimeters(labels32, region_ids)
    order = np.argsort(flat_labels, kind="stable")
    ordered_labels = flat_labels[order]
    starts = np.searchsorted(ordered_labels, region_ids, side="left")
    ends = np.searchsorted(ordered_labels, region_ids, side="right")

    annotations = annotations or {}
    stats: dict[RegionId, RegionStats] = {}
    for region_id, start, end in zip(region_ids, starts, ends, strict=True):
        rid = int(region_id)
        positions = order[start:end]
        ys, xs = np.divmod(positions, width)
        hull_xy, hull_area = _pixel_hull(
            xs.astype(np.int64),
            ys.astype(np.int64),
        )
        annotation = annotations.get(rid, RegionAnnotation())
        stats[rid] = RegionStats(
            id=rid,
            pixel_count=int(pixel_count[rid]),
            sum_lab=sum_lab[rid],
            sum_sq_lab=sum_sq_lab[rid],
            sum_x=float(sum_x[rid]),
            sum_y=float(sum_y[rid]),
            sum_xx=float(sum_xx[rid]),
            sum_yy=float(sum_yy[rid]),
            sum_xy=float(sum_xy[rid]),
            bbox=(
                int(x_min[rid]),
                int(y_min[rid]),
                int(x_max[rid] + 1),
                int(y_max[rid] + 1),
            ),
            perimeter_px=perimeters[rid],
            hull_xy=hull_xy,
            hull_area=hull_area,
            subject_prob_sum=float(subject_prob_sum[rid]),
            subject_confidence_sum=float(subject_confidence_sum[rid]),
            characteristic_supports=annotation.characteristic_supports,
            semantic_tag=annotation.semantic_tag,
            semantic_confidence=annotation.semantic_confidence,
        )

    return stats


def _boundary_histogram(
    values: NDArray[np.floating],
    bins: int,
) -> NDArray[np.int64]:
    clipped = np.clip(np.asarray(values, dtype=np.float64), 0.0, 1.0)
    hist, _ = np.histogram(clipped, bins=bins, range=(0.0, 1.0))
    return hist.astype(np.int64, copy=False)


def _collect_boundaries(
    labels: NDArray[np.int32],
    edge_raw: NDArray[np.floating],
    edge_structural: NDArray[np.floating],
    alpha: NDArray[np.floating] | None,
) -> dict[EdgeKey, tuple[list[float], list[float], int, int]]:
    buckets: dict[EdgeKey, tuple[list[float], list[float], int, int]] = {}

    def add_pair(
        a: int,
        b: int,
        raw_value: float,
        structural_value: float,
        alpha_hit: bool,
    ) -> None:
        key = edge_key(a, b)
        if key not in buckets:
            buckets[key] = ([], [], 0, 0)
        raw_values, structural_values, alpha_hits, total = buckets[key]
        raw_values.append(raw_value)
        structural_values.append(structural_value)
        buckets[key] = (
            raw_values,
            structural_values,
            alpha_hits + int(alpha_hit),
            total + 1,
        )

    for axis in (1, 0):
        if axis == 1:
            lhs_labels, rhs_labels = labels[:, :-1], labels[:, 1:]
            lhs_raw, rhs_raw = edge_raw[:, :-1], edge_raw[:, 1:]
            lhs_struct, rhs_struct = edge_structural[:, :-1], edge_structural[:, 1:]
            if alpha is not None:
                lhs_alpha, rhs_alpha = alpha[:, :-1], alpha[:, 1:]
        else:
            lhs_labels, rhs_labels = labels[:-1, :], labels[1:, :]
            lhs_raw, rhs_raw = edge_raw[:-1, :], edge_raw[1:, :]
            lhs_struct, rhs_struct = edge_structural[:-1, :], edge_structural[1:, :]
            if alpha is not None:
                lhs_alpha, rhs_alpha = alpha[:-1, :], alpha[1:, :]

        mask = lhs_labels != rhs_labels
        if not np.any(mask):
            continue

        a_values = lhs_labels[mask]
        b_values = rhs_labels[mask]
        raw_values = np.maximum(lhs_raw[mask], rhs_raw[mask])
        structural_values = np.maximum(lhs_struct[mask], rhs_struct[mask])
        if alpha is None:
            alpha_hits = np.zeros(a_values.shape, dtype=bool)
        else:
            alpha_hits = np.abs(lhs_alpha[mask] - rhs_alpha[mask]) >= _ALPHA_EDGE_DELTA

        for a, b, raw_value, structural_value, alpha_hit in zip(
            a_values,
            b_values,
            raw_values,
            structural_values,
            alpha_hits,
            strict=True,
        ):
            add_pair(
                int(a),
                int(b),
                float(raw_value),
                float(structural_value),
                bool(alpha_hit),
            )

    return buckets


def build_region_graph_from_arrays(
    initial_labels: NDArray[np.integer],
    analysis_lab: NDArray[np.floating],
    edge_raw: NDArray[np.floating],
    edge_structural: NDArray[np.floating],
    *,
    subject_prob: NDArray[np.floating] | None = None,
    subject_confidence: NDArray[np.floating] | None = None,
    alpha: NDArray[np.floating] | None = None,
    annotations: Mapping[RegionId, RegionAnnotation] | None = None,
    gradient_bins: int = DEFAULT_GRADIENT_BINS,
) -> RegionGraph:
    labels = np.asarray(initial_labels, dtype=np.int32)
    height, width = _validate_analysis_inputs(
        labels,
        analysis_lab,
        edge_raw,
        edge_structural,
    )
    _validate_optional_map("subject_prob", subject_prob, (height, width))
    _validate_optional_map("subject_confidence", subject_confidence, (height, width))
    _validate_optional_map("alpha", alpha, (height, width))
    if gradient_bins <= 1:
        raise ValueError("gradient_bins must be greater than 1")

    stats = build_region_stats(
        labels,
        analysis_lab,
        subject_prob=subject_prob,
        subject_confidence=subject_confidence,
        annotations=annotations,
    )
    adjacency = {region_id: set() for region_id in stats}
    edges: dict[EdgeKey, RegionEdge] = {}

    for key, (
        raw_values,
        structural_values,
        alpha_hits,
        total,
    ) in _collect_boundaries(labels, edge_raw, edge_structural, alpha).items():
        a, b = key
        adjacency[a].add(b)
        adjacency[b].add(a)
        edges[key] = RegionEdge(
            a=a,
            b=b,
            shared_boundary_px=float(total),
            raw_gradient_hist=_boundary_histogram(
                np.asarray(raw_values),
                gradient_bins,
            ),
            structural_gradient_hist=_boundary_histogram(
                np.asarray(structural_values),
                gradient_bins,
            ),
            alpha_boundary_fraction=(alpha_hits / total) if total else 0.0,
        )

    return RegionGraph(
        nodes=stats,
        edges=edges,
        adjacency=adjacency,
        initial_labels=labels,
        next_region_id=max(stats) + 1,
    )


def build_region_graph(
    bundle: ImageBundle,
    labels: LabelMap,
    *,
    annotations: Mapping[RegionId, RegionAnnotation] | None = None,
    gradient_bins: int = DEFAULT_GRADIENT_BINS,
) -> RegionGraph:
    labels_array = np.asarray(labels)
    if labels_array.dtype != np.int32:
        raise ValueError("initial labels must have dtype int32")
    expected_shape = bundle.analysis_rgb.shape[:2]
    if labels_array.shape != expected_shape:
        raise ValueError("initial labels must match analysis resolution")
    region_ids = np.unique(labels_array)
    expected_ids = np.arange(region_ids.size, dtype=np.int32)
    if not np.array_equal(region_ids, expected_ids):
        raise ValueError("initial labels must be sequential from 0")
    if annotations is not None:
        unknown_annotations = set(annotations) - set(int(value) for value in region_ids)
        if unknown_annotations:
            raise ValueError(
                f"annotations reference unknown regions: {sorted(unknown_annotations)}"
            )
    graph = build_region_graph_from_arrays(
        labels_array,
        bundle.analysis_lab,
        bundle.edge_raw,
        bundle.edge_structural,
        subject_prob=bundle.subject_prob,
        subject_confidence=bundle.subject_confidence,
        alpha=bundle.alpha,
        annotations=annotations,
        gradient_bins=gradient_bins,
    )
    validate_graph(graph)
    return graph


def build_initial_merge_tree(graph: RegionGraph) -> RegionMergeTree:
    nodes = {
        region_id: MergeTreeNode(
            region_id=region_id,
            left_id=None,
            right_id=None,
            raw_merge_cost=0.0,
            hierarchy_height=0.0,
            stage="initial",
            stats=stats,
        )
        for region_id, stats in graph.nodes.items()
    }
    leaf_ids = frozenset(nodes)
    return RegionMergeTree(
        nodes=nodes,
        leaf_ids=leaf_ids,
        roots=set(nodes),
        merge_sequence=[],
    )


def _merge_supports(
    left: Sequence[CharacteristicSupport],
    right: Sequence[CharacteristicSupport],
) -> tuple[CharacteristicSupport, ...]:
    totals: dict[int, tuple[float, float]] = {}
    for support in (*left, *right):
        mass, weighted_confidence = totals.get(support.anchor_id, (0.0, 0.0))
        totals[support.anchor_id] = (
            mass + support.support_mass,
            weighted_confidence + support.support_mass * support.confidence,
        )

    merged = []
    for anchor_id in sorted(totals):
        mass, weighted_confidence = totals[anchor_id]
        confidence = weighted_confidence / mass if mass > 0.0 else 0.0
        merged.append(
            CharacteristicSupport(
                anchor_id=anchor_id,
                support_mass=mass,
                confidence=confidence,
            )
        )
    return tuple(merged)


def _merged_hull(
    left: NDArray[np.float32],
    right: NDArray[np.float32],
) -> tuple[NDArray[np.float32], float]:
    points = np.concatenate((left, right), axis=0).astype(np.float32, copy=False)
    hull = (
        cv2.convexHull(points, returnPoints=True)
        .reshape(-1, 2)
        .astype(np.float32, copy=False)
    )
    return hull, float(cv2.contourArea(hull))


def merge_region_stats(
    left: RegionStats,
    right: RegionStats,
    *,
    new_region_id: RegionId,
    shared_boundary_px: float,
) -> RegionStats:
    hull_xy, hull_area = _merged_hull(left.hull_xy, right.hull_xy)
    x0 = min(left.bbox[0], right.bbox[0])
    y0 = min(left.bbox[1], right.bbox[1])
    x1 = max(left.bbox[2], right.bbox[2])
    y1 = max(left.bbox[3], right.bbox[3])

    if left.semantic_tag is not None and left.semantic_tag == right.semantic_tag:
        semantic_tag = left.semantic_tag
        total_pixels = left.pixel_count + right.pixel_count
        semantic_confidence = (
            left.semantic_confidence * left.pixel_count
            + right.semantic_confidence * right.pixel_count
        ) / total_pixels
    else:
        semantic_tag = None
        semantic_confidence = 0.0

    return RegionStats(
        id=new_region_id,
        pixel_count=left.pixel_count + right.pixel_count,
        sum_lab=left.sum_lab + right.sum_lab,
        sum_sq_lab=left.sum_sq_lab + right.sum_sq_lab,
        sum_x=left.sum_x + right.sum_x,
        sum_y=left.sum_y + right.sum_y,
        sum_xx=left.sum_xx + right.sum_xx,
        sum_yy=left.sum_yy + right.sum_yy,
        sum_xy=left.sum_xy + right.sum_xy,
        bbox=(x0, y0, x1, y1),
        perimeter_px=(
            left.perimeter_px + right.perimeter_px - 2.0 * shared_boundary_px
        ),
        hull_xy=hull_xy,
        hull_area=hull_area,
        subject_prob_sum=left.subject_prob_sum + right.subject_prob_sum,
        subject_confidence_sum=(
            left.subject_confidence_sum + right.subject_confidence_sum
        ),
        characteristic_supports=_merge_supports(
            left.characteristic_supports,
            right.characteristic_supports,
        ),
        semantic_tag=semantic_tag,
        semantic_confidence=semantic_confidence,
    )


def merge_region_edges(
    edges: Sequence[RegionEdge],
    *,
    new_region_id: RegionId,
    neighbor_id: RegionId,
) -> RegionEdge:
    if not edges:
        raise ValueError("at least one region edge is required")

    hist_shape = edges[0].raw_gradient_hist.shape
    if any(edge.raw_gradient_hist.shape != hist_shape for edge in edges):
        raise ValueError("raw gradient histogram shapes must match")
    if any(edge.structural_gradient_hist.shape != hist_shape for edge in edges):
        raise ValueError("structural gradient histogram shapes must match")

    shared_boundary = sum(edge.shared_boundary_px for edge in edges)
    raw_hist = np.sum(
        [edge.raw_gradient_hist for edge in edges],
        axis=0,
        dtype=np.int64,
    )
    structural_hist = np.sum(
        [edge.structural_gradient_hist for edge in edges],
        axis=0,
        dtype=np.int64,
    )
    alpha_fraction = (
        sum(
            edge.alpha_boundary_fraction * edge.shared_boundary_px
            for edge in edges
        )
        / shared_boundary
    )

    return RegionEdge(
        a=new_region_id,
        b=neighbor_id,
        shared_boundary_px=shared_boundary,
        raw_gradient_hist=raw_hist,
        structural_gradient_hist=structural_hist,
        alpha_boundary_fraction=alpha_fraction,
    )


def apply_merge(
    graph: RegionGraph,
    tree: RegionMergeTree,
    left_id: RegionId,
    right_id: RegionId,
    *,
    raw_merge_cost: float,
    stage: str,
) -> RegionId:
    if not np.isfinite(raw_merge_cost) or raw_merge_cost < 0.0:
        raise ValueError("raw_merge_cost must be finite and non-negative")
    if not stage:
        raise ValueError("stage must not be empty")
    if left_id == right_id:
        raise ValueError("cannot merge a region with itself")
    if left_id not in graph.nodes or right_id not in graph.nodes:
        raise KeyError("both regions must be active graph nodes")

    separating_key = edge_key(left_id, right_id)
    if separating_key not in graph.edges:
        raise ValueError("regions must be adjacent")
    if left_id not in tree.roots or right_id not in tree.roots:
        raise ValueError("both regions must be active merge-tree roots")

    new_region_id = graph.next_region_id
    separating_edge = graph.edges[separating_key]
    new_stats = merge_region_stats(
        graph.nodes[left_id],
        graph.nodes[right_id],
        new_region_id=new_region_id,
        shared_boundary_px=separating_edge.shared_boundary_px,
    )

    neighbors = (
        graph.adjacency[left_id] | graph.adjacency[right_id]
    ) - {left_id, right_id}
    replacement_edges: dict[EdgeKey, RegionEdge] = {}
    for neighbor_id in neighbors:
        source_edges = []
        for source_id in (left_id, right_id):
            key = edge_key(source_id, neighbor_id)
            if key in graph.edges:
                source_edges.append(graph.edges[key])
        replacement = merge_region_edges(
            source_edges,
            new_region_id=new_region_id,
            neighbor_id=neighbor_id,
        )
        replacement_edges[edge_key(new_region_id, neighbor_id)] = replacement

    # Build all replacement data first, then mutate the active graph atomically.
    for region_id in (left_id, right_id):
        for neighbor_id in tuple(graph.adjacency[region_id]):
            graph.edges.pop(edge_key(region_id, neighbor_id), None)
            if neighbor_id in graph.adjacency:
                graph.adjacency[neighbor_id].discard(region_id)
        graph.adjacency.pop(region_id)
        graph.nodes.pop(region_id)

    graph.nodes[new_region_id] = new_stats
    graph.adjacency[new_region_id] = set(neighbors)
    for neighbor_id in neighbors:
        graph.adjacency[neighbor_id].add(new_region_id)
    graph.edges.update(replacement_edges)
    graph.next_region_id = new_region_id + 1

    left_tree = tree.nodes[left_id]
    right_tree = tree.nodes[right_id]
    hierarchy_height = max(
        raw_merge_cost,
        left_tree.hierarchy_height,
        right_tree.hierarchy_height,
    )
    tree.nodes[new_region_id] = MergeTreeNode(
        region_id=new_region_id,
        left_id=left_id,
        right_id=right_id,
        raw_merge_cost=raw_merge_cost,
        hierarchy_height=hierarchy_height,
        stage=stage,
        stats=new_stats,
    )
    tree.roots.discard(left_id)
    tree.roots.discard(right_id)
    tree.roots.add(new_region_id)
    tree.merge_sequence.append(new_region_id)

    return new_region_id


def validate_graph(graph: RegionGraph) -> None:
    if graph.initial_labels.flags.writeable:
        raise ValueError("initial_labels must be immutable")
    if graph.nodes and graph.next_region_id <= max(graph.nodes):
        raise ValueError("next_region_id must be greater than all active region ids")
    if set(graph.nodes) != set(graph.adjacency):
        raise ValueError("graph nodes and adjacency keys differ")

    for region_id, neighbors in graph.adjacency.items():
        for neighbor_id in neighbors:
            if neighbor_id not in graph.nodes:
                raise ValueError("adjacency references an inactive node")
            if region_id not in graph.adjacency[neighbor_id]:
                raise ValueError("adjacency must be symmetric")
            if edge_key(region_id, neighbor_id) not in graph.edges:
                raise ValueError("adjacency is missing a RegionEdge")

    for key, edge in graph.edges.items():
        if key != edge_key(edge.a, edge.b):
            raise ValueError("edge dictionary key is not canonical")
        if edge.a not in graph.nodes or edge.b not in graph.nodes:
            raise ValueError("edge references an inactive node")
        if (
            edge.b not in graph.adjacency[edge.a]
            or edge.a not in graph.adjacency[edge.b]
        ):
            raise ValueError("edge is missing from adjacency")

def validate_merge_tree(tree: RegionMergeTree) -> None:
    node_ids = set(tree.nodes)
    if not tree.leaf_ids <= node_ids:
        raise ValueError("leaf_ids must reference merge-tree nodes")
    if not tree.roots <= node_ids:
        raise ValueError("roots must reference merge-tree nodes")
    if len(tree.merge_sequence) != len(set(tree.merge_sequence)):
        raise ValueError("merge_sequence must not contain duplicates")

    parent_count = {region_id: 0 for region_id in node_ids}
    internal_ids: set[RegionId] = set()
    for region_id, node in tree.nodes.items():
        if node.region_id != region_id or node.stats.id != region_id:
            raise ValueError("merge-tree node ids must match dictionary keys and stats ids")
        is_leaf = node.left_id is None and node.right_id is None
        if is_leaf:
            if region_id not in tree.leaf_ids:
                raise ValueError("every childless merge-tree node must be a leaf")
            continue
        if node.left_id is None or node.right_id is None:
            raise ValueError("merge-tree nodes must have either zero or two children")
        internal_ids.add(region_id)
        for child_id in (node.left_id, node.right_id):
            if child_id not in tree.nodes:
                raise ValueError("merge-tree child references a missing node")
            if child_id == region_id:
                raise ValueError("merge-tree node cannot reference itself as a child")
            parent_count[child_id] += 1
            child = tree.nodes[child_id]
            if node.hierarchy_height + 1e-12 < child.hierarchy_height:
                raise ValueError("hierarchy_height must be monotonic")

    if set(tree.merge_sequence) != internal_ids:
        raise ValueError("merge_sequence must contain every internal node exactly once")
    if tree.leaf_ids & internal_ids:
        raise ValueError("leaf_ids must not contain internal nodes")
    expected_roots = {region_id for region_id, count in parent_count.items() if count == 0}
    if expected_roots != tree.roots:
        raise ValueError("roots must be exactly the parentless merge-tree nodes")
    if any(count > 1 for count in parent_count.values()):
        raise ValueError("merge-tree nodes may have at most one parent")
