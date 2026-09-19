from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import math

import numpy as np

from minimalize_engine.v2.types import RegionId
from minimalize_engine.v2.region_merge.types import (
    CutPolicy,
    HierarchyCut,
    HierarchyCutFamily,
    RegionMergeResult,
    RegionMergeTree,
    RegionSelection,
)

_PRESET_ORDER = ("detailed", "balanced", "minimal", "ultra_minimal")


def default_cut_policies() -> dict[str, CutPolicy]:
    return {
        "detailed": CutPolicy(100, 170, 0.40, 0.80),
        "balanced": CutPolicy(65, 110, 0.55, 1.25),
        # Approved-78 calibration: 24 shapes was too aggressive corpus-wide.
        # A 40-shape ceiling removes roughly half of the old Minimal complexity
        # while preserving substantially more silhouette and edge structure.
        "minimal": CutPolicy(24, 40, 1.00, 1.10, target_weight=1.10),
        # Keep the preset family monotonic below the calibrated Minimal range.
        "ultra_minimal": CutPolicy(12, 20, 1.30, 1.25, target_weight=1.35),
    }

@dataclass(frozen=True, slots=True)
class _NodePlan:
    visual_loss: float
    select_self: bool
    left_count: int = 0
    right_count: int = 0


@dataclass(frozen=True, slots=True)
class _ForestPlan:
    visual_loss: float
    previous_count: int
    root_count: int


def _protection_weight(node, policy: CutPolicy) -> float:
    stats = node.stats
    anchor_confidence = max(
        (support.confidence for support in stats.characteristic_supports),
        default=0.0,
    )
    return 1.0 + (
        policy.anchor_protection_weight * anchor_confidence
        + policy.semantic_protection_weight * stats.semantic_confidence
        + policy.subject_protection_weight * stats.subject_confidence
    )

def cumulative_visual_loss(
    tree: RegionMergeTree,
    *,
    total_pixels: int,
    policy: CutPolicy,
) -> dict[RegionId, float]:
    if total_pixels <= 0:
        raise ValueError("total_pixels must be positive")
    losses: dict[RegionId, float] = {leaf_id: 0.0 for leaf_id in tree.leaf_ids}
    for region_id in tree.merge_sequence:
        node = tree.nodes[region_id]
        assert node.left_id is not None and node.right_id is not None
        area_ratio = node.stats.pixel_count / float(total_pixels)
        merge_loss = (
            node.raw_merge_cost
            * math.sqrt(max(area_ratio, 0.0))
            * _protection_weight(node, policy)
        )
        losses[region_id] = losses[node.left_id] + losses[node.right_id] + merge_loss
    if set(losses) != set(tree.nodes):
        raise ValueError("merge-tree sequence does not cover every node")
    return losses


def _minimum_feasible_counts(
    tree: RegionMergeTree,
    policy: CutPolicy,
    atomic_ids: frozenset[RegionId],
) -> dict[RegionId, int]:
    counts = {leaf_id: 1 for leaf_id in tree.leaf_ids}
    for region_id in tree.merge_sequence:
        node = tree.nodes[region_id]
        if region_id in atomic_ids:
            counts[region_id] = 1
            continue
        assert node.left_id is not None and node.right_id is not None
        if node.hierarchy_height <= policy.max_hierarchy_height:
            counts[region_id] = 1
        else:
            counts[region_id] = counts[node.left_id] + counts[node.right_id]
    return counts

def _combine_states(
    left: Mapping[int, _NodePlan],
    right: Mapping[int, _NodePlan],
    *,
    cap: int,
) -> dict[int, _NodePlan]:
    combined: dict[int, _NodePlan] = {}
    for left_count, left_plan in left.items():
        for right_count, right_plan in right.items():
            count = left_count + right_count
            if count > cap:
                continue
            loss = left_plan.visual_loss + right_plan.visual_loss
            current = combined.get(count)
            if current is None or loss < current.visual_loss - 1e-15:
                combined[count] = _NodePlan(
                    visual_loss=loss,
                    select_self=False,
                    left_count=left_count,
                    right_count=right_count,
                )
    return combined


def _build_node_states(
    tree: RegionMergeTree,
    losses: Mapping[RegionId, float],
    policy: CutPolicy,
    atomic_ids: frozenset[RegionId],
    cap: int,
) -> dict[RegionId, dict[int, _NodePlan]]:
    states: dict[RegionId, dict[int, _NodePlan]] = {
        leaf_id: {1: _NodePlan(0.0, True)} for leaf_id in tree.leaf_ids
    }
    for region_id in tree.merge_sequence:
        node = tree.nodes[region_id]
        if region_id in atomic_ids:
            states[region_id] = {1: _NodePlan(losses[region_id], True)}
            continue
        assert node.left_id is not None and node.right_id is not None
        merged = _combine_states(
            states[node.left_id], states[node.right_id], cap=cap
        )
        if node.hierarchy_height <= policy.max_hierarchy_height:
            selected = _NodePlan(losses[region_id], True)
            current = merged.get(1)
            if current is None or selected.visual_loss < current.visual_loss:
                merged[1] = selected
        if not merged:
            raise ValueError("no feasible hierarchy-cut state for merge-tree node")
        states[region_id] = merged
    return states

