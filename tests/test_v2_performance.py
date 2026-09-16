from __future__ import annotations
import numpy as np
import pytest
from minimalize_engine.v2.pipeline import minimalize_v2
from minimalize_engine.v2.performance import profile_v2_rgb
from minimalize_engine.v2.regression import algorithm_digest

def _image() -> np.ndarray:
    image=np.zeros((40,48,3),dtype=np.uint8)
    image[:,:24]=(220,70,95)
    image[:,24:] = (55,100,210)
    image[8:32,16:32]=(245,215,75)
    return image

def test_profile_v2_is_observational_and_deterministic():
    image=_image()
    direct=minimalize_v2(image,presets=("minimal",))
    profile=profile_v2_rgb(image,repeats=2)
    expected=algorithm_digest(direct,"minimal")
    assert profile.mean_wall_seconds > 0.0
    assert profile.mean_phase_seconds["preprocessing"] > 0.0
    assert profile.mean_phase_seconds["region_merge"] > 0.0
    assert profile.mean_phase_seconds["minimal.contour"] > 0.0
    assert len(profile.samples) == 2
    assert all(sample.algorithm_digest == expected for sample in profile.samples)
    assert all(0.0 <= share <= 1.0 for share in profile.phase_share.values())

def test_profile_v2_rejects_non_positive_repeats():
    with pytest.raises(ValueError, match="repeats must be positive"):
        profile_v2_rgb(_image(),repeats=0)
