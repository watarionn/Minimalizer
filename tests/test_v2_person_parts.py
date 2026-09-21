import numpy as np
import pytest

from minimalize_engine.v2.analysis_guidance import AnalysisGuidance, StructuralGuide
from minimalize_engine.v2.person_parts import (
    PERSON_PART_NAMES,
    PersonPartConfig,
    build_person_part_partition,
)


def _guidance() -> AnalysisGuidance:
    h, w = 20, 16
    subject = np.zeros((h, w), dtype=np.float32)
    subject[2:19, 3:13] = 0.95
    labels = (
        "torso",
        "left_upper_arm",
        "left_forearm",
        "right_upper_arm",
        "right_forearm",
        "left_thigh",
        "left_shin",
        "right_thigh",
        "right_shin",
    )
    maps = np.zeros((len(labels), h, w), dtype=np.float32)
    maps[0, 7:14, 6:10] = 0.9
    maps[1, 8:11, 3:7] = 0.8
    maps[2, 10:14, 3:6] = 0.8
    maps[3, 8:11, 9:13] = 0.8
    maps[4, 10:14, 10:13] = 0.8
    maps[5, 13:17, 6:8] = 0.8
    maps[6, 16:19, 5:8] = 0.8
    maps[7, 13:17, 8:10] = 0.8
    maps[8, 16:19, 9:12] = 0.8
    structural = StructuralGuide(labels=labels, confidence_maps=maps, provider="test", model="pose")
    return AnalysisGuidance(
        subject_prob=subject,
        subject_confidence=np.ones_like(subject),
        structural=structural,
        subject_provider="test",
        subject_model="mask",
    )


def test_partition_separates_background_and_six_coarse_parts():
    partition = build_person_part_partition(_guidance())
    assert set(partition.part_masks) == set(PERSON_PART_NAMES)
    assert np.array_equal(partition.background_mask, ~partition.subject_mask)
    assert partition.part_masks["head"].any()
    for name in PERSON_PART_NAMES[1:]:
        assert partition.part_masks[name].any()
        assert not np.any(partition.part_masks[name] & partition.background_mask)


def test_partition_without_pose_uses_silhouette_body_fallback():
    guidance = _guidance()
    guidance = AnalysisGuidance(
        subject_prob=guidance.subject_prob,
        subject_confidence=guidance.subject_confidence,
        subject_provider="test",
        subject_model="mask",
    )
    partition = build_person_part_partition(guidance)
    assert partition.part_masks["head"].any()
    assert partition.part_masks["torso"].any()
    assert partition.part_masks["left_leg"].any()
    assert partition.part_masks["right_leg"].any()


def test_partition_requires_subject_guidance():
    with pytest.raises(ValueError, match="subject_prob"):
        build_person_part_partition(AnalysisGuidance())


def test_partition_config_rejects_invalid_thresholds():
    with pytest.raises(ValueError):
        PersonPartConfig(subject_threshold=0.0)


def test_pipeline_exposes_partition_only_when_layered_mode_is_enabled():
    from minimalize_engine.v2.pipeline import LayeredPersonConfig, PipelineConfig, minimalize_v2

    guidance = _guidance()
    image = np.full((20, 16, 3), 240, dtype=np.uint8)
    image[2:19, 3:13] = (120, 80, 60)
    result = minimalize_v2(
        image,
        config=PipelineConfig(
            analysis_max_side=20,
            layered_person=LayeredPersonConfig(enabled=True),
        ),
        guidance=guidance,
    )
    assert result.person_parts is not None
    assert result.person_parts.part_masks["torso"].any()

    baseline = minimalize_v2(
        image,
        config=PipelineConfig(analysis_max_side=20),
        guidance=guidance,
    )
    assert baseline.person_parts is None


def test_resize_partition_projects_masks_to_analysis_resolution():
    from minimalize_engine.v2.person_parts import resize_person_part_partition

    partition = build_person_part_partition(_guidance())
    resized = resize_person_part_partition(partition, (10, 8))
    assert resized.subject_mask.shape == (10, 8)
    assert resized.background_mask.shape == (10, 8)
    assert all(mask.shape == (10, 8) for mask in resized.part_masks.values())
    assert not np.any(resized.subject_mask & resized.background_mask)
    occupied = np.zeros((10, 8), dtype=np.uint8)
    for mask in resized.part_masks.values():
        assert not np.any((occupied > 0) & mask)
        occupied[mask] += 1


