import numpy as np
import pytest

from minimalizer_zerobase.evaluation.forbidden_face_detail_gate import (
    forbidden_face_detail_ratio,
)
from minimalizer_zerobase.semantic_abstraction.face_raster_guard import (
    apply_face_raster_guard,
)


def test_face_guard_flattens_only_authorized_face_pixels():
    source = np.full((40, 40, 3), [245, 220, 210], dtype=np.uint8)
    source[12:16, 12:16] = [250, 225, 218]
    face = np.zeros((40, 40), dtype=bool)
    face[10:30, 10:30] = True

    rendered = np.full((40, 40, 3), [255, 255, 255], dtype=np.uint8)
    rendered[14:18, 14:18] = [20, 20, 20]
    before = rendered.copy()

    result = apply_face_raster_guard(rendered, source, face)

    assert result.changed_outside_face_pixels == 0
    assert np.array_equal(result.rgb[~face], before[~face])
    assert result.fill_rgb in {
        tuple(int(v) for v in row) for row in source[face]
    }
    assert forbidden_face_detail_ratio(result.rgb, face) == 0.0


def test_face_guard_is_deterministic():
    source = np.full((30, 30, 3), [240, 210, 200], dtype=np.uint8)
    face = np.zeros((30, 30), dtype=bool)
    face[8:22, 9:21] = True
    rendered = np.full((30, 30, 3), [255, 255, 255], dtype=np.uint8)

    a = apply_face_raster_guard(rendered, source, face)
    b = apply_face_raster_guard(rendered, source, face)

    assert a.fill_rgb == b.fill_rgb
    assert np.array_equal(a.rgb, b.rgb)


def test_face_guard_rejects_small_or_mismatched_mask():
    source = np.zeros((20, 20, 3), dtype=np.uint8)
    rendered = np.zeros((20, 20, 3), dtype=np.uint8)

    with pytest.raises(ValueError, match="too small"):
        apply_face_raster_guard(
            rendered,
            source,
            np.zeros((20, 20), dtype=bool),
        )

    with pytest.raises(ValueError, match="shape mismatch"):
        apply_face_raster_guard(
            rendered,
            source,
            np.ones((19, 20), dtype=bool),
        )
