import numpy as np
from minimalizer_zerobase.refine.constrained_polygon import *
def cp(step,loss,iou): return PolygonCheckpoint(step,loss,iou,np.zeros((3,2)))
def test_selects_best_loss_among_feasible_steps():
    r=choose_best_feasible([cp(1,.9,.99),cp(2,.8,.986),cp(3,.7,.98)],minimum_iou=.985,initial_loss=1)
    assert r.step==2
def test_requires_real_improvement():
    assert choose_best_feasible([cp(1,1,.99)],initial_loss=1) is None
def test_no_feasible_checkpoint_returns_none():
    assert choose_best_feasible([cp(1,.5,.9)],initial_loss=1) is None
def test_hard_iou_identical_is_one():
    a=np.array([[1,0],[0,0]],bool); assert hard_iou(a,a)==1
