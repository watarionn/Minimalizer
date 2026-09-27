import numpy as np
import pytest
from minimalizer_zerobase.analyzers.slic_regions import SLICRegionAdapter
from minimalizer_zerobase.core.coordinates import CoordinateSpace

def test_alpha_foreground_filter_excludes_transparent_regions():
    image = np.zeros((20, 20, 4), dtype=np.uint8)
    image[:, :, :3] = 255
    image[5:15, 5:15, :3] = 0
    image[5:15, 5:15, 3] = 255
    evidence = SLICRegionAdapter(n_segments=16, min_foreground_ratio=0.5).analyze(
        image, CoordinateSpace(20, 20)
    )
    assert evidence
    assert all(e.semantic_label == "foreground" for e in evidence)
    assert all(e.normalization["foreground_source"] == "alpha" for e in evidence)
    assert all(e.normalization["foreground_ratio"] >= 0.5 for e in evidence)

def test_foreground_filter_fails_closed_without_alpha():
    image = np.zeros((20, 20, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="alpha channel"):
        SLICRegionAdapter(min_foreground_ratio=0.5).analyze(image, CoordinateSpace(20, 20))
