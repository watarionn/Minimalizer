from __future__ import annotations

from collections import Counter
from typing import Mapping

from minimalize_engine.v2.detail_budget.types import (
    COLLAPSE_STYLE,
    HIDE_OVERLAY,
    RETAIN,
    DetailBudgetConfig,
    DetailBudgetMetrics,
    DetailBudgetPolicy,
    DetailBudgetResult,
    DetailShapeInfo,
)
from minimalize_engine.v2.palette.sampling import ciede2000
from minimalize_engine.v2.palette.types import PaletteConsolidationResult, PaletteRelationship
from minimalize_engine.v2.types import RegionId


def _draw_geometry_count(
    info: Mapping[RegionId, DetailShapeInfo], actions: Mapping[RegionId, str]
) -> int:
    return sum(actions[region_id] != HIDE_OVERLAY for region_id in info)


def _visual_group_count(
    info: Mapping[RegionId, DetailShapeInfo],
    actions: Mapping[RegionId, str],
    palettes: Mapping[RegionId, int],
) -> int:
    core = {
        region_id for region_id, item in info.items()
        if not item.overlay and actions[region_id] != HIDE_OVERLAY
    }
    visited: set[RegionId] = set()
    groups = 0
    for start in sorted(core):
        if start in visited:
            continue
        groups += 1
        target_palette = palettes[start]
        stack = [start]
        visited.add(start)
        while stack:
            current = stack.pop()
            for other in info[current].neighbor_ids:
                if other not in core or other in visited:
                    continue
                if palettes[other] != target_palette:
                    continue
                visited.add(other)
                stack.append(other)
    groups += sum(
        item.overlay and actions[region_id] != HIDE_OVERLAY
        for region_id, item in info.items()
    )
    return groups


def _relationship_safe(
    relationship: PaletteRelationship,
    palettes: Mapping[RegionId, int],
    palette_result: PaletteConsolidationResult,
    config: DetailBudgetConfig,
) -> bool:
    entry_a = palette_result.entries[palettes[relationship.region_a]]
    entry_b = palette_result.entries[palettes[relationship.region_b]]
    assigned_delta_e = float(ciede2000(entry_a.lab, entry_b.lab))
    assigned_delta_l = float(entry_a.lab[0] - entry_b.lab[0])
    if "characteristic_anchor" in relationship.reasons:
        if assigned_delta_e <= config.anchor_equivalence_delta_e:
            return False
    if (
        relationship.original_delta_e >= config.contrast_original_delta_e
        and assigned_delta_e <= config.contrast_assigned_delta_e
    ):
        return False
    if abs(relationship.original_delta_l) >= config.significant_delta_l:
        if relationship.original_delta_l * assigned_delta_l < 0.0:
            return False
    return True


def _all_relationships_safe(
    palettes: Mapping[RegionId, int],
    palette_result: PaletteConsolidationResult,
    config: DetailBudgetConfig,
) -> bool:
    return all(
        _relationship_safe(item, palettes, palette_result, config)
        for item in palette_result.relationships
    )


def _anchor_support_counts(
    info: Mapping[RegionId, DetailShapeInfo],
    palettes: Mapping[RegionId, int],
    palette_result: PaletteConsolidationResult,
) -> Counter[int]:
    counts: Counter[int] = Counter()
    for region_id, item in info.items():
        entry = palette_result.entries[palettes[region_id]]
        for anchor_id in item.anchor_ids:
            if anchor_id in entry.anchor_ids:
                counts[anchor_id] += 1
    return counts


def _keeps_last_anchor_support(
    region_id: RegionId,
    candidate_palette: int,
    info: Mapping[RegionId, DetailShapeInfo],
    palettes: Mapping[RegionId, int],
    palette_result: PaletteConsolidationResult,
) -> bool:
    item = info[region_id]
    if not item.anchor_ids:
        return True
    current_entry = palette_result.entries[palettes[region_id]]
    candidate_entry = palette_result.entries[candidate_palette]
    counts = _anchor_support_counts(info, palettes, palette_result)
    for anchor_id in item.anchor_ids:
        currently_supports = anchor_id in current_entry.anchor_ids
        candidate_supports = anchor_id in candidate_entry.anchor_ids
        if currently_supports and not candidate_supports and counts[anchor_id] <= 1:
            return False
    return True


def _fallback_candidates(
    region_id: RegionId,
    info: Mapping[RegionId, DetailShapeInfo],
    palettes: Mapping[RegionId, int],
    palette_result: PaletteConsolidationResult,
) -> tuple[RegionId, ...]:
    source_lab = palette_result.region_samples[region_id].lab
    candidates: list[tuple[float, int]] = []
    for other in info[region_id].neighbor_ids:
        if other not in info or info[other].overlay:
            continue
        palette_id = palettes[other]
        if palette_id == palettes[region_id]:
            continue
        distance = float(ciede2000(source_lab, palette_result.entries[palette_id].lab))
        candidates.append((distance, other))
    candidates.sort(key=lambda item: (item[0], item[1]))
    return tuple(other for _, other in candidates)


def _can_consider(item: DetailShapeInfo, policy: DetailBudgetPolicy) -> bool:
    return (
        not item.protected
        and item.importance <= policy.collapse_importance_limit
    )


