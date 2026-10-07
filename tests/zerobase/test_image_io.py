from __future__ import annotations

import cv2
import numpy as np

from minimalizer_zerobase.image_io import read_cv_image


def test_read_cv_image_accepts_unicode_path(tmp_path):
    path = tmp_path / "日本語画像.png"
    image = np.full((7, 9, 3), (12, 34, 56), dtype=np.uint8)
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    path.write_bytes(encoded.tobytes())

    loaded = read_cv_image(path, cv2.IMREAD_COLOR)

    assert loaded is not None
    assert loaded.shape == image.shape
    assert np.array_equal(loaded, image)


def test_read_cv_image_fails_closed_for_missing_path(tmp_path):
    assert read_cv_image(tmp_path / "存在しない.png") is None
