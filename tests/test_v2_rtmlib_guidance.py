import numpy as np
import pytest

from minimalize_engine.v2 import AnalysisGuidance, LineGuide
from minimalize_engine.v2.rtmlib_guidance import (
    RTMLIB_STRUCTURAL_LABELS,
    RtmlibStructuralConfig,
    attach_rtmlib_structure,
    build_rtmlib_structural_guide,
    build_structural_guide_from_pose,
    select_primary_skeleton,
)


def _body17(offset_x: float = 0.0, offset_y: float = 0.0) -> np.ndarray:
    points = np.array(
        [
            (30, 8), (27, 7), (33, 7), (24, 9), (36, 9),
            (20, 20), (40, 20), (18, 35), (42, 35),
            (16, 50), (44, 50), (24, 45), (36, 45),
            (24, 65), (36, 65), (24, 85), (36, 85),
        ],
        dtype=np.float32,
    )
    points[:, 0] += offset_x
    points[:, 1] += offset_y
    return points


def _scores(value: float = 0.9) -> np.ndarray:
    return np.full(17, value, dtype=np.float32)


def test_primary_selection_suppresses_near_duplicate_and_keeps_stronger_pose():
    keypoints = np.stack((_body17(), _body17(1.0, 1.0)))
    scores = np.stack((_scores(0.75), _scores(0.95)))

    selection = select_primary_skeleton(
        keypoints,
        scores,
        source_shape=(100, 100),
    )

    assert selection is not None
    assert selection.person_index == 1
    assert selection.duplicate_indices == (0,)


def test_primary_selection_uses_subject_support_for_distinct_people():
    keypoints = np.stack((_body17(), _body17(45.0, 0.0)))
    scores = np.stack((_scores(0.95), _scores(0.80)))
    subject = np.zeros((100, 100), dtype=np.float32)
    subject[:, 55:] = 1.0

    selection = select_primary_skeleton(
        keypoints,
        scores,
        source_shape=(100, 100),
        subject_prob=subject,
    )

    assert selection is not None
    assert selection.person_index == 1
    assert selection.duplicate_indices == ()


def test_visibility_gate_does_not_invent_missing_lower_leg():
    keypoints = _body17()[None, ...]
    scores = _scores()[None, ...]
    scores[0, 15] = 0.20

    guide, selection = build_structural_guide_from_pose(
        keypoints,
        scores,
        source_shape=(100, 100),
    )

    assert selection is not None
    left_thigh = guide.confidence_maps[RTMLIB_STRUCTURAL_LABELS.index("left_thigh")]
    left_shin = guide.confidence_maps[RTMLIB_STRUCTURAL_LABELS.index("left_shin")]
    assert float(left_thigh.max()) > 0.0
    assert float(left_shin.max()) == pytest.approx(0.0)


def test_corridor_support_is_soft_bounded_and_subject_gated():
    keypoints = _body17()[None, ...]
    scores = _scores(0.8)[None, ...]
    subject = np.zeros((100, 100), dtype=np.float32)
    subject[10:91, 10:51] = 1.0

    guide, _ = build_structural_guide_from_pose(
        keypoints,
        scores,
        source_shape=(100, 100),
        subject_prob=subject,
    )

    arm = guide.confidence_maps[RTMLIB_STRUCTURAL_LABELS.index("left_upper_arm")]
    assert arm.dtype == np.float32
    assert float(arm.max()) <= 0.800001
    assert float(arm[28, 19]) > float(arm[28, 45])
    assert float(arm[:, 55:].max()) == pytest.approx(0.0)


def test_empty_pose_result_produces_zero_structural_evidence():
    guide, selection = build_structural_guide_from_pose(
        np.zeros((0, 17, 2), dtype=np.float32),
        np.zeros((0, 17), dtype=np.float32),
        source_shape=(32, 32),
    )

    assert selection is None
    assert guide.source_shape == (32, 32)
    assert float(guide.confidence_maps.max()) == pytest.approx(0.0)


class _FakeWholebody:
    def __init__(self, keypoints: np.ndarray, scores: np.ndarray):
        self.keypoints = keypoints
        self.scores = scores
        self.seen = None

    def __call__(self, image: np.ndarray):
        self.seen = image.copy()
        return self.keypoints, self.scores


def test_build_adapter_converts_rgb_to_bgr_and_accepts_fake_runtime():
    source = np.zeros((100, 100, 3), dtype=np.uint8)
    source[0, 0] = (255, 0, 0)
    fake = _FakeWholebody(_body17()[None, ...], _scores()[None, ...])

    guide, selection = build_rtmlib_structural_guide(source, model=fake)

    assert selection is not None
    assert fake.seen is not None
    assert tuple(int(value) for value in fake.seen[0, 0]) == (0, 0, 255)
    assert guide.labels == RTMLIB_STRUCTURAL_LABELS


def test_attach_preserves_other_analysis_lanes():
    source = np.zeros((100, 100, 3), dtype=np.uint8)
    subject = np.ones((100, 100), dtype=np.float32)
    line = LineGuide(
        np.zeros((100, 100), dtype=np.float32),
        "deeplsd",
        "deeplsd_md",
        0.13,
    )
    base = AnalysisGuidance(
        subject_prob=subject,
        line=line,
        subject_provider="rembg",
        subject_model="isnet-anime",
    )
    fake = _FakeWholebody(_body17()[None, ...], _scores()[None, ...])

    combined, selection = attach_rtmlib_structure(
        source,
        base_guidance=base,
        model=fake,
    )

    assert selection is not None
    assert combined.subject_prob is subject
    assert combined.line is line
    assert combined.structural is not None
    assert combined.structural.provider == "rtmlib"
    assert combined.subject_provider == "rembg"


def test_config_rejects_invalid_duplicate_and_corridor_parameters():
    with pytest.raises(ValueError):
        RtmlibStructuralConfig(duplicate_distance_ratio=0.0)
    with pytest.raises(ValueError):
        RtmlibStructuralConfig(duplicate_min_common_joints=1)
    with pytest.raises(ValueError):
        RtmlibStructuralConfig(min_corridor_radius_px=5.0, max_corridor_radius_px=4.0)
