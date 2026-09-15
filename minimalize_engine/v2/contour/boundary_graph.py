from __future__ import annotations

from collections import defaultdict, deque
from typing import DefaultDict

import numpy as np

from minimalize_engine.v2.contour.types import (
    BoundaryChain,
    BoundaryGraph,
    BoundaryVertex,
    ContourSimplificationConfig,
    OrientedChainRef,
)
from minimalize_engine.v2.region_merge.types import RegionMergeResult, RegionSelection
from minimalize_engine.v2.types import ImageBundle, RegionId

Coord = tuple[int, int]
Pair = tuple[int, int]
Edge = tuple[Coord, Coord]


def _edge_key(a: Coord, b: Coord) -> Edge:
    return (a, b) if a <= b else (b, a)


def _pair_key(a: int, b: int) -> Pair:
    return (a, b) if a <= b else (b, a)


def _add_segment(
    pair_edges: DefaultDict[Pair, set[Edge]],
    halfedge_dirs: dict[tuple[Pair, Edge, RegionId], tuple[Coord, Coord]],
    incident_regions: DefaultDict[Coord, set[RegionId]],
    a: Coord,
    b: Coord,
    side_a: int,
    side_b: int,
    orientations: dict[RegionId, tuple[Coord, Coord]],
) -> None:
    if side_a == side_b:
        return
    pair = _pair_key(side_a, side_b)
    edge = _edge_key(a, b)
    pair_edges[pair].add(edge)
    for region_id in (side_a, side_b):
        if region_id >= 0:
            incident_regions[a].add(region_id)
            incident_regions[b].add(region_id)
    for region_id, direction in orientations.items():
        if region_id >= 0:
            halfedge_dirs[(pair, edge, region_id)] = direction


def _extract_raw_segments(labels: np.ndarray):
    height, width = labels.shape
    pair_edges: DefaultDict[Pair, set[Edge]] = defaultdict(set)
    halfedge_dirs: dict[tuple[Pair, Edge, RegionId], tuple[Coord, Coord]] = {}
    incident_regions: DefaultDict[Coord, set[RegionId]] = defaultdict(set)
    for y in range(height):
        for x in range(width + 1):
            left = -1 if x == 0 else int(labels[y, x - 1])
            right = -1 if x == width else int(labels[y, x])
            top = (x, y)
            bottom = (x, y + 1)
            _add_segment(
                pair_edges, halfedge_dirs, incident_regions,
                top, bottom, left, right,
                {
                    left: (top, bottom),
                    right: (bottom, top),
                },
            )
    for y in range(height + 1):
        for x in range(width):
            top_region = -1 if y == 0 else int(labels[y - 1, x])
            bottom_region = -1 if y == height else int(labels[y, x])
            left_point = (x, y)
            right_point = (x + 1, y)
            _add_segment(
                pair_edges, halfedge_dirs, incident_regions,
                left_point, right_point, top_region, bottom_region,
                {
                    bottom_region: (left_point, right_point),
                    top_region: (right_point, left_point),
                },
            )
    return pair_edges, halfedge_dirs, incident_regions


def _edge_strength(bundle: ImageBundle, point: Coord) -> float:
    x, y = point
    height, width = bundle.edge_structural.shape
    values: list[float] = []
    for yy in (y - 1, y):
        for xx in (x - 1, x):
            if 0 <= yy < height and 0 <= xx < width:
                values.append(float(bundle.edge_structural[yy, xx]))
    return max(values, default=0.0)


def _selected_stats(merge_result: RegionMergeResult, region_id: RegionId):
    try:
        return merge_result.tree.nodes[region_id].stats
    except KeyError as exc:
        raise ValueError(f"selection references missing merge-tree region {region_id}") from exc


def _pair_protection_reasons(
    merge_result: RegionMergeResult,
    pair: Pair,
    config: ContourSimplificationConfig,
) -> tuple[str, ...]:
    regions = [region_id for region_id in pair if region_id >= 0]
    if len(regions) != 2:
        return ()
    a = _selected_stats(merge_result, regions[0])
    b = _selected_stats(merge_result, regions[1])
    reasons: list[str] = []

    high_a = {
        item.anchor_id for item in a.characteristic_supports
        if item.confidence >= config.characteristic_protection_confidence
    }
    high_b = {
        item.anchor_id for item in b.characteristic_supports
        if item.confidence >= config.characteristic_protection_confidence
    }
    if high_a and high_b and high_a.isdisjoint(high_b):
        reasons.append("characteristic_boundary")

    if (
        a.semantic_tag is not None
        and b.semantic_tag is not None
        and a.semantic_tag != b.semantic_tag
        and a.semantic_confidence >= config.semantic_protection_confidence
        and b.semantic_confidence >= config.semantic_protection_confidence
    ):
        reasons.append("semantic_boundary")
    return tuple(reasons)


