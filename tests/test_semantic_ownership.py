import numpy as np
from minimalizer_zerobase.refine.semantic_ownership import *

def m(x0=1,x1=4):
    a=np.zeros((6,6),bool); a[1:5,x0:x1]=1; return a
def test_identical_owned_part_passes():
    r=evaluate_ownership_retention({"face":m()},{"face":m()},critical_parts=("face",))
    assert r.passed and r.per_part_iou["face"]==1
def test_small_owned_part_move_can_fail_hard_gate():
    r=evaluate_ownership_retention({"face":m()},{"face":m(2,5)},critical_parts=("face",),minimum_iou=.8)
    assert not r.passed
def test_missing_owned_part_fails_closed():
    r=evaluate_ownership_retention({"face":m()},{},critical_parts=("face",))
    assert not r.passed
def test_empty_to_empty_is_retained():
    z=np.zeros((4,4),bool)
    assert mask_iou(z,z)==1
