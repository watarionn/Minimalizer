from __future__ import annotations

from dataclasses import dataclass
import heapq
from itertools import combinations

import numpy as np

from minimalize_engine.v2.contour.types import ContourSimplificationResult
from minimalize_engine.v2.palette.sampling import ciede2000
from minimalize_engine.v2.palette.types import (
    PaletteConfig,
    PaletteHierarchy,
    PaletteNode,
    PaletteRelationship,
    RegionColorSample,
)
from minimalize_engine.v2.region_merge.types import RegionSelection
from minimalize_engine.v2.types import CharacteristicContext, ImageBundle, RegionId


@dataclass(frozen=True, slots=True)
class PaletteMergeEvaluation:
    allowed: bool
    total_cost: float
    color_cost: float
    anchor_cost: float
    semantic_cost: float
    relationship_cost: float
    blocked_by: tuple[str, ...] = ()


def _pair_key(a: RegionId, b: RegionId) -> tuple[RegionId, RegionId]:
    return (a, b) if a < b else (b, a)


def _region_subject_stats(
    bundle: ImageBundle,
    selection: RegionSelection,
) -> dict[RegionId, tuple[float, float]]:
    if bundle.subject_prob is None:
        return {}
    result: dict[RegionId, tuple[float, float]] = {}
    for region_id in sorted(selection.region_ids):
        mask = selection.labels == region_id
        ratio = float(np.mean(bundle.subject_prob[mask], dtype=np.float64))
        if bundle.subject_confidence is None:
            confidence = 1.0
        else:
            confidence = float(np.mean(bundle.subject_confidence[mask], dtype=np.float64))
        result[region_id] = (ratio, confidence)
    return result


def _semantic_boundary(sample_a: RegionColorSample, sample_b: RegionColorSample, config: PaletteConfig) -> bool:
    return (
        sample_a.semantic_tag is not None
        and sample_b.semantic_tag is not None
        and sample_a.semantic_tag != sample_b.semantic_tag
        and sample_a.semantic_confidence >= config.semantic_confidence_threshold
        and sample_b.semantic_confidence >= config.semantic_confidence_threshold
    )


def build_palette_relationships(
    bundle: ImageBundle,
    selection: RegionSelection,
    contour_result: ContourSimplificationResult,
    samples: dict[RegionId, RegionColorSample],
    *,
    characteristic: CharacteristicContext | None,
    config: PaletteConfig,
) -> tuple[PaletteRelationship, ...]:
    pending: dict[tuple[RegionId, RegionId], tuple[set[str], float]] = {}

    def add(a: RegionId, b: RegionId, reason: str, protection: float) -> None:
        if a == b:
            return
        key = _pair_key(a, b)
        reasons, current = pending.get(key, (set(), 0.0))
        reasons.add(reason)
        pending[key] = (reasons, max(current, protection))

    total_pixels = float(selection.labels.size)
    major = {
        region_id
        for region_id, sample in samples.items()
        if sample.pixel_count / total_pixels >= config.major_region_area_ratio
    }
    subject_stats = _region_subject_stats(bundle, selection)
    graph = contour_result.boundary_graph
    for chain in graph.chains.values():
        if len(chain.regions) != 2:
            continue
        a, b = chain.regions
        if a in major and b in major:
            add(a, b, "adjacent_major", 0.80)
        if "characteristic_boundary" in chain.protection_reasons:
            add(a, b, "characteristic_boundary", 1.00)
        if "semantic_boundary" in chain.protection_reasons or _semantic_boundary(samples[a], samples[b], config):
            add(a, b, "semantic_boundary", 0.90)
        if a in subject_stats and b in subject_stats:
            ratio_a, conf_a = subject_stats[a]
            ratio_b, conf_b = subject_stats[b]
            subject_background = (
                conf_a >= config.subject_confidence_threshold
                and conf_b >= config.subject_confidence_threshold
                and (
                    (ratio_a >= config.subject_high_threshold and ratio_b <= config.subject_low_threshold)
                    or (ratio_b >= config.subject_high_threshold and ratio_a <= config.subject_low_threshold)
                )
            )
            if subject_background:
                add(a, b, "subject_background", 1.00)

    for a, b in combinations(sorted(major), 2):
        delta = float(ciede2000(samples[a].lab, samples[b].lab))
        if delta >= config.contrast_original_delta_e:
            add(a, b, "major_mass", 0.75)

    anchor_labs = {}
    if characteristic is not None:
        anchor_labs = {anchor.id: anchor.lab for anchor in characteristic.anchors}
    region_ids = sorted(samples)
    for index, a in enumerate(region_ids):
        if not samples[a].anchor_ids:
            continue
        for b in region_ids[index + 1:]:
            if not samples[b].anchor_ids:
                continue
            distinct = False
            for anchor_a in samples[a].anchor_ids:
                for anchor_b in samples[b].anchor_ids:
                    if anchor_a == anchor_b:
                        continue
                    if anchor_a not in anchor_labs or anchor_b not in anchor_labs:
                        continue
                    delta = float(ciede2000(anchor_labs[anchor_a], anchor_labs[anchor_b]))
                    if delta >= config.anchor_distinct_delta_e:
                        distinct = True
                        break
                if distinct:
                    break
            if distinct:
                add(a, b, "characteristic_anchor", 1.00)

    relationships: list[PaletteRelationship] = []
    for (a, b), (reasons, protection) in sorted(pending.items()):
        relationships.append(
            PaletteRelationship(
                region_a=a,
                region_b=b,
                original_delta_e=float(ciede2000(samples[a].lab, samples[b].lab)),
                original_delta_l=float(samples[a].lab[0] - samples[b].lab[0]),
                protection=protection,
                reasons=tuple(sorted(reasons)),
            )
        )
    return tuple(relationships)