def _combine_forest_states(
    root_ids: tuple[RegionId, ...],
    states: Mapping[RegionId, Mapping[int, _NodePlan]],
    *,
    cap: int,
) -> tuple[list[dict[int, _ForestPlan]], dict[int, float]]:
    stages: list[dict[int, _ForestPlan]] = []
    losses: dict[int, float] = {0: 0.0}
    for root_id in root_ids:
        next_losses: dict[int, float] = {}
        stage: dict[int, _ForestPlan] = {}
        for previous_count, previous_loss in losses.items():
            for root_count, root_plan in states[root_id].items():
                count = previous_count + root_count
                if count > cap:
                    continue
                loss = previous_loss + root_plan.visual_loss
                if count not in next_losses or loss < next_losses[count] - 1e-15:
                    next_losses[count] = loss
                    stage[count] = _ForestPlan(loss, previous_count, root_count)
        if not next_losses:
            raise ValueError("no feasible hierarchy-cut state for merge-tree forest")
        stages.append(stage)
        losses = next_losses
    return stages, losses

def _target_penalty(count: int, policy: CutPolicy) -> float:
    if policy.target_min <= count <= policy.target_max:
        return 0.0
    if count < policy.target_min:
        return (policy.target_min - count) / float(policy.target_min)
    return (count - policy.target_max) / float(policy.target_max)


def _objective(
    *,
    count: int,
    visual_loss: float,
    total_visual_loss: float,
    initial_region_count: int,
    policy: CutPolicy,
) -> tuple[float, float]:
    normalized_loss = (
        visual_loss / total_visual_loss if total_visual_loss > 1e-15 else 0.0
    )
    normalized_count = count / float(initial_region_count)
    objective = (
        normalized_loss
        + policy.complexity_lambda * normalized_count
        + policy.target_weight * _target_penalty(count, policy)
    )
    return normalized_loss, objective

def _reconstruct_selected(
    tree: RegionMergeTree,
    states: Mapping[RegionId, Mapping[int, _NodePlan]],
    root_counts: Mapping[RegionId, int],
) -> frozenset[RegionId]:
    selected: set[RegionId] = set()
    stack = list(root_counts.items())
    while stack:
        region_id, count = stack.pop()
        plan = states[region_id][count]
        if plan.select_self:
            selected.add(region_id)
            continue
        node = tree.nodes[region_id]
        if node.left_id is None or node.right_id is None:
            raise ValueError("split plan cannot reference a leaf")
        stack.append((node.left_id, plan.left_count))
        stack.append((node.right_id, plan.right_count))
    return frozenset(selected)


def _reconstruct_root_counts(
    root_ids: tuple[RegionId, ...],
    stages: list[dict[int, _ForestPlan]],
    final_count: int,
) -> dict[RegionId, int]:
    counts: dict[RegionId, int] = {}
    current = final_count
    for root_id, stage in zip(reversed(root_ids), reversed(stages), strict=True):
        plan = stage[current]
        counts[root_id] = plan.root_count
        current = plan.previous_count
    if current != 0:
        raise ValueError("invalid forest cut reconstruction")
    return counts

def _build_cut(
    merge_result: RegionMergeResult,
    *,
    preset: str,
    policy: CutPolicy,
    atomic_ids: frozenset[RegionId],
) -> HierarchyCut:
    tree = merge_result.tree
    total_pixels = int(merge_result.initial_labels.size)
    losses = cumulative_visual_loss(tree, total_pixels=total_pixels, policy=policy)
    minimums = _minimum_feasible_counts(tree, policy, atomic_ids)
    root_ids = tuple(sorted(tree.roots))
    min_count = sum(minimums[root_id] for root_id in root_ids)
    desired_cap = max(policy.target_max * 2, policy.target_max + 64)
    cap = max(min_count, min(merge_result.initial_region_count, desired_cap))
    states = _build_node_states(tree, losses, policy, atomic_ids, cap)
    stages, forest_losses = _combine_forest_states(root_ids, states, cap=cap)
    total_visual_loss = sum(losses[root_id] for root_id in root_ids)
    scored: list[tuple[float, float, int, float, float]] = []
    for count, visual_loss in forest_losses.items():
        normalized_loss, objective = _objective(
            count=count,
            visual_loss=visual_loss,
            total_visual_loss=total_visual_loss,
            initial_region_count=merge_result.initial_region_count,
            policy=policy,
        )
        scored.append((objective, _target_penalty(count, policy), count, visual_loss, normalized_loss))
    if not scored:
        raise ValueError("no feasible hierarchy cut")
    objective, _, count, visual_loss, normalized_loss = min(scored)
    root_counts = _reconstruct_root_counts(root_ids, stages, count)
    selected = _reconstruct_selected(tree, states, root_counts)
    max_height = max(tree.nodes[region_id].hierarchy_height for region_id in selected)
    if max_height > policy.max_hierarchy_height + 1e-12:
        raise ValueError("selected cut exceeds hierarchy-height guard")
    return HierarchyCut(
        preset=preset,
        selected_ids=selected,
        region_count=count,
        visual_loss=visual_loss,
        normalized_visual_loss=normalized_loss,
        objective=objective,
        max_selected_hierarchy_height=max_height,
    )

