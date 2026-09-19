import sys

import numpy as np
import pytest

from minimalize_engine.v2 import AnalysisGuidance, StructuralGuide
from minimalize_engine.v2.deeplsd_guidance import (
    DeepLsdLineConfig,
    attach_deeplsd_lines,
    build_deeplsd_line_guide,
    build_line_guide_from_segments,
    create_deeplsd_runtime,
)


def _segments() -> np.ndarray:
    return np.asarray(
        [
            [[10.0, 10.0], [90.0, 10.0]],
            [[-100.0, 20.0], [10.0, 20.0]],
            [[20.0, 30.0], [30.0, 30.0]],
            [[-10.0, 40.0], [90.0, 40.0]],
        ],
        dtype=np.float64,
    )


def test_clip_then_length_gate_rejects_short_outside_segment():
    guide, summary = build_line_guide_from_segments(
        _segments(),
        source_shape=(100, 100),
    )

    assert guide.source_shape == (100, 100)
    assert guide.min_length_diagonal_ratio == pytest.approx(0.13)
    assert summary.raw_line_count == 4
    assert summary.clipped_line_count == 4
    assert summary.accepted_line_count == 2
    assert summary.outside_endpoint_line_count == 2
    assert np.all(summary.accepted_lines[:, :, 0] >= 0.0)
    assert np.all(summary.accepted_lines[:, :, 0] <= 99.0)
    assert np.all(summary.accepted_lines[:, :, 1] >= 0.0)
    assert np.all(summary.accepted_lines[:, :, 1] <= 99.0)


def test_normalized_length_gate_scales_with_image_diagonal():
    config = DeepLsdLineConfig(min_length_diagonal_ratio=0.13)
    line_100 = np.asarray([[[10.0, 50.0], [30.0, 50.0]]])
    line_200 = np.asarray([[[20.0, 100.0], [60.0, 100.0]]])

    _, small = build_line_guide_from_segments(
        line_100,
        source_shape=(100, 100),
        config=config,
    )
    _, large = build_line_guide_from_segments(
        line_200,
        source_shape=(200, 200),
        config=config,
    )

    assert small.accepted_line_count == 1
    assert large.accepted_line_count == 1


def test_soft_support_is_bounded_and_decays_away_from_line():
    guide, summary = build_line_guide_from_segments(
        np.asarray([[[10.0, 50.0], [90.0, 50.0]]]),
        source_shape=(100, 100),
    )

    support = guide.support_map
    assert summary.accepted_line_count == 1
    assert support.dtype == np.float32
    assert float(support.min()) >= 0.0
    assert float(support.max()) <= 1.0
    assert float(support[50, 50]) == pytest.approx(1.0)
    assert 0.0 < float(support[51, 50]) < 1.0
    assert float(support[70, 50]) == pytest.approx(0.0)


def test_empty_or_short_segments_produce_zero_support():
    guide_empty, empty = build_line_guide_from_segments(
        np.empty((0, 2, 2), dtype=np.float64),
        source_shape=(64, 64),
    )
    guide_short, short = build_line_guide_from_segments(
        np.asarray([[[1.0, 1.0], [5.0, 1.0]]]),
        source_shape=(64, 64),
    )

    assert empty.accepted_line_count == 0
    assert short.accepted_line_count == 0
    assert float(guide_empty.support_map.max()) == pytest.approx(0.0)
    assert float(guide_short.support_map.max()) == pytest.approx(0.0)


class _FakeRuntime:
    def __init__(self, lines: np.ndarray):
        self.lines = lines
        self.seen = None

    def infer(self, gray: np.ndarray):
        self.seen = gray.copy()
        return self.lines


def test_build_adapter_converts_rgb_to_gray_and_accepts_fake_runtime():
    source = np.zeros((100, 100, 3), dtype=np.uint8)
    source[:, :] = (255, 0, 0)
    runtime = _FakeRuntime(
        np.asarray([[[10.0, 20.0], [90.0, 20.0]]], dtype=np.float64)
    )

    guide, summary = build_deeplsd_line_guide(
        source,
        config=DeepLsdLineConfig(),
        runtime=runtime,
    )

    assert runtime.seen is not None
    assert runtime.seen.dtype == np.uint8
    assert int(runtime.seen[0, 0]) in range(75, 78)
    assert guide.provider == "deeplsd"
    assert summary.accepted_line_count == 1


def test_attach_preserves_other_analysis_lanes():
    source = np.zeros((100, 100, 3), dtype=np.uint8)
    structural = StructuralGuide(
        ("torso",),
        np.zeros((1, 100, 100), dtype=np.float32),
        "rtmlib",
        "wholebody-balanced",
    )
    base = AnalysisGuidance(structural=structural)
    runtime = _FakeRuntime(
        np.asarray([[[10.0, 20.0], [90.0, 20.0]]], dtype=np.float64)
    )

    combined, summary = attach_deeplsd_lines(
        source,
        config=DeepLsdLineConfig(),
        base_guidance=base,
        runtime=runtime,
    )

    assert summary.accepted_line_count == 1
    assert combined.structural is structural
    assert combined.line is not None
    assert combined.line.provider == "deeplsd"


def test_invalid_segments_and_config_fail_fast():
    with pytest.raises(ValueError):
        build_line_guide_from_segments(
            np.zeros((2, 4), dtype=np.float64),
            source_shape=(100, 100),
        )
    invalid = np.zeros((1, 2, 2), dtype=np.float64)
    invalid[0, 0, 0] = np.nan
    with pytest.raises(ValueError):
        build_line_guide_from_segments(invalid, source_shape=(100, 100))
    with pytest.raises(ValueError):
        DeepLsdLineConfig(min_length_diagonal_ratio=0.0)
    with pytest.raises(ValueError):
        DeepLsdLineConfig(support_radius_diagonal_ratio=0.0)
    with pytest.raises(ValueError):
        DeepLsdLineConfig(min_support_radius_px=5.0, max_support_radius_px=4.0)


def test_runtime_creation_requires_explicit_weights_path():
    with pytest.raises(ValueError):
        create_deeplsd_runtime(DeepLsdLineConfig())


def test_public_import_does_not_eagerly_import_torch_or_deeplsd():
    assert "torch" not in sys.modules
    assert "deeplsd" not in sys.modules