def test_sparse_pose_support_falls_back_to_complete_silhouette_partition():
    guidance = _guidance()
    maps = np.zeros_like(guidance.structural.confidence_maps)
    # A detector may return one convincing limb while the rest of the pose is unusable.
    maps[1, 8:12, 3:7] = 0.9
    sparse = AnalysisGuidance(
        subject_prob=guidance.subject_prob,
        subject_confidence=guidance.subject_confidence,
        structural=StructuralGuide(
            labels=guidance.structural.labels,
            confidence_maps=maps,
            provider="test",
            model="sparse-pose",
        ),
        subject_provider="test",
        subject_model="mask",
    )
    partition = build_person_part_partition(
        sparse,
        config=PersonPartConfig(structural_min_part_pixels=4),
    )
    for name in PERSON_PART_NAMES:
        assert partition.part_masks[name].any()


def test_partition_config_rejects_invalid_structural_coverage():
    with pytest.raises(ValueError):
        PersonPartConfig(structural_min_coverage_ratio=0.0)


def test_person_part_primitive_config_is_deliberately_coarser_for_limbs():
    from minimalize_engine.v2.pipeline import _person_part_primitive_config
    from minimalize_engine.v2.primitive import PrimitiveFitConfig

    base = PrimitiveFitConfig()
    limb = _person_part_primitive_config("left_arm", base)
    head = _person_part_primitive_config("head", base)
    assert limb.min_iou < base.min_iou
    assert limb.max_overcoverage > base.max_overcoverage
    assert limb.complexity_reward > base.complexity_reward
    assert limb.rectangle_complexity < limb.ellipse_complexity
    assert limb.trapezoid_complexity < limb.capsule_complexity
    assert head.ellipse_complexity > base.ellipse_complexity
    assert head.min_iou > limb.min_iou


def test_layered_person_can_disable_coarse_part_primitive_policy():
    from minimalize_engine.v2.pipeline import LayeredPersonConfig

    assert LayeredPersonConfig().coarse_part_primitives is True
    assert LayeredPersonConfig(coarse_part_primitives=False).coarse_part_primitives is False


def test_person_part_minimal_cut_budgets_are_bold():
    from minimalize_engine.v2.pipeline import _person_part_cut_policies

    expected_max = {
        "head": 6,
        "torso": 5,
        "left_arm": 3,
        "right_arm": 3,
        "left_leg": 3,
        "right_leg": 3,
    }
    for name, ceiling in expected_max.items():
        assert _person_part_cut_policies(name)["minimal"].target_max == ceiling


def test_structural_partition_expands_pose_corridors_across_subject():
    partition = build_person_part_partition(_guidance(), config=PersonPartConfig(structural_min_part_pixels=4))
    covered = np.zeros_like(partition.subject_mask)
    for mask in partition.part_masks.values():
        covered |= mask
    assert np.array_equal(covered, partition.subject_mask)


def test_semantic_part_shape_limits_match_approved_coarse_budget():
    from minimalize_engine.v2.pipeline import _semantic_part_shape_limit

    assert _semantic_part_shape_limit("head", "minimal") == 5
    assert _semantic_part_shape_limit("torso", "minimal") == 4
    for name in ("left_arm", "right_arm", "left_leg", "right_leg"):
        assert _semantic_part_shape_limit(name, "minimal") == 3


def test_person_part_contours_are_more_aggressively_simplified():
    from minimalize_engine.v2.contour import ContourSimplificationConfig
    from minimalize_engine.v2.pipeline import _person_part_contour_config

    base = ContourSimplificationConfig()
    coarse = _person_part_contour_config(base)
    assert coarse.minimal_epsilon_ratio > base.minimal_epsilon_ratio
    assert coarse.ultra_minimal_epsilon_ratio > coarse.minimal_epsilon_ratio
    assert coarse.min_iou < base.min_iou
    assert coarse.max_area_change > base.max_area_change