def _anchor_cost(
    first: PaletteNode,
    second: PaletteNode,
    anchor_labs: dict[int, np.ndarray],
    config: PaletteConfig,
) -> tuple[float, bool]:
    if not first.anchor_ids and not second.anchor_ids:
        return 0.0, False
    if not first.anchor_ids or not second.anchor_ids:
        return 0.5, False
    distances: list[float] = []
    for anchor_a in first.anchor_ids:
        for anchor_b in second.anchor_ids:
            if anchor_a == anchor_b:
                distances.append(0.0)
                continue
            if anchor_a not in anchor_labs or anchor_b not in anchor_labs:
                continue
            distance = float(ciede2000(anchor_labs[anchor_a], anchor_labs[anchor_b]))
            if distance >= config.anchor_distinct_delta_e:
                return 1.0, True
            distances.append(distance)
    if not distances:
        return 0.5, False
    closest = min(distances)
    if closest <= config.anchor_equivalence_delta_e:
        return 0.0, False
    span = config.anchor_distinct_delta_e - config.anchor_equivalence_delta_e
    return min((closest - config.anchor_equivalence_delta_e) / span, 1.0), False


def _semantic_cost(first: PaletteNode, second: PaletteNode) -> float:
    a = set(first.semantic_tags)
    b = set(second.semantic_tags)
    if not a and not b:
        return 0.0
    if not a or not b:
        return 0.35
    union = a | b
    return 1.0 - len(a & b) / max(len(union), 1)


def _relationship_cost(
    first: PaletteNode,
    second: PaletteNode,
    relationships: tuple[PaletteRelationship, ...],
    config: PaletteConfig,
) -> tuple[float, bool]:
    left = set(first.member_regions)
    right = set(second.member_regions)
    risk = 0.0
    blocked = False
    for relationship in relationships:
        spans = (
            relationship.region_a in left and relationship.region_b in right
        ) or (
            relationship.region_b in left and relationship.region_a in right
        )
        if not spans:
            continue
        contrast = max(
            relationship.original_delta_e / config.contrast_original_delta_e,
            abs(relationship.original_delta_l) / config.significant_delta_l,
        )
        risk = max(risk, relationship.protection * min(contrast, 1.0))
        if relationship.protection >= 0.95 and (
            relationship.original_delta_e >= config.contrast_original_delta_e
            or abs(relationship.original_delta_l) >= config.significant_delta_l
        ):
            blocked = True
    return risk, blocked


def evaluate_palette_merge(
    first: PaletteNode,
    second: PaletteNode,
    relationships: tuple[PaletteRelationship, ...],
    anchor_labs: dict[int, np.ndarray],
    config: PaletteConfig,
    *,
    color_distance: float | None = None,
) -> PaletteMergeEvaluation:
    if color_distance is None:
        color_distance = float(ciede2000(first.lab, second.lab))
    color_cost = min(color_distance / config.color_distance_scale, 1.0)
    anchor_cost, anchor_block = _anchor_cost(first, second, anchor_labs, config)
    semantic_cost = _semantic_cost(first, second)
    relationship_cost, relationship_block = _relationship_cost(
        first, second, relationships, config
    )
    blocked_by: list[str] = []
    if anchor_block:
        blocked_by.append("anchor_conflict")
    if relationship_block:
        blocked_by.append("protected_relationship")
    total_weight = (
        config.color_weight + config.anchor_weight
        + config.semantic_weight + config.relationship_weight
    )
    total_cost = (
        config.color_weight * color_cost
        + config.anchor_weight * anchor_cost
        + config.semantic_weight * semantic_cost
        + config.relationship_weight * relationship_cost
    ) / total_weight
    return PaletteMergeEvaluation(
        allowed=not blocked_by,
        total_cost=float(total_cost),
        color_cost=float(color_cost),
        anchor_cost=float(anchor_cost),
        semantic_cost=float(semantic_cost),
        relationship_cost=float(relationship_cost),
        blocked_by=tuple(blocked_by),
    )


def _pairwise_region_distances(
    samples: dict[RegionId, RegionColorSample],
) -> tuple[list[RegionId], dict[RegionId, int], np.ndarray]:
    region_ids = sorted(samples)
    index = {region_id: position for position, region_id in enumerate(region_ids)}
    colors = np.asarray([samples[region_id].lab for region_id in region_ids], dtype=np.float64)
    distances = ciede2000(colors[:, None, :], colors[None, :, :])
    return region_ids, index, np.asarray(distances, dtype=np.float64)


