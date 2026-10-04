from __future__ import annotations

import numpy as np
import pytest

from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.production.frozen_semantic_observer import (
    observations_from_semantic_guide,
)


def _space():
    return CoordinateSpace(width=8,height=6)


def test_frozen_semantic_map_becomes_labelled_bbox_evidence():
    maps=np.zeros((2,6,8),dtype=np.float32)
    maps[0,1:4,2:6]=0.7
    obs=observations_from_semantic_guide(("hair","accessory"),maps,_space())
    assert len(obs)==1
    assert obs[0].semantic_label=="hair"
    assert obs[0].geometry["bbox"]==[2,1,4,3]
    assert obs[0].normalization["observer_role"]=="hypothesis-only"


def test_threshold_is_frozen():
    maps=np.zeros((1,6,8),dtype=np.float32)
    with pytest.raises(ValueError,match="fixed at 0.20"):
        observations_from_semantic_guide(("hair",),maps,_space(),active_threshold=0.1)


def test_below_threshold_is_not_promoted():
    maps=np.full((1,6,8),0.19,dtype=np.float32)
    assert observations_from_semantic_guide(("hair",),maps,_space())==[]


def test_nonfinite_maps_fail_closed():
    maps=np.zeros((1,6,8),dtype=np.float32); maps[0,0,0]=np.nan
    with pytest.raises(ValueError,match="finite"):
        observations_from_semantic_guide(("hair",),maps,_space())


def test_adapter_does_not_invent_finer_semantics():
    maps=np.zeros((1,6,8),dtype=np.float32); maps[0,2:4,2:4]=0.8
    obs=observations_from_semantic_guide(("accessory",),maps,_space())
    assert [x.semantic_label for x in obs]==["accessory"]
