import numpy as np
from minimalizer_zerobase.evaluation.visual_delta_gate import visual_delta_ratio,passes_visual_delta
def test_visual_delta_rejects_near_identical_stage():
 a=np.zeros((20,20,3),np.uint8);b=a.copy();b[:1,:1]=255
 assert visual_delta_ratio(a,b)<.015 and not passes_visual_delta(a,b)
def test_visual_delta_accepts_meaningful_change():
 a=np.zeros((20,20,3),np.uint8);b=a.copy();b[:5,:5]=255
 assert passes_visual_delta(a,b)
