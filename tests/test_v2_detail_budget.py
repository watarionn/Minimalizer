from __future__ import annotations

from dataclasses import asdict, replace
import json

import numpy as np

from minimalize_engine.v2.contour import ContourSimplificationConfig, simplify_region_contours
from minimalize_engine.v2.detail_budget import (
    COLLAPSE_STYLE,
    HIDE_OVERLAY,
    RETAIN,
    DetailBudgetConfig,
    DetailBudgetPolicy,
    DetailShapeInfo,
    analyze_shape_importance,
    apply_detail_budget,
)
from minimalize_engine.v2.palette import PaletteConfig, consolidate_palette
from minimalize_engine.v2.preprocessing import build_image_bundle
from minimalize_engine.v2.primitive import PrimitiveFitConfig, fit_region_primitives
from minimalize_engine.v2.region_merge.graph import build_initial_merge_tree, build_region_graph_from_arrays
from minimalize_engine.v2.region_merge.types import HierarchyCut, RegionMergeMetrics, RegionMergeResult, RegionSelection
from minimalize_engine.v2.types import CharacteristicAnchor, CharacteristicContext


def _fixture(colors: list[tuple[int, int, int]], *, characteristic=None):
    height, stripe = 8, 6
    labels = np.empty((height, stripe * len(colors)), dtype=np.int32)
    image = np.empty((height, stripe * len(colors), 3), dtype=np.uint8)
    for region_id, color in enumerate(colors):
        x0, x1 = region_id * stripe, (region_id + 1) * stripe
        labels[:, x0:x1] = region_id
        image[:, x0:x1] = color
    bundle = build_image_bundle(image, analysis_max_side=max(labels.shape))
    graph = build_region_graph_from_arrays(
        labels, bundle.analysis_lab, bundle.edge_raw, bundle.edge_structural
    )
    tree = build_initial_merge_tree(graph)
    ids = frozenset(range(len(colors)))
    merge_result = RegionMergeResult(
        initial_labels=labels,
        tree=tree,
        initial_region_count=len(ids),
        safe_merge_count=0,
        hierarchy_merge_count=0,
        metrics=RegionMergeMetrics(len(graph.edges), 0, 0, 0, len(ids)),
    )
    cut = HierarchyCut(
        preset="detailed",
        selected_ids=ids,
        region_count=len(ids),
        visual_loss=0.0,
        normalized_visual_loss=0.0,
        objective=0.0,
        max_selected_hierarchy_height=0.0,
    )
    selection = RegionSelection("detailed", cut, labels, ids)
    contours = simplify_region_contours(
        bundle, merge_result, selection, config=ContourSimplificationConfig()
    )
    primitives = fit_region_primitives(
        bundle, selection, contours, config=PrimitiveFitConfig()
    )
    palette = consolidate_palette(
        bundle,
        selection,
        contours,
        primitives,
        characteristic=characteristic,
        config=PaletteConfig(mode="fixed", fixed_palette_size=len(ids)),
    )
    return bundle, selection, contours, primitives, palette


def _loose_config() -> DetailBudgetConfig:
    return DetailBudgetConfig(
        structural_mass_area_ratio=1.0,
        silhouette_protection_ratio=1.0,
        pose_protection_threshold=1.0,
        semantic_protection_confidence=1.0,
    )


def test_detail_budget_config_is_json_serializable():
    encoded = json.dumps(asdict(DetailBudgetConfig()))
    assert '"area_weight": 0.25' in encoded
    assert '"ultra_minimal_target": [20, 40]' in encoded


def test_importance_uses_declared_weighted_formula():
    bundle, selection, contours, primitives, palette = _fixture(
        [(120, 120, 120), (122, 122, 122)]
    )
    config = _loose_config()
    info = analyze_shape_importance(
        bundle, selection, contours, primitives, palette, config=config
    )
    item = info[0]
    expected = (
        0.25 * item.area_score
        + 0.20 * item.structural_score
        + 0.20 * item.characteristic_score
        + 0.15 * item.contrast_score
        + 0.10 * item.semantic_score
        + 0.10 * item.pose_score
    )
    assert item.importance == expected


