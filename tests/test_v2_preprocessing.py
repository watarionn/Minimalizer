import numpy as np
import pytest

from minimalize_engine.v2.preprocessing import (
    ShadingFlattenConfig,
    build_image_bundle,
    compute_shading_flatten_sp,
    flatten_shading_rgb,
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


def test_shading_flatten_auto_sp_scales_with_short_side():
    assert compute_shading_flatten_sp(340, 340) == 5
    assert compute_shading_flatten_sp(2000, 2000) == 30
    assert compute_shading_flatten_sp(10000, 4000) == 60


def test_shading_flatten_reduces_gradient_variation_but_keeps_major_color_split():
    image = np.zeros((80, 120, 3), dtype=np.uint8)
    x = np.linspace(-18, 18, 60, dtype=np.float32)
    left = np.clip(90 + x, 0, 255).astype(np.uint8)
    right = np.clip(190 + x, 0, 255).astype(np.uint8)
    image[:, :60] = left[None, :, None]
    image[:, 60:] = right[None, :, None]

    flattened = flatten_shading_rgb(
        image,
        config=ShadingFlattenConfig(enabled=True, sr=55),
    )

    assert float(flattened[:, :58, 0].std()) < float(image[:, :58, 0].std())
    assert float(flattened[:, 70:118, 0].std()) < float(image[:, 70:118, 0].std())
    left_mean = float(flattened[:, :55, 0].mean())
    right_mean = float(flattened[:, 65:, 0].mean())
    assert right_mean - left_mean > 70.0


def test_shading_flatten_uses_alpha_to_avoid_transparent_white_bleed():
    image = np.full((48, 48, 3), 255, dtype=np.uint8)
    alpha = np.zeros((48, 48), dtype=np.float32)
    alpha[8:40, 8:40] = 1.0
    image[8:40, 8:40] = (80, 110, 140)
    image[16:32, 16:32] = (95, 125, 155)

    flattened = flatten_shading_rgb(
        image,
        alpha=alpha,
        config=ShadingFlattenConfig(enabled=True, sr=55),
    )

    boundary = flattened[9:39, 9:39].reshape(-1, 3)
    assert float(boundary.mean()) < 180.0
    assert np.array_equal(flattened[alpha == 0.0], image[alpha == 0.0])


def test_bundle_shading_flatten_changes_analysis_plane_but_not_source_rgb():
    image = np.zeros((48, 64, 3), dtype=np.uint8)
    ramp = np.linspace(60, 120, 32, dtype=np.uint8)
    image[:, :32] = ramp[None, :, None]
    image[:, 32:] = (210, 70, 70)

    plain = build_image_bundle(image, analysis_max_side=64)
    flattened = build_image_bundle(
        image,
        analysis_max_side=64,
        shading_flatten=ShadingFlattenConfig(enabled=True, sr=55),
    )

    assert np.array_equal(flattened.source_rgb, image)
    assert not np.array_equal(flattened.analysis_rgb, plain.analysis_rgb)


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
