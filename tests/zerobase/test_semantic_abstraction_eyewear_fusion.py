import cv2
import numpy as np
from minimalizer_zerobase.semantic_abstraction.eyewear_structure import observe_eyewear_structure
from minimalizer_zerobase.semantic_abstraction.eyewear_fusion import EyewearObserverEvidence,fuse_eyewear_evidence


def _fixture():
    rgb=np.full((120,120,3),190,np.uint8);h=np.zeros((120,120),bool);ha=np.zeros_like(h);f=np.zeros_like(h)
    h[10:85,20:100]=1;ha[5:55,15:105]=1;f[42:92,35:85]=1
    cv2.ellipse(rgb,(43,35),(13,8),-8,0,360,(35,45,55),3);cv2.ellipse(rgb,(75,34),(13,8),8,0,360,(35,45,55),3);cv2.line(rgb,(56,34),(62,34),(35,45,55),3)
    s=observe_eyewear_structure(rgb,h,ha,f)
    return rgb,h,ha,f,s


def test_independent_region_and_structural_agreement_promotes():
    _,h,ha,f,s=_fixture()
    region=EyewearObserverEvidence("sam:eyewear",s.mask,.82,"region")
    r=fuse_eyewear_evidence(s,(region,),head_mask=h,hair_mask=ha,face_mask=f)
    assert r.promoted and "structural" in r.supporting_observers and "sam:eyewear" in r.supporting_observers


def test_confidence_alone_without_independent_role_fails_closed():
    _,h,ha,f,s=_fixture()
    empty=type(s)(np.zeros_like(h),np.zeros_like(h),np.zeros_like(h),np.zeros_like(h),0,False)
    a=EyewearObserverEvidence("sam:a",s.mask,.99,"region");b=EyewearObserverEvidence("sam:b",s.mask,.99,"region")
    r=fuse_eyewear_evidence(empty,(a,b),head_mask=h,hair_mask=ha,face_mask=f)
    assert not r.promoted and r.reason=="insufficient_independent_roles"


def test_disjoint_observers_do_not_promote():
    _,h,ha,f,s=_fixture();m=np.zeros_like(h);m[12:20,20:30]=1
    r=fuse_eyewear_evidence(s,(EyewearObserverEvidence("sam:x",m,.9,"region"),),head_mask=h,hair_mask=ha,face_mask=f)
    assert not r.promoted and r.reason=="no_spatial_agreement"


def test_face_only_feature_risk_is_rejected():
    _,h,ha,f,s=_fixture();empty=type(s)(np.zeros_like(h),np.zeros_like(h),np.zeros_like(h),np.zeros_like(h),0,False)
    m=np.zeros_like(h);m[55:70,43:77]=1
    obs=(EyewearObserverEvidence("sam:x",m,.9,"region"),EyewearObserverEvidence("dino:x",m,.9,"feature_local"))
    r=fuse_eyewear_evidence(empty,obs,head_mask=h,hair_mask=ha,face_mask=f)
    assert not r.promoted and r.reason=="face_feature_risk"


def test_observer_outside_authority_cannot_rescue_candidate():
    _,h,ha,f,s=_fixture();m=np.ones_like(h)
    r=fuse_eyewear_evidence(s,(EyewearObserverEvidence("sam:x",m,.99,"region"),),head_mask=h,hair_mask=ha,face_mask=f)
    assert not r.promoted


def test_fusion_is_order_invariant():
    _,h,ha,f,s=_fixture();a=EyewearObserverEvidence("sam:x",s.mask,.8,"region");b=EyewearObserverEvidence("dino:x",s.mask,.7,"feature_local")
    x=fuse_eyewear_evidence(s,(a,b),head_mask=h,hair_mask=ha,face_mask=f);y=fuse_eyewear_evidence(s,(b,a),head_mask=h,hair_mask=ha,face_mask=f)
    assert x.to_dict()==y.to_dict() and np.array_equal(x.mask,y.mask)