def _pair_adjacency(edges: set[Edge]) -> dict[Coord, set[Coord]]:
    adjacency: DefaultDict[Coord, set[Coord]] = defaultdict(set)
    for a, b in edges:
        adjacency[a].add(b)
        adjacency[b].add(a)
    return dict(adjacency)


def _is_turn(point: Coord, neighbors: set[Coord]) -> bool:
    if len(neighbors) != 2:
        return False
    first, second = sorted(neighbors)
    v1 = (first[0] - point[0], first[1] - point[1])
    v2 = (second[0] - point[0], second[1] - point[1])
    return v1[0] * v2[1] != v1[1] * v2[0]


def _component_vertices(
    adjacency: dict[Coord, set[Coord]],
) -> list[set[Coord]]:
    remaining = set(adjacency)
    components: list[set[Coord]] = []
    while remaining:
        seed = min(remaining)
        queue = deque([seed])
        component: set[Coord] = set()
        while queue:
            point = queue.popleft()
            if point in component:
                continue
            component.add(point)
            queue.extend(sorted(adjacency[point] - component))
        remaining -= component
        components.append(component)
    return components


def _farthest_point(origin: Coord, points: set[Coord]) -> Coord:
    return max(
        points,
        key=lambda point: (
            (point[0] - origin[0]) ** 2 + (point[1] - origin[1]) ** 2,
            point,
        ),
    )


def _base_vertex_reasons(
    point: Coord,
    incident_regions: dict[Coord, set[RegionId]],
    width: int,
    height: int,
) -> set[str]:
    reasons: set[str] = set()
    x, y = point
    if len(incident_regions.get(point, set())) >= 3:
        reasons.add("multi_region_junction")
    if point in {(0, 0), (width, 0), (0, height), (width, height)}:
        reasons.add("image_corner")
    return reasons


def _split_vertices_for_pair(
    pair: Pair,
    adjacency: dict[Coord, set[Coord]],
    incident_regions: dict[Coord, set[RegionId]],
    bundle: ImageBundle,
    config: ContourSimplificationConfig,
    preset: str,
) -> tuple[set[Coord], dict[Coord, set[str]]]:
    height, width = bundle.analysis_rgb.shape[:2]
    split: set[Coord] = set()
    reasons: dict[Coord, set[str]] = {}
    for point, neighbors in adjacency.items():
        local = _base_vertex_reasons(point, incident_regions, width, height)
        if len(neighbors) != 2:
            local.add("boundary_junction")
        x, y = point
        on_border = x in (0, width) or y in (0, height)
        if on_border and pair[0] >= 0 and pair[1] >= 0:
            local.add("image_border_anchor")
        if (
            _is_turn(point, neighbors)
            and _edge_strength(bundle, point) >= config.strong_corner_threshold_for(preset)
        ):
            local.add("strong_structural_corner")
        if local:
            split.add(point)
            reasons[point] = local

    for component in _component_vertices(adjacency):
        component_split = split & component
        if len(component_split) >= 2:
            continue
        if not component:
            continue
        first = min(component_split) if component_split else min(component)
        if not component_split:
            split.add(first)
            reasons.setdefault(first, set()).add("cycle_anchor")
        if len(component) > 1:
            second = _farthest_point(first, component - {first})
            split.add(second)
            reasons.setdefault(second, set()).add("cycle_anchor")
    return split, reasons


def _trace_pair_chains(
    pair: Pair,
    edges: set[Edge],
    split_vertices: set[Coord],
) -> list[list[Coord]]:
    adjacency = _pair_adjacency(edges)
    visited: set[Edge] = set()
    chains: list[list[Coord]] = []

    for start in sorted(split_vertices):
        for neighbor in sorted(adjacency[start]):
            first_edge = _edge_key(start, neighbor)
            if first_edge in visited:
                continue
            points = [start]
            previous = start
            current = neighbor
            visited.add(first_edge)
            points.append(current)
            while current not in split_vertices:
                candidates = [
                    item for item in sorted(adjacency[current])
                    if item != previous and _edge_key(current, item) not in visited
                ]
                if not candidates:
                    break
                if len(candidates) > 1:
                    raise ValueError("boundary chain branches between protected vertices")
                nxt = candidates[0]
                visited.add(_edge_key(current, nxt))
                previous, current = current, nxt
                points.append(current)
            chains.append(points)

    if len(visited) != len(edges):
        missing = len(edges) - len(visited)
        raise ValueError(f"failed to trace {missing} boundary segments for pair {pair}")
    return chains


