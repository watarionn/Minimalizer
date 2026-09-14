from __future__ import annotations

import numpy as np

from minimalize_engine.v2.contour.types import (
    BoundaryChain,
    BoundaryGraph,
    BoundaryVertex,
    ContourSimplificationMetrics,
    ContourSimplificationResult,
    OrientedChainRef,
    RegionContour,
)
from minimalize_engine.v2.preprocessing import build_image_bundle
from minimalize_engine.v2.primitive import PrimitiveFitConfig, fit_region_primitives
from minimalize_engine.v2.primitive.scoring import metric_rejection_reasons
from minimalize_engine.v2.primitive.types import PrimitiveMetrics
from minimalize_engine.v2.region_merge.types import HierarchyCut, RegionSelection


def _rectangle_fixture(width: int = 14, height: int = 10):
    labels = np.zeros((height, width), dtype=np.int32)
    image = np.zeros((height, width, 3), dtype=np.uint8)
    bundle = build_image_bundle(image, analysis_max_side=max(height, width))
    region_ids = frozenset({0})
    cut = HierarchyCut(
        preset="detailed",
        selected_ids=region_ids,
        region_count=1,
        visual_loss=0.0,
        normalized_visual_loss=0.0,
        objective=0.0,
        max_selected_hierarchy_height=0.0,
    )
    selection = RegionSelection(
        preset="detailed",
        cut=cut,
        labels=labels,
        region_ids=region_ids,
    )
    loop = np.asarray(
        [[0.0, 0.0], [float(width), 0.0],
         [float(width), float(height)], [0.0, float(height)]],
        dtype=np.float32,
    )
    vertices = {
        0: BoundaryVertex(0, 0.0, 0.0),
        1: BoundaryVertex(1, 0.0, float(height)),
    }
    chain = BoundaryChain(
        id=0,
        start_vertex=0,
        end_vertex=1,
        points=loop,
        regions=(0,),
        original_point_count=4,
    )
    graph = BoundaryGraph(
        vertices=vertices,
        chains={0: chain},
        region_chains={0: [OrientedChainRef(0, False)]},
    )
    contour = RegionContour(
        region_id=0,
        loops=(loop,),
        area_px=width * height,
        centroid=(width / 2.0, height / 2.0),
    )
    metrics = ContourSimplificationMetrics(
        4, 4, 0, 0, 0, 1.0, 0.0, 0.0, 0.0
    )
    contour_result = ContourSimplificationResult(
        boundary_graph=graph,
        contours={0: contour},
        metrics=metrics,
    )
    return bundle, selection, contour_result


def test_rectangle_converts_to_oriented_rectangle():
    bundle, selection, contours = _rectangle_fixture()
    result = fit_region_primitives(
        bundle, selection, contours, config=PrimitiveFitConfig()
    )
    selected = result.primitives[0].selected
    assert result.metrics.region_count == 1
    assert result.metrics.converted_region_count == 1
    assert selected.geometry.kind == "oriented_rectangle"
    assert selected.metrics.iou >= 0.99
    assert selected.metrics.complexity_gain >= 0.35


def test_polygon_baseline_is_always_eligible_and_exact():
    bundle, selection, contours = _rectangle_fixture()
    result = fit_region_primitives(
        bundle, selection, contours, config=PrimitiveFitConfig()
    )
    candidates = result.primitives[0].candidates
    polygon = next(item for item in candidates if item.geometry.kind == "polygon")
    assert polygon.eligible is True
    assert polygon.rejection_reasons == ()
    assert polygon.metrics.iou == 1.0
    assert polygon.metrics.complexity_gain == 0.0

def test_guarded_overlap_is_rejected():
    metrics = PrimitiveMetrics(
        0.99, 0.0, 0.02, 0.02, 0.02, 0.0,
        0.0, 0.0, 0.0, 0.0, 1.0, 0.50,
    )
    reasons = metric_rejection_reasons(
        metrics,
        kind="oriented_rectangle",
        config=PrimitiveFitConfig(),
    )
    assert "guarded_neighbor_overlap" in reasons

def test_low_gain_uses_polygon_fallback():
    metrics = PrimitiveMetrics(
        1.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 1.0, 0.20,
    )
    reasons = metric_rejection_reasons(
        metrics, kind="ellipse", config=PrimitiveFitConfig()
    )
    assert "complexity_gain" in reasons


def test_primitive_fitting_is_deterministic():
    bundle, selection, contours = _rectangle_fixture()
    first = fit_region_primitives(
        bundle, selection, contours, config=PrimitiveFitConfig()
    )
    second = fit_region_primitives(
        bundle, selection, contours, config=PrimitiveFitConfig()
    )
    left = first.primitives[0].selected
    right = second.primitives[0].selected
    assert left.geometry.kind == right.geometry.kind
    assert left.objective == right.objective

def test_face_semantic_hint_disables_rectangle_and_favors_ellipse():
    config = PrimitiveFitConfig()
    loop = np.asarray([[0, 0], [4, 0], [4, 4], [0, 4]], dtype=np.float32)
    contour = RegionContour(
        region_id=0, loops=(loop,), area_px=16, centroid=(2.0, 2.0),
        semantic_tag="face", semantic_confidence=0.95,
    )
    from minimalize_engine.v2.primitive.candidates import semantic_adjustment
    disabled, _ = semantic_adjustment(contour, "oriented_rectangle", config)
    assert disabled is True
    disabled, ellipse_adjustment = semantic_adjustment(contour, "ellipse", config)
    assert disabled is False
    assert ellipse_adjustment < 0.0

def test_subject_background_boundary_becomes_guarded_neighbor():
    from minimalize_engine.v2.primitive.fit import _subject_guarded_neighbors
    config = PrimitiveFitConfig()
    subject_stats = {0: (0.95, 0.95), 1: (0.05, 0.95), 2: (0.80, 0.95)}
    guarded = _subject_guarded_neighbors(
        0, frozenset({1, 2}), subject_stats, config
    )
    assert guarded == frozenset({1})

def test_primitive_config_is_json_serializable():
    import json
    from dataclasses import asdict
    payload = json.dumps(asdict(PrimitiveFitConfig()), sort_keys=True)
    assert 'critical_neighbor_leakage_limit' in payload