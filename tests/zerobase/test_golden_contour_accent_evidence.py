from __future__ import annotations
import numpy as np
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.production.frozen_semantic_observer import observations_from_semantic_guide
from minimalizer_zerobase.production.blind_observation import bind_blind_observations
from minimalizer_zerobase.production.authorized_palette import extract_authorized_palette_roles

def test_contour_envelope_is_deterministic_shape_only_evidence():
    m=np.zeros((1,16,16),float)
    for y in range(2,14):
        m[0,y,4:min(12,5+y//3)]=.8
    a=observations_from_semantic_guide(["face-skin"],m,CoordinateSpace(16,16))[0]
    b=observations_from_semantic_guide(["face-skin"],m,CoordinateSpace(16,16))[0]
    env=a.geometry["contour_envelope"]
    assert env==b.geometry["contour_envelope"]
    assert env["bands"]==8 and len(env["x_extent"])==8

def test_binder_preserves_contour_without_new_semantics():
    m=np.zeros((1,8,8),float);m[0,1:7,2:6]=.9
    o=observations_from_semantic_guide(["face-skin"],m,CoordinateSpace(8,8))[0]
    row={"evidence_id":o.evidence_id,"semantic_label":o.semantic_label,"confidence":o.confidence,"geometry":o.geometry}
    bound=bind_blind_observations({"case_id":"x","features":[{"id":"face","semantic_role":"face-skin"}]},[row])
    assert bound["authorized_masks"]["face"]["contour_envelope"]==o.geometry["contour_envelope"]
    assert bound["manual_semantic_labels_used"] is False

def test_local_accent_preserves_small_saturated_color():
    im=np.full((20,20,3),[220,210,200],dtype=np.uint8)
    im[8:12,8:12]=[20,180,40]
    roles=extract_authorized_palette_roles(im,{"feature":{"authorized":True,"bbox":[0,0,20,20]}})
    assert roles["feature"]["dominant"] != roles["feature"]["accent"]
    assert roles["feature"]["accent"] is not None

def test_accent_api_cannot_create_features():
    im=np.full((4,4,3),100,dtype=np.uint8)
    assert set(extract_authorized_palette_roles(im,{"hair":{"authorized":True,"bbox":[0,0,4,4]}}))=={"hair"}