def _parent_map(tree: RegionMergeTree) -> dict[RegionId, RegionId | None]:
    parents: dict[RegionId, RegionId | None] = {
        region_id: None for region_id in tree.nodes
    }
    for region_id in tree.merge_sequence:
        node = tree.nodes[region_id]
        assert node.left_id is not None and node.right_id is not None
        parents[node.left_id] = region_id
        parents[node.right_id] = region_id
    return parents

def _assert_nested_pair(
    tree: RegionMergeTree,
    finer: HierarchyCut,
    coarser: HierarchyCut,
) -> None:
    parents = _parent_map(tree)
    coarse_ids = set(coarser.selected_ids)
    for region_id in finer.selected_ids:
        current: RegionId | None = region_id
        while current is not None and current not in coarse_ids:
            current = parents[current]
        if current is None:
            raise ValueError(
                f"cut {coarser.preset} is not an ancestral coarsening of {finer.preset}"
            )
    if coarser.region_count > finer.region_count:
        raise ValueError("coarser cut cannot contain more regions than finer cut")

def validate_cut_family(
    merge_result: RegionMergeResult,
    family: HierarchyCutFamily,
) -> None:
    cuts = (
        family.detailed,
        family.balanced,
        family.minimal,
        family.ultra_minimal,
    )
    if tuple(cut.preset for cut in cuts) != _PRESET_ORDER:
        raise ValueError("cut family presets are not in canonical order")
    for finer, coarser in zip(cuts, cuts[1:]):
        _assert_nested_pair(merge_result.tree, finer, coarser)


def _validate_policy_order(policies: Mapping[str, CutPolicy]) -> None:
    missing = set(_PRESET_ORDER) - set(policies)
    if missing:
        raise ValueError(f"missing cut policies: {sorted(missing)}")
    ordered = [policies[name] for name in _PRESET_ORDER]
    target_mins = [policy.target_min for policy in ordered]
    target_maxs = [policy.target_max for policy in ordered]
    if any(left < right for left, right in zip(target_mins, target_mins[1:])):
        raise ValueError("coarser presets must not raise target_min")
    if any(left < right for left, right in zip(target_maxs, target_maxs[1:])):
        raise ValueError("coarser presets must not raise target_max")
    heights = [policy.max_hierarchy_height for policy in ordered]
    if any(left > right for left, right in zip(heights, heights[1:])):
        raise ValueError("coarser presets must not lower the hierarchy-height guard")

def build_cut_family(
    merge_result: RegionMergeResult,
    *,
    policies: Mapping[str, CutPolicy] | None = None,
) -> HierarchyCutFamily:
    active_policies = default_cut_policies() if policies is None else dict(policies)
    _validate_policy_order(active_policies)

    cuts: dict[str, HierarchyCut] = {}
    atomic_ids: frozenset[RegionId] = frozenset()
    for preset in _PRESET_ORDER:
        cut = _build_cut(
            merge_result,
            preset=preset,
            policy=active_policies[preset],
            atomic_ids=atomic_ids,
        )
        cuts[preset] = cut
        atomic_ids = cut.selected_ids

    family = HierarchyCutFamily(
        detailed=cuts["detailed"],
        balanced=cuts["balanced"],
        minimal=cuts["minimal"],
        ultra_minimal=cuts["ultra_minimal"],
    )
    validate_cut_family(merge_result, family)
    return family

def _leaf_to_selected_lut(
    merge_result: RegionMergeResult,
    cut: HierarchyCut,
) -> np.ndarray:
    tree = merge_result.tree
    lut = np.full(merge_result.initial_region_count, -1, dtype=np.int64)
    for selected_id in cut.selected_ids:
        stack = [selected_id]
        while stack:
            region_id = stack.pop()
            node = tree.nodes[region_id]
            if node.left_id is None:
                if region_id >= merge_result.initial_region_count:
                    raise ValueError("invalid leaf id")
                if lut[region_id] != -1:
                    raise ValueError("cut regions overlap")
                lut[region_id] = selected_id
                continue
            if node.right_id is None:
                raise ValueError("internal node is missing a child")
            stack.append(node.left_id)
            stack.append(node.right_id)
    if np.any(lut < 0):
        raise ValueError("cut does not cover all leaves")
    return lut


def materialize_region_selection(
    merge_result: RegionMergeResult,
    cut: HierarchyCut,
) -> RegionSelection:
    if not cut.selected_ids <= set(merge_result.tree.nodes):
        raise ValueError("cut references unknown merge-tree nodes")
    lut = _leaf_to_selected_lut(merge_result, cut)
    max_selected_id = int(lut.max())
    if max_selected_id > np.iinfo(np.int32).max:
        raise OverflowError("selected region id exceeds int32 range")
    labels = lut[merge_result.initial_labels].astype(np.int32, copy=False)
    return RegionSelection(
        preset=cut.preset,
        cut=cut,
        labels=labels,
        region_ids=cut.selected_ids,
    )
