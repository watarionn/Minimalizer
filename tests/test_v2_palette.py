from __future__ import annotations

from dataclasses import asdict, replace
import json

import numpy as np
import pytest

from minimalize_engine.v2.contour import ContourSimplificationConfig, simplify_region_contours
from minimalize_engine.v2.palette import PaletteConfig, ciede2000, consolidate_palette
from minimalize_engine.v2.palette.hierarchy import evaluate_palette_merge
from minimalize_engine.v2.palette.sampling import sample_region_colors
from minimalize_engine.v2.palette.types import PaletteNode
from minimalize_engine.v2.preprocessing import build_image_bundle
from minimalize_engine.v2.primitive import PrimitiveFitConfig, fit_region_primitives
from minimalize_engine.v2.region_merge.graph import (
    build_initial_merge_tree,
    build_region_graph_from_arrays,
)
from minimalize_engine.v2.region_merge.types import (
    HierarchyCut,
    RegionMergeMetrics,
    RegionMergeResult,
    RegionSelection,
)
from minimalize_engine.v2.types import CharacteristicAnchor, CharacteristicContext


def _pipeline_fixture(labels: np.ndarray, image: np.ndarray, *, preset: str = "detailed"):
    bundle = build_image_bundle(image, analysis_max_side=max(labels.shape))
    graph = build_region_graph_from_arrays(
        labels,
        bundle.analysis_lab,
        bundle.edge_raw,
        bundle.edge_structural,
    )
    tree = build_initial_merge_tree(graph)
    region_ids = frozenset(int(value) for value in np.unique(labels))
    metrics = RegionMergeMetrics(
        initial_edge_count=len(graph.edges),
        evaluation_count=0,
        blocked_evaluation_count=0,
        safe_candidate_count=0,
        final_root_count=len(region_ids),
    )
    merge_result = RegionMergeResult(
        initial_labels=labels,
        tree=tree,
        initial_region_count=len(region_ids),
        safe_merge_count=0,
        hierarchy_merge_count=0,
        metrics=metrics,
    )
    cut = HierarchyCut(
        preset=preset,
        selected_ids=region_ids,
        region_count=len(region_ids),
        visual_loss=0.0,
        normalized_visual_loss=0.0,
        objective=0.0,
        max_selected_hierarchy_height=0.0,
    )
    selection = RegionSelection(
        preset=preset,
        cut=cut,
        labels=labels,
        region_ids=region_ids,
    )
    contours = simplify_region_contours(
        bundle,
        merge_result,
        selection,
        config=ContourSimplificationConfig(),
    )
    primitives = fit_region_primitives(
        bundle,
        selection,
        contours,
        config=PrimitiveFitConfig(),
    )
    return bundle, selection, contours, primitives


def _vertical_fixture(colors: list[tuple[int, int, int]], *, height: int = 8, stripe: int = 5):
    width = stripe * len(colors)
    labels = np.empty((height, width), dtype=np.int32)
    image = np.empty((height, width, 3), dtype=np.uint8)
    for region_id, color in enumerate(colors):
        x0, x1 = region_id * stripe, (region_id + 1) * stripe
        labels[:, x0:x1] = region_id
        image[:, x0:x1] = color
    return labels, image


def test_ciede2000_matches_reference_pair():
    first = np.asarray([50.0, 2.6772, -79.7751], dtype=np.float64)
    second = np.asarray([50.0, 0.0, -82.7485], dtype=np.float64)
    assert float(ciede2000(first, second)) == pytest.approx(2.0425, abs=1e-4)


def test_palette_config_is_json_serializable():
    encoded = json.dumps(asdict(PaletteConfig()))
    assert '"mode": "auto"' in encoded


def test_precomputed_palette_distance_matches_direct_evaluation_bit_exact():
    first = PaletteNode(0, None, None, (0,), 0, np.asarray([51.0, 22.0, -18.0]), (120, 80, 70), (0, 0))
    second = PaletteNode(1, None, None, (1,), 1, np.asarray([63.0, -12.0, 31.0]), (80, 130, 170), (1, 0))
    colors = np.stack((first.lab, second.lab))
    matrix = np.asarray(ciede2000(colors[:, None, :], colors[None, :, :]), dtype=np.float64)
    direct_distance = np.float64(ciede2000(first.lab, second.lab))
    assert matrix[0, 1].tobytes() == direct_distance.tobytes()
    config = PaletteConfig()
    direct = evaluate_palette_merge(first, second, (), {}, config)
    reused = evaluate_palette_merge(first, second, (), {}, config, color_distance=float(matrix[0, 1]))
    assert reused == direct


def test_palette_entries_are_observed_source_colors():
    labels, image = _vertical_fixture([(220, 40, 40), (215, 45, 45), (40, 70, 220)])
    bundle, selection, contours, primitives = _pipeline_fixture(labels, image)
    result = consolidate_palette(
        bundle,
        selection,
        contours,
        primitives,
        config=PaletteConfig(mode="fixed", fixed_palette_size=2),
    )
    observed = {tuple(int(v) for v in pixel) for pixel in image.reshape(-1, 3)}
    for entry in result.entries.values():
        assert entry.rgb in observed
        x, y = entry.source_xy
        assert tuple(int(v) for v in bundle.analysis_rgb[y, x]) == entry.rgb