def _representative_region(
    member_regions: tuple[RegionId, ...],
    samples: dict[RegionId, RegionColorSample],
    region_index: dict[RegionId, int],
    distances: np.ndarray,
) -> RegionId:
    positions = np.asarray([region_index[region_id] for region_id in member_regions], dtype=np.int64)
    weights = np.asarray([samples[region_id].pixel_count for region_id in member_regions], dtype=np.float64)
    local = distances[np.ix_(positions, positions)]
    totals = local @ weights
    minimum = float(np.min(totals))
    candidates = [
        member_regions[index]
        for index, value in enumerate(totals)
        if np.isclose(float(value), minimum, rtol=0.0, atol=1e-12)
    ]
    return min(candidates)


def _leaf_node(
    node_id: int,
    sample: RegionColorSample,
    config: PaletteConfig,
) -> PaletteNode:
    tags = ()
    if sample.semantic_tag is not None and sample.semantic_confidence >= config.semantic_confidence_threshold:
        tags = (sample.semantic_tag,)
    return PaletteNode(
        id=node_id,
        left_id=None,
        right_id=None,
        member_regions=(sample.region_id,),
        representative_region_id=sample.region_id,
        lab=sample.lab,
        rgb=sample.rgb,
        source_xy=sample.source_xy,
        anchor_ids=sample.anchor_ids,
        semantic_tags=tags,
    )


def _merged_node(
    node_id: int,
    first: PaletteNode,
    second: PaletteNode,
    evaluation: PaletteMergeEvaluation,
    samples: dict[RegionId, RegionColorSample],
    region_index: dict[RegionId, int],
    distances: np.ndarray,
) -> PaletteNode:
    members = tuple(sorted(first.member_regions + second.member_regions))
    representative = _representative_region(
        members, samples, region_index, distances
    )
    sample = samples[representative]
    return PaletteNode(
        id=node_id,
        left_id=first.id,
        right_id=second.id,
        member_regions=members,
        representative_region_id=representative,
        lab=sample.lab,
        rgb=sample.rgb,
        source_xy=sample.source_xy,
        merge_cost=evaluation.total_cost,
        hierarchy_height=max(
            evaluation.total_cost, first.hierarchy_height, second.hierarchy_height
        ),
        anchor_ids=tuple(sorted(set(first.anchor_ids) | set(second.anchor_ids))),
        semantic_tags=tuple(sorted(set(first.semantic_tags) | set(second.semantic_tags))),
    )


def build_palette_hierarchy(
    samples: dict[RegionId, RegionColorSample],
    relationships: tuple[PaletteRelationship, ...],
    *,
    characteristic: CharacteristicContext | None,
    config: PaletteConfig,
) -> PaletteHierarchy:
    if not samples:
        raise ValueError("palette hierarchy requires region color samples")
    region_ids, region_index, distances = _pairwise_region_distances(samples)
    nodes = {
        node_id: _leaf_node(node_id, samples[region_id], config)
        for node_id, region_id in enumerate(region_ids)
    }
    leaf_ids = frozenset(nodes)
    active = set(nodes)
    next_id = len(nodes)
    merge_sequence: list[int] = []
    anchor_labs = {}
    if characteristic is not None:
        anchor_labs = {anchor.id: anchor.lab for anchor in characteristic.anchors}
    heap: list[tuple[float, int, int]] = []
    def push_pair(a: int, b: int) -> None:
        if a == b:
            return
        left, right = (a, b) if a < b else (b, a)
        color_distance = float(
            distances[
                region_index[nodes[left].representative_region_id],
                region_index[nodes[right].representative_region_id],
            ]
        )
        evaluation = evaluate_palette_merge(
            nodes[left], nodes[right], relationships, anchor_labs, config,
            color_distance=color_distance,
        )
        if evaluation.allowed:
            heapq.heappush(heap, (evaluation.total_cost, left, right))

    for left, right in combinations(sorted(active), 2):
        push_pair(left, right)

    while heap:
        _, left_id, right_id = heapq.heappop(heap)
        if left_id not in active or right_id not in active:
            continue
        color_distance = float(
            distances[
                region_index[nodes[left_id].representative_region_id],
                region_index[nodes[right_id].representative_region_id],
            ]
        )
        evaluation = evaluate_palette_merge(
            nodes[left_id], nodes[right_id], relationships, anchor_labs, config,
            color_distance=color_distance,
        )
        if not evaluation.allowed:
            continue
        node = _merged_node(
            next_id,
            nodes[left_id],
            nodes[right_id],
            evaluation,
            samples,
            region_index,
            distances,
        )
        nodes[next_id] = node
        active.remove(left_id)
        active.remove(right_id)
        active.add(next_id)
        merge_sequence.append(next_id)
        created_id = next_id
        next_id += 1
        for other_id in sorted(active - {created_id}):
            push_pair(created_id, other_id)

    return PaletteHierarchy(
        nodes=nodes,
        leaf_ids=leaf_ids,
        roots=set(active),
        merge_sequence=merge_sequence,
    )
