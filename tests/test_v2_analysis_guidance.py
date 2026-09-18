import numpy as np
import pytest

from minimalize_engine.v2.analysis_guidance import (
    AnalysisGuidance,
    SemanticGuide,
    semantic_regions_from_guide,
)
from minimalize_engine.v2.pipeline import PipelineConfig, minimalize_v2
from minimalize_engine.v2.preprocessing import build_image_bundle
from minimalize_engine.v2.regression import algorithm_digest


def _image(size: int = 32) -> np.ndarray:
    image = np.zeros((size, size, 3), dtype=np.uint8)
    image[:, : size // 2] = (235, 230, 225)
    image[:, size // 2 :] = (45, 55, 70)
    return image


def test_semantic_guide_requires_well_formed_confidence_maps():
    maps = np.ones((2, 4, 4), dtype=np.float32)
    guide = SemanticGuide(("background", "hair"), maps, "test", "synthetic")
    assert guide.source_shape == (4, 4)

    with pytest.raises(ValueError):
        SemanticGuide(("hair", "hair"), maps, "test", "synthetic")
    with pytest.raises(ValueError):
        SemanticGuide(("background",), maps, "test", "synthetic")


def test_semantic_guide_aggregates_confidence_over_initial_regions():
    image = _image(4)
    bundle = build_image_bundle(image, analysis_max_side=4)
    labels = np.zeros((4, 4), dtype=np.int32)
    labels[:, 2:] = 1
    confidence = np.zeros((2, 4, 4), dtype=np.float32)
    confidence[0, :, :2] = 0.98
    confidence[0, :, 2:] = 0.02
    confidence[1, :, :2] = 0.03
    confidence[1, :, 2:] = 0.96
    guide = SemanticGuide(
        ("background", "hair"), confidence, "mediapipe", "synthetic-multiclass"
    )

    semantic = semantic_regions_from_guide(bundle, labels, guide)

    assert semantic is not None
    assert semantic[0][0] == "background"
    assert semantic[0][1] == pytest.approx(0.98)
    assert semantic[1][0] == "hair"
    assert semantic[1][1] == pytest.approx(0.96)


def test_analysis_guidance_rejects_source_resolution_mismatch():
    probability = np.ones((8, 8), dtype=np.float32)
    guidance = AnalysisGuidance(
        subject_prob=probability,
        subject_provider="rembg",
        subject_model="isnet-anime",
    )
    with pytest.raises(ValueError):
        minimalize_v2(_image(16), guidance=guidance)


def test_subject_guidance_flows_into_v2_bundle_and_region_tree():
    image = _image(32)
    probability = np.zeros((32, 32), dtype=np.float32)
    probability[:, 16:] = 1.0
    confidence = np.full((32, 32), 0.99, dtype=np.float32)
    guidance = AnalysisGuidance(
        subject_prob=probability,
        subject_confidence=confidence,
        subject_provider="rembg",
        subject_model="isnet-anime",
    )

    result = minimalize_v2(
        image,
        config=PipelineConfig(analysis_max_side=32),
        guidance=guidance,
    )

    assert result.bundle.subject_prob is not None
    assert result.bundle.subject_confidence is not None
    assert float(result.bundle.subject_prob[:, :12].max()) == pytest.approx(0.0)
    assert float(result.bundle.subject_prob[:, 20:].min()) == pytest.approx(1.0)
    leaf_stats = [result.region_merge.tree.nodes[rid].stats for rid in result.region_merge.tree.leaf_ids]
    assert any(stats.subject_ratio <= 0.05 for stats in leaf_stats)
    assert any(stats.subject_ratio >= 0.95 for stats in leaf_stats)


def test_semantic_guidance_flows_into_initial_merge_tree_leaves():
    image = _image(32)
    maps = np.zeros((2, 32, 32), dtype=np.float32)
    maps[0, :, :16] = 0.99
    maps[0, :, 16:] = 0.01
    maps[1, :, :16] = 0.02
    maps[1, :, 16:] = 0.98
    guidance = AnalysisGuidance(
        semantic=SemanticGuide(
            ("background", "hair"), maps, "mediapipe", "synthetic-multiclass"
        )
    )

    result = minimalize_v2(
        image,
        config=PipelineConfig(analysis_max_side=32),
        guidance=guidance,
    )

    leaf_stats = [result.region_merge.tree.nodes[rid].stats for rid in result.region_merge.tree.leaf_ids]
    tags = {stats.semantic_tag for stats in leaf_stats if stats.semantic_confidence >= 0.90}
    assert "background" in tags
    assert "hair" in tags


def test_empty_guidance_is_observationally_identical_to_no_guidance():
    image = _image(32)
    baseline = minimalize_v2(image, presets=("minimal",))
    guided = minimalize_v2(image, presets=("minimal",), guidance=AnalysisGuidance())

    assert algorithm_digest(baseline, "minimal") == algorithm_digest(guided, "minimal")