def test_distant_regions_can_share_palette_color():
    labels, image = _vertical_fixture([(210, 45, 45), (35, 70, 215), (210, 45, 45)])
    bundle, selection, contours, primitives = _pipeline_fixture(labels, image)
    result = consolidate_palette(
        bundle,
        selection,
        contours,
        primitives,
        config=PaletteConfig(mode="fixed", fixed_palette_size=2),
    )
    assert result.metrics.palette_count == 2
    assert result.region_to_palette[0] == result.region_to_palette[2]
    assert result.region_to_palette[0] != result.region_to_palette[1]


def test_major_relationship_repairs_fixed_one_color_cut():
    labels, image = _vertical_fixture([(235, 30, 30), (25, 55, 230)], stripe=7)
    bundle, selection, contours, primitives = _pipeline_fixture(labels, image)
    result = consolidate_palette(
        bundle,
        selection,
        contours,
        primitives,
        config=PaletteConfig(mode="fixed", fixed_palette_size=1),
    )
    assert result.metrics.palette_count == 2
    assert result.metrics.repaired_split_count >= 1
    assert result.region_to_palette[0] != result.region_to_palette[1]


def test_distinct_characteristic_anchors_force_palette_overflow():
    labels, image = _vertical_fixture([(120, 120, 120), (122, 122, 122)], stripe=6)
    bundle, selection, contours, primitives = _pipeline_fixture(labels, image)
    anchor_map = np.where(labels == 0, 0, 1).astype(np.int32)
    characteristic = CharacteristicContext(
        anchors=(
            CharacteristicAnchor(0, np.asarray([55.0, 65.0, 40.0], np.float64), 0.95),
            CharacteristicAnchor(1, np.asarray([55.0, -55.0, -45.0], np.float64), 0.95),
        ),
        anchor_map=anchor_map,
    )
    result = consolidate_palette(
        bundle,
        selection,
        contours,
        primitives,
        characteristic=characteristic,
        config=PaletteConfig(mode="fixed", fixed_palette_size=1),
    )
    assert result.metrics.palette_count == 2
    assert result.region_to_palette[0] != result.region_to_palette[1]
    assert any("characteristic_anchor" in item.reasons for item in result.relationships)


def test_palette_consolidation_is_deterministic():
    labels, image = _vertical_fixture(
        [(205, 55, 55), (198, 60, 60), (45, 80, 205), (50, 85, 200)]
    )
    bundle, selection, contours, primitives = _pipeline_fixture(labels, image)
    config = PaletteConfig(mode="fixed", fixed_palette_size=2)
    first = consolidate_palette(bundle, selection, contours, primitives, config=config)
    second = consolidate_palette(bundle, selection, contours, primitives, config=config)
    assert dict(first.region_to_palette) == dict(second.region_to_palette)
    assert tuple(sorted((key, value.rgb) for key, value in first.entries.items())) == tuple(
        sorted((key, value.rgb) for key, value in second.entries.items())
    )
    assert first.metrics == second.metrics

def test_subject_class_conflict_prevents_cross_class_palette_merge():
    labels, image = _vertical_fixture([(120, 120, 120), (121, 121, 121)], stripe=6)
    bundle, selection, contours, primitives = _pipeline_fixture(labels, image)
    bundle = replace(
        bundle,
        subject_prob=np.where(labels == 0, 0.95, 0.05).astype(np.float32),
        subject_confidence=np.ones(labels.shape, dtype=np.float32),
    )
    result = consolidate_palette(
        bundle,
        selection,
        contours,
        primitives,
        config=PaletteConfig(mode="fixed", fixed_palette_size=1),
    )
    assert result.metrics.palette_count == 2
    assert result.region_to_palette[0] != result.region_to_palette[1]


def test_subject_class_conflict_is_inactive_without_guidance():
    labels, image = _vertical_fixture([(120, 120, 120), (121, 121, 121)], stripe=6)
    bundle, selection, contours, primitives = _pipeline_fixture(labels, image)
    result = consolidate_palette(
        bundle,
        selection,
        contours,
        primitives,
        config=PaletteConfig(mode="fixed", fixed_palette_size=1),
    )
    assert result.metrics.palette_count == 1
    assert result.region_to_palette[0] == result.region_to_palette[1]


def test_subject_rescue_protects_strong_subject_with_mid_confidence():
    labels, image = _vertical_fixture([(120, 120, 120), (121, 121, 121)], stripe=6)
    bundle, selection, contours, primitives = _pipeline_fixture(labels, image)
    bundle = replace(
        bundle,
        subject_prob=np.where(labels == 0, 0.95, 0.05).astype(np.float32),
        subject_confidence=np.where(labels == 0, 0.75, 0.95).astype(np.float32),
    )
    result = consolidate_palette(
        bundle,
        selection,
        contours,
        primitives,
        config=PaletteConfig(mode="fixed", fixed_palette_size=1),
    )
    assert result.metrics.palette_count == 2
    assert result.region_to_palette[0] != result.region_to_palette[1]


def test_subject_rescue_requires_near_background_color_collision():
    from minimalize_engine.v2.palette.consolidate import _build_subject_classes

    labels, image = _vertical_fixture([(120, 120, 120), (220, 40, 40)], stripe=6)
    bundle, selection, contours, primitives = _pipeline_fixture(labels, image)
    bundle = replace(
        bundle,
        subject_prob=np.where(labels == 0, 0.95, 0.05).astype(np.float32),
        subject_confidence=np.where(labels == 0, 0.75, 0.95).astype(np.float32),
    )
    samples = sample_region_colors(
        bundle,
        selection,
        contours,
        characteristic=None,
        config=PaletteConfig(),
    )
    classes = _build_subject_classes(bundle, selection, samples, PaletteConfig())
    assert classes == {0: 0, 1: -1}
