from __future__ import annotations

import numpy as np
import pytest

from minimalizer_zerobase.reviewed_sa10.parts_decomposition import (
    _normalize_hough_lines,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (np.array([[[1, 2, 3, 4]], [[5, 6, 7, 8]]], dtype=np.int32), (2, 4)),
        (np.array([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.int32), (2, 4)),
        (np.array([1, 2, 3, 4], dtype=np.int32), (1, 4)),
        (np.array([1, 2, 3, 4, 5, 6, 7, 8], dtype=np.int32), (2, 4)),
    ],
)
def test_hough_lines_normalize_to_n_by_four(value, expected):
    normalized = _normalize_hough_lines(value)
    assert normalized.shape == expected
    assert normalized.dtype == np.int32
    expected_values = [[1, 2, 3, 4]] if expected == (1, 4) else [[1, 2, 3, 4], [5, 6, 7, 8]]
    np.testing.assert_array_equal(normalized, expected_values)


@pytest.mark.parametrize("value", [np.array([], dtype=np.int32), np.array([1, 2, 3])])
def test_malformed_hough_lines_fail_closed(value):
    normalized = _normalize_hough_lines(value)
    assert normalized.shape == (0, 4)
