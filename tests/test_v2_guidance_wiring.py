import numpy as np
import pytest

import minimalize_engine.v2.pipeline as pipeline_module
from minimalize_engine.v2.analysis_guidance import (
    AnalysisGuidance,
    LineGuide,
    StructuralGuide,
    line_support_from_guide,
    structural_regions_from_guide,
)
from minimalize_engine.v2.pipeline import PipelineConfig, minimalize_v2
from minimalize_engine.v2.preprocessing import build_image_bundle
from minimalize_engine.v2.region_merge.graph import (
    build_region_graph_from_arrays,
    merge_region_edges,
)
from minimalize_engine.v2.region_merge.types import RegionEdge
from minimalize_engine.v2.regression import algorithm_digest


def _image(size: int = 32) -> np.ndarray:
    image = np.zeros((size, size, 3), dtype=np.uint8)
    image[:, : size // 2] = (220, 60, 70)
    image[:, size // 2 :] = (50, 80, 210)
    return image


def test_structural_regions_are_aggregated_at_analysis_resolution():
    image = _image(8)
    bundle = build_image_bundle(image, analysis_max_side=4)
    labels = np.zeros((4, 4), dtype=np.int32)
    labels[:, 2:] = 1
    maps = np.zeros((2, 8, 8), dtype=np.float32)
    maps[0, :, :4] = 0.9
    maps[1, :, 4:] = 0.8
    guide = StructuralGuide(
        ("torso", "left_upper_arm"),
        maps,
        "rtmlib",
        "wholebody-balanced",
    )

    regions = structural_regions_from_guide(bundle, labels, guide)

    assert regions is not None
    assert regions[0][0] == "torso"
    assert regions[0][1] == pytest.approx(0.9)
    assert regions[1][0] == "left_upper_arm"
    assert regions[1][1] == pytest.approx(0.8)


def test_line_support_is_resized_to_analysis_resolution():
    image = _image(8)
    bundle = build_image_bundle(image, analysis_max_side=4)
    support = np.zeros((8, 8), dtype=np.float32)
    support[:, 3:5] = 1.0
    guide = LineGuide(support, "deeplsd", "deeplsd_md", 0.13)

    resized = line_support_from_guide(bundle, guide)

    assert resized is not None
    assert resized.dtype == np.float32
    assert resized.shape == (4, 4)
    assert float(resized.max()) > 0.0
    assert 0.0 <= float(resized.min()) <= float(resized.max()) <= 1.0


def test_rag_edge_keeps_line_support_without_changing_gradient_histograms():
    labels = np.zeros((4, 4), dtype=np.int32)
    labels[:, 2:] = 1
    lab = np.zeros((4, 4, 3), dtype=np.float32)
    raw = np.zeros((4, 4), dtype=np.float32)
    structural = np.zeros((4, 4), dtype=np.float32)
    line = np.zeros((4, 4), dtype=np.float32)
    line[:, 1:3] = 1.0

    graph = build_region_graph_from_arrays(
        labels,
        lab,
        raw,
        structural,
        line_support=line,
        gradient_bins=8,
    )

    edge = graph.edges[(0, 1)]
    assert edge.line_support_mean == pytest.approx(1.0)
    assert int(edge.raw_gradient_hist[-1]) == 0
    assert int(edge.structural_gradient_hist[-1]) == 0


def test_merged_rag_edge_preserves_boundary_weighted_line_support():
    hist = np.asarray([2, 0, 0, 0], dtype=np.int64)
    left = RegionEdge(
        0,
        2,
        2.0,
        hist,
        hist,
        line_support_mean=0.25,
    )
    right_hist = np.asarray([6, 0, 0, 0], dtype=np.int64)
    right = RegionEdge(
        1,
        2,
        6.0,
        right_hist,
        right_hist,
        line_support_mean=0.75,
    )

    merged = merge_region_edges(
        (left, right),
        new_region_id=3,
        neighbor_id=2,
    )

    assert merged.shared_boundary_px == pytest.approx(8.0)
    assert merged.line_support_mean == pytest.approx(0.625)


def test_pipeline_routes_structural_and_line_guidance_before_merge(monkeypatch):
    image = _image(32)
    structural_maps = np.full((1, 32, 32), 0.75, dtype=np.float32)
    line_map = np.zeros((32, 32), dtype=np.float32)
    line_map[:, 15:17] = 1.0
    guidance = AnalysisGuidance(
        structural=StructuralGuide(
            ("torso",),
            structural_maps,
            "rtmlib",
            "wholebody-balanced",
        ),
        line=LineGuide(
            line_map,
            "deeplsd",
            "deeplsd_md",
            0.13,
        ),
    )

    captured = {}
    real_build = pipeline_module.build_region_graph

    def capture_graph(bundle, labels, **kwargs):
        captured["line_support"] = kwargs.get("line_support")
        captured["annotations"] = kwargs.get("annotations")
        return real_build(bundle, labels, **kwargs)

    monkeypatch.setattr(pipeline_module, "build_region_graph", capture_graph)
    result = minimalize_v2(
        image,
        config=PipelineConfig(analysis_max_side=16),
        guidance=guidance,
    )

    assert captured["line_support"] is not None
    assert captured["line_support"].shape == (16, 16)
    assert float(captured["line_support"].max()) > 0.0
    annotations = captured["annotations"]
    assert annotations
    assert all(item.structure_tag == "torso" for item in annotations.values())
    leaf_stats = [
        result.region_merge.tree.nodes[region_id].stats
        for region_id in result.region_merge.tree.leaf_ids
    ]
    assert all(stats.structure_tag == "torso" for stats in leaf_stats)
    assert all(stats.structure_confidence == pytest.approx(0.75) for stats in leaf_stats)


def test_wiring_only_guidance_does_not_change_algorithm_digest():
    image = _image(32)
    config = PipelineConfig(analysis_max_side=32)
    structural_maps = np.full((1, 32, 32), 0.8, dtype=np.float32)
    line_map = np.zeros((32, 32), dtype=np.float32)
    line_map[:, 15:17] = 1.0
    guidance = AnalysisGuidance(
        structural=StructuralGuide(
            ("torso",),
            structural_maps,
            "rtmlib",
            "wholebody-balanced",
        ),
        line=LineGuide(
            line_map,
            "deeplsd",
            "deeplsd_md",
            0.13,
        ),
    )

    baseline = minimalize_v2(image, config=config)
    wired = minimalize_v2(image, config=config, guidance=guidance)

    assert algorithm_digest(baseline, "minimal") == algorithm_digest(wired, "minimal")


def test_pose_aware_line_gate_softly_attenuates_unsupported_lines():
    from minimalize_engine.v2.analysis_guidance import LineGuide, apply_pose_aware_line_gate

    line = np.ones((8, 8), dtype=np.float32)
    pose = np.zeros((1, 8, 8), dtype=np.float32)
    pose[0, :, 3:5] = 1.0
    gated = apply_pose_aware_line_gate(
        LineGuide(line, "deeplsd", "deeplsd_md", 0.13),
        StructuralGuide(("torso",), pose, "rtmlib", "wholebody-balanced"),
        floor=0.20,
    )
    assert float(gated.support_map[4, 4]) == pytest.approx(1.0)
    assert float(gated.support_map[4, 0]) == pytest.approx(0.20)
    assert gated.model.endswith("+pose-gate-v2")


def test_pose_aware_line_gate_default_floor_is_fixed_at_point20():
    from minimalize_engine.v2.analysis_guidance import LineGuide, apply_pose_aware_line_gate

    line = np.ones((8, 8), dtype=np.float32)
    pose = np.zeros((1, 8, 8), dtype=np.float32)
    pose[0, :, 3:5] = 1.0
    gated = apply_pose_aware_line_gate(
        LineGuide(line, "deeplsd", "deeplsd_md", 0.13),
        StructuralGuide(("torso",), pose, "rtmlib", "wholebody-balanced"),
    )

    assert float(gated.support_map[4, 4]) == pytest.approx(1.0)
    assert float(gated.support_map[4, 0]) == pytest.approx(0.20)


def test_pose_aware_line_gate_preserves_line_without_structural_guide():
    from minimalize_engine.v2.analysis_guidance import LineGuide, apply_pose_aware_line_gate

    guide = LineGuide(np.ones((4, 4), dtype=np.float32), "deeplsd", "deeplsd_md", 0.13)
    assert apply_pose_aware_line_gate(guide, None) is guide