def _chain_orientation_for_region(
    pair: Pair,
    points: list[Coord],
    region_id: RegionId,
    halfedge_dirs: dict[tuple[Pair, Edge, RegionId], tuple[Coord, Coord]],
) -> bool:
    first_edge = _edge_key(points[0], points[1])
    direction = halfedge_dirs[(pair, first_edge, region_id)]
    if direction == (points[0], points[1]):
        return False
    if direction == (points[1], points[0]):
        return True
    raise ValueError("boundary half-edge direction is inconsistent with chain")


def build_boundary_graph(
    bundle: ImageBundle,
    merge_result: RegionMergeResult,
    selection: RegionSelection,
    *,
    config: ContourSimplificationConfig,
) -> BoundaryGraph:
    labels = selection.labels
    if labels.shape != bundle.analysis_rgb.shape[:2]:
        raise ValueError("selection labels must match analysis resolution")
    if set(int(value) for value in np.unique(labels)) != set(selection.region_ids):
        raise ValueError("selection label ids must match selection.region_ids")

    pair_edges, halfedge_dirs, incident_regions = _extract_raw_segments(labels)
    vertex_reasons_by_coord: DefaultDict[Coord, set[str]] = defaultdict(set)
    pending_chains: list[tuple[Pair, list[Coord], tuple[str, ...]]] = []
    for pair in sorted(pair_edges):
        adjacency = _pair_adjacency(pair_edges[pair])
        split, reasons = _split_vertices_for_pair(
            pair, adjacency, incident_regions, bundle, config, selection.preset
        )
        for point, local in reasons.items():
            vertex_reasons_by_coord[point].update(local)
        pair_reasons = _pair_protection_reasons(merge_result, pair, config)
        for points in _trace_pair_chains(pair, pair_edges[pair], split):
            pending_chains.append((pair, points, pair_reasons))

    endpoint_coords = sorted(
        {points[0] for _, points, _ in pending_chains}
        | {points[-1] for _, points, _ in pending_chains}
    )
    coord_to_vertex = {point: index for index, point in enumerate(endpoint_coords)}
    vertices = {
        vertex_id: BoundaryVertex(
            id=vertex_id,
            x=float(point[0]),
            y=float(point[1]),
            protected=bool(vertex_reasons_by_coord.get(point)),
            protection_reasons=tuple(sorted(vertex_reasons_by_coord.get(point, set()))),
        )
        for point, vertex_id in coord_to_vertex.items()
    }
    chains: dict[int, BoundaryChain] = {}
    region_chains: DefaultDict[RegionId, list[OrientedChainRef]] = defaultdict(list)
    for chain_id, (pair, points, pair_reasons) in enumerate(pending_chains):
        regions = tuple(region_id for region_id in pair if region_id >= 0)
        chain = BoundaryChain(
            id=chain_id,
            start_vertex=coord_to_vertex[points[0]],
            end_vertex=coord_to_vertex[points[-1]],
            points=np.asarray(points, dtype=np.float32),
            regions=regions,
            protected=bool(pair_reasons),
            protection_reasons=pair_reasons,
            original_point_count=len(points),
        )
        chains[chain_id] = chain
        for region_id in regions:
            region_chains[region_id].append(
                OrientedChainRef(
                    chain_id=chain_id,
                    reversed=_chain_orientation_for_region(
                        pair, points, region_id, halfedge_dirs
                    ),
                )
            )

    expected_regions = set(selection.region_ids)
    if set(region_chains) != expected_regions:
        missing = sorted(expected_regions - set(region_chains))
        raise ValueError(f"BoundaryGraph is missing selected regions: {missing}")
    for refs in region_chains.values():
        refs.sort(key=lambda ref: (ref.chain_id, ref.reversed))
    return BoundaryGraph(
        vertices=vertices,
        chains=chains,
        region_chains=dict(region_chains),
    )
