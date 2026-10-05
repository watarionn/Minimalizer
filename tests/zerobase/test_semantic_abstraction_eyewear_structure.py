import numpy as np
import cv2
from minimalizer_zerobase.semantic_abstraction.eyewear_structure import observe_eyewear_structure


def _fixture(with_pair=True):
    rgb=np.full((120,120,3),190,np.uint8)
    head=np.zeros((120,120),bool);hair=np.zeros_like(head);face=np.zeros_like(head)
    head[10:85,20:100]=1;hair[5:55,15:105]=1;face[42:92,35:85]=1
    if with_pair:
        cv2.ellipse(rgb,(43,35),(13,8),-8,0,360,(35,45,55),3)
        cv2.ellipse(rgb,(75,34),(13,8),8,0,360,(35,45,55),3)
        cv2.line(rgb,(56,34),(62,34),(35,45,55),3)
    return rgb,head,hair,face


def test_paired_worn_structure_yields_two_lenses_and_bridge():
    rgb,h,ha,f=_fixture()
    e=observe_eyewear_structure(rgb,h,ha,f)
    assert e.paired
    assert e.left_lens.sum()>0 and e.right_lens.sum()>0
    assert e.frame.sum()>0
    assert e.bridge.sum()>0
    assert e.confidence>=.6


def test_structure_stays_inside_head_or_hair_authority():
    rgb,h,ha,f=_fixture();e=observe_eyewear_structure(rgb,h,ha,f)
    assert not np.any(e.mask&~(h|ha))


def test_face_only_eye_like_marks_do_not_become_eyewear():
    rgb,h,ha,f=_fixture(False)
    cv2.circle(rgb,(48,63),4,(30,30,30),-1);cv2.circle(rgb,(72,63),4,(30,30,30),-1)
    e=observe_eyewear_structure(rgb,h,ha,f)
    assert not e.paired
    assert e.left_lens.sum()==0 and e.right_lens.sum()==0


def test_missing_face_fails_closed_without_inventing_structure():
    rgb,h,ha,f=_fixture();f[:]=0
    e=observe_eyewear_structure(rgb,h,ha,f)
    assert not e.paired and e.mask.sum()==0 and e.confidence==0


def test_observer_is_deterministic():
    args=_fixture();a=observe_eyewear_structure(*args);b=observe_eyewear_structure(*args)
    assert a.to_dict()==b.to_dict()
    assert np.array_equal(a.mask,b.mask)