def test_core_regions_collapse_style_without_hiding_coverage():
    bundle, selection, contours, primitives, palette = _fixture(
        [(120, 120, 120), (122, 122, 122), (124, 124, 124), (126, 126, 126)]
    )
    config = _loose_config()
    info = analyze_shape_importance(
        bundle, selection, contours, primitives, palette, config=config
    )
    policy = DetailBudgetPolicy("detailed", 1, 2, 1.0)
    result = apply_detail_budget(info, palette, policy=policy, config=config)
    assert result.metrics.visual_group_count <= 2
    assert result.metrics.collapsed_style_count >= 1
    assert result.metrics.hidden_overlay_count == 0
    assert all(action != HIDE_OVERLAY for action in result.actions.values())
    assert result.metrics.draw_geometry_count == len(info)


def test_protected_core_regions_allow_budget_overflow_instead_of_holes():
    bundle, selection, contours, primitives, palette = _fixture(
        [(30, 30, 30), (220, 220, 220)]
    )
    config = DetailBudgetConfig()
    info = analyze_shape_importance(
        bundle, selection, contours, primitives, palette, config=config
    )
    assert all(item.protected for item in info.values())
    result = apply_detail_budget(
        info, palette,
        policy=DetailBudgetPolicy("detailed", 1, 1, 1.0),
        config=config,
    )
    assert result.metrics.budget_overflow is True
    assert set(result.actions.values()) == {RETAIN}


def test_last_characteristic_support_is_protected():
    labels = np.zeros((8, 12), dtype=np.int32)
    labels[:, 6:] = 1
    anchor_map = np.full(labels.shape, -1, dtype=np.int32)
    anchor_map[:, :6] = 7
    characteristic = CharacteristicContext(
        anchors=(
            CharacteristicAnchor(
                7, np.asarray([50.0, 40.0, 30.0], dtype=np.float64), 0.95
            ),
        ),
        anchor_map=anchor_map,
    )
    bundle, selection, contours, primitives, palette = _fixture(
        [(120, 120, 120), (122, 122, 122)], characteristic=characteristic
    )
    config = _loose_config()
    info = analyze_shape_importance(
        bundle, selection, contours, primitives, palette, config=config
    )
    assert "last_characteristic_support" in info[0].protection_reasons
    result = apply_detail_budget(
        info, palette,
        policy=DetailBudgetPolicy("detailed", 1, 1, 1.0),
        config=config,
    )
    assert result.actions[0] == RETAIN


def test_overlay_can_hide_when_coverage_parent_is_known():
    bundle, selection, contours, primitives, palette = _fixture([(120, 120, 120)])
    config = _loose_config()
    info = dict(analyze_shape_importance(
        bundle, selection, contours, primitives, palette, config=config
    ))
    base = info[0]
    info[99] = DetailShapeInfo(
        region_id=99,
        palette_id=base.palette_id,
        area_ratio=0.01,
        area_score=0.01,
        structural_score=0.0,
        characteristic_score=0.0,
        contrast_score=0.0,
        semantic_score=0.0,
        pose_score=0.0,
        importance=0.01,
        overlay=True,
        coverage_parent_id=0,
    )
    result = apply_detail_budget(
        info, palette,
        policy=DetailBudgetPolicy("detailed", 1, 1, 1.0),
        config=config,
    )
    assert result.actions[99] == HIDE_OVERLAY
    assert result.fallback_region_by_region[99] == 0
    assert result.metrics.draw_geometry_count == 1


def test_protected_color_relationship_blocks_style_collapse():
    bundle, selection, contours, primitives, palette = _fixture(
        [(20, 20, 20), (235, 235, 235)]
    )
    config = _loose_config()
    info = analyze_shape_importance(
        bundle, selection, contours, primitives, palette, config=config
    )
    result = apply_detail_budget(
        info, palette,
        policy=DetailBudgetPolicy("detailed", 1, 1, 1.0),
        config=config,
    )
    assert result.metrics.budget_overflow is True
    assert set(result.actions.values()) == {RETAIN}


def test_detail_budget_is_deterministic():
    bundle, selection, contours, primitives, palette = _fixture(
        [(120, 120, 120), (122, 122, 122), (124, 124, 124)]
    )
    config = _loose_config()
    info = analyze_shape_importance(
        bundle, selection, contours, primitives, palette, config=config
    )
    policy = DetailBudgetPolicy("detailed", 1, 2, 1.0)
    first = apply_detail_budget(info, palette, policy=policy, config=config)
    second = apply_detail_budget(info, palette, policy=policy, config=config)
    assert dict(first.actions) == dict(second.actions)
    assert dict(first.effective_palette_by_region) == dict(second.effective_palette_by_region)
    assert first.metrics == second.metrics
