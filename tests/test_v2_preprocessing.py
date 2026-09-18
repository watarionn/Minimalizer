import numpy as np
import pytest

from minimalize_engine.v2.preprocessing import (
    build_image_bundle,
    l0_gradient_smooth,
    lab_edge_map,
    resize_for_analysis,
    rgb_to_canonical_lab,
)


def test_analysis_resize_never_enlarges_and_tracks_source_scale():
    small = np.zeros((20, 30, 3), dtype=np.uint8)
    same, sx, sy = resize_for_analysis(small, max_side=64)
    assert same.shape == small.shape
    assert (sx, sy) == (1.0, 1.0)

    large = np.zeros((100, 200, 3), dtype=np.uint8)
    resized, sx, sy = resize_for_analysis(large, max_side=80)
    assert resized.shape == (40, 80, 3)
    assert sx == pytest.approx(2.5)
    assert sy == pytest.approx(2.5)


def test_canonical_lab_is_float_cielab_not_opencv_uint8_encoding():
    rgb = np.array([[[255, 255, 255], [0, 0, 0], [255, 0, 0]]], dtype=np.uint8)
    lab = rgb_to_canonical_lab(rgb)
    assert lab.dtype == np.float32
    assert lab[0, 0, 0] == pytest.approx(100.0, abs=0.1)
    assert lab[0, 1, 0] == pytest.approx(0.0, abs=0.1)
    assert -128.0 <= float(lab[..., 1].min()) <= 127.0
    assert -128.0 <= float(lab[..., 1].max()) <= 127.0
    assert -128.0 <= float(lab[..., 2].min()) <= 127.0
    assert -128.0 <= float(lab[..., 2].max()) <= 127.0


def test_l0_smoothing_suppresses_microtexture_without_erasing_major_split():
    image = np.zeros((48, 64, 3), dtype=np.uint8)
    image[:, :32] = (80, 80, 80)
    image[:, 32:] = (190, 190, 190)
    checker = ((np.indices((48, 64)).sum(axis=0) % 2) * 18 - 9).astype(np.int16)
    textured = np.clip(image.astype(np.int16) + checker[:, :, None], 0, 255).astype(np.uint8)
    smoothed = l0_gradient_smooth(textured)
    before_left = float(textured[:, :30, 0].std())
    after_left = float(smoothed[:, :30, 0].std())
    left_mean = float(smoothed[:, :30, 0].mean())
    right_mean = float(smoothed[:, 34:, 0].mean())
    assert after_left < before_left
    assert right_mean - left_mean > 70.0


def test_lab_edge_map_is_normalized_and_bundle_keeps_raw_and_structural_paths():
    image = np.zeros((48, 64, 3), dtype=np.uint8)
    image[:, :32] = (220, 40, 40)
    image[:, 32:] = (30, 50, 220)
    lab = rgb_to_canonical_lab(image)
    edge = lab_edge_map(lab)
    assert edge.dtype == np.float32
    assert float(edge.min()) >= 0.0
    assert float(edge.max()) <= 1.0
    bundle = build_image_bundle(image, analysis_max_side=32)
    assert bundle.analysis_rgb.shape == (24, 32, 3)
    assert bundle.structural_rgb.shape == bundle.analysis_rgb.shape
    assert bundle.analysis_lab.shape == (24, 32, 3)
    assert bundle.structural_lab.shape == (24, 32, 3)
    assert bundle.edge_raw.shape == (24, 32)
    assert bundle.edge_structural.shape == (24, 32)
    assert bundle.scale_x == pytest.approx(2.0)
    assert bundle.scale_y == pytest.approx(2.0)


def test_optional_maps_follow_analysis_resize():
    image = np.zeros((40, 80, 3), dtype=np.uint8)
    probability = np.linspace(0.0, 1.0, 40 * 80, dtype=np.float32).reshape(40, 80)
    bundle = build_image_bundle(
        image,
        subject_prob=probability,
        subject_confidence=np.ones((40, 80), dtype=np.float32),
        alpha=np.ones((40, 80), dtype=np.float32),
        analysis_max_side=40,
    )
    assert bundle.subject_prob.shape == (20, 40)
    assert bundle.subject_confidence.shape == (20, 40)
    assert bundle.alpha.shape == (20, 40)
    assert 0.0 <= float(bundle.subject_prob.min()) <= float(bundle.subject_prob.max()) <= 1.0
