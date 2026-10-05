from __future__ import annotations
import numpy as np
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.production.frozen_semantic_observer import observations_from_semantic_guide
from minimalizer_zerobase.production.blind_observation import bind_blind_observations

def test_observer_emits_deterministic_nonsemantic_shape_descriptor():
    maps=np.zeros((1,8,8),dtype=float);maps[0,1:7,2:6]=.8
    a=observations_from_semantic_guide(["hair"],maps,CoordinateSpace(8,8))[0]
    b=observations_from_semantic_guide(["hair"],maps,CoordinateSpace(8,8))[0]
    d=a.geometry["mask_descriptor"]
    assert d==b.geometry["mask_descriptor"]
    assert d["grid"]==[4,4]
    assert len(d["occupancy"])==4 and all(len(row)==4 for row in d["occupancy"])
    assert all(0<=v<=1 for row in d["occupancy"] for v in row)

def test_binder_preserves_descriptor_without_granting_new_semantics():
    maps=np.zeros((1,8,8),dtype=float);maps[0,1:7,2:6]=.8
    o=observations_from_semantic_guide(["hair"],maps,CoordinateSpace(8,8))[0]
    row={"evidence_id":o.evidence_id,"semantic_label":o.semantic_label,"confidence":o.confidence,"geometry":o.geometry}
    manifest={"case_id":"x","features":[{"id":"hair","semantic_role":"hair"}]}
    bound=bind_blind_observations(manifest,[row])
    assert bound["authorized_masks"]["hair"]["mask_descriptor"]==o.geometry["mask_descriptor"]
    assert bound["manual_semantic_labels_used"] is False
    assert bound["golden_used"] is False