def apply_detail_budget(
    shape_info: Mapping[RegionId, DetailShapeInfo],
    palette_result: PaletteConsolidationResult,
    *,
    policy: DetailBudgetPolicy,
    config: DetailBudgetConfig,
) -> DetailBudgetResult:
    info = dict(shape_info)
    if not info:
        raise ValueError("detail budget requires at least one shape")
    core_ids = {region_id for region_id, item in info.items() if not item.overlay}
    if not set(palette_result.region_to_palette) <= core_ids:
        raise ValueError("palette regions must exist as core detail shapes")
    for item in info.values():
        if item.palette_id not in palette_result.entries:
            raise ValueError("detail shape references unknown palette entry")

    actions: dict[RegionId, str] = {region_id: RETAIN for region_id in info}
    palettes: dict[RegionId, int] = {
        region_id: item.palette_id for region_id, item in info.items()
    }
    fallbacks: dict[RegionId, RegionId | None] = {
        region_id: None for region_id in info
    }
    group_count = _visual_group_count(info, actions, palettes)

    overlays = sorted(
        (
            item for item in info.values()
            if item.overlay and _can_consider(item, policy)
        ),
        key=lambda item: (item.importance, item.area_ratio, item.region_id),
    )
    for item in overlays:
        if group_count <= policy.target_max:
            break
        actions[item.region_id] = HIDE_OVERLAY
        fallbacks[item.region_id] = item.coverage_parent_id
        group_count = _visual_group_count(info, actions, palettes)

    candidates = sorted(
        (
            item for item in info.values()
            if not item.overlay and _can_consider(item, policy)
        ),
        key=lambda item: (item.importance, item.area_ratio, item.region_id),
    )
    while group_count > policy.target_max:
        progressed = False
        for item in candidates:
            region_id = item.region_id
            if actions[region_id] != RETAIN:
                continue
            before = group_count
            for fallback_region in _fallback_candidates(
                region_id, info, palettes, palette_result
            ):
                candidate_palette = palettes[fallback_region]
                if not _keeps_last_anchor_support(
                    region_id, candidate_palette, info, palettes, palette_result
                ):
                    continue
                tentative = dict(palettes)
                tentative[region_id] = candidate_palette
                if not _all_relationships_safe(tentative, palette_result, config):
                    continue
                after = _visual_group_count(info, actions, tentative)
                if after >= before:
                    continue
                palettes = tentative
                actions[region_id] = COLLAPSE_STYLE
                fallbacks[region_id] = fallback_region
                group_count = after
                progressed = True
                break
            if group_count <= policy.target_max:
                break
        if not progressed:
            break

    if policy.preset in config.micro_detail_presets and group_count > policy.target_min:
        micro_candidates = sorted(
            (
                item for item in info.values()
                if not item.overlay and not item.protected
                and actions[item.region_id] == RETAIN
                and item.area_ratio <= config.micro_detail_area_ratio
                and item.importance <= config.micro_detail_importance_limit
            ),
            key=lambda item: (item.area_ratio, item.importance, item.region_id),
        )
        for item in micro_candidates:
            if group_count <= policy.target_min:
                break
            region_id = item.region_id
            before = group_count
            for fallback_region in _fallback_candidates(
                region_id, info, palettes, palette_result
            ):
                candidate_palette = palettes[fallback_region]
                if not _keeps_last_anchor_support(
                    region_id, candidate_palette, info, palettes, palette_result
                ):
                    continue
                tentative = dict(palettes)
                tentative[region_id] = candidate_palette
                if not _all_relationships_safe(tentative, palette_result, config):
                    continue
                after = _visual_group_count(info, actions, tentative)
                if after >= before or after < policy.target_min:
                    continue
                palettes = tentative
                actions[region_id] = COLLAPSE_STYLE
                fallbacks[region_id] = fallback_region
                group_count = after
                break

    if policy.preset in config.medium_detail_presets and group_count > policy.target_min:
        medium_candidates = sorted(
            (
                item for item in info.values()
                if not item.overlay and not item.protected
                and actions[item.region_id] == RETAIN
                and config.micro_detail_area_ratio < item.area_ratio
                and item.area_ratio <= config.medium_detail_area_ratio
                and item.importance <= config.medium_detail_importance_limit
            ),
            key=lambda item: (item.area_ratio, item.importance, item.region_id),
        )
        for item in medium_candidates:
            if group_count <= policy.target_min:
                break
            region_id = item.region_id
            before = group_count
            for fallback_region in _fallback_candidates(
                region_id, info, palettes, palette_result
            ):
                candidate_palette = palettes[fallback_region]
                if not _keeps_last_anchor_support(
                    region_id, candidate_palette, info, palettes, palette_result
                ):
                    continue
                tentative = dict(palettes)
                tentative[region_id] = candidate_palette
                if not _all_relationships_safe(tentative, palette_result, config):
                    continue
                after = _visual_group_count(info, actions, tentative)
                if after >= before or after < policy.target_min:
                    continue
                palettes = tentative
                actions[region_id] = COLLAPSE_STYLE
                fallbacks[region_id] = fallback_region
                group_count = after
                break

    metrics = DetailBudgetMetrics(
        draw_geometry_count=_draw_geometry_count(info, actions),
        visual_group_count=group_count,
        target_min=policy.target_min,
        target_max=policy.target_max,
        collapsed_style_count=sum(action == COLLAPSE_STYLE for action in actions.values()),
        hidden_overlay_count=sum(action == HIDE_OVERLAY for action in actions.values()),
        protected_shape_count=sum(item.protected for item in info.values()),
        budget_overflow=group_count > policy.target_max,
    )
    return DetailBudgetResult(
        shape_info=info,
        actions=actions,
        effective_palette_by_region=palettes,
        fallback_region_by_region=fallbacks,
        metrics=metrics,
    )
