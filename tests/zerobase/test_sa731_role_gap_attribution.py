import numpy as np
from minimalizer_zerobase.evaluation.role_gap_attribution import *
def test_role_gap_ranks_large_wrong_region_first():
 a=np.zeros((20,20,3),np.uint8);g=a.copy();g[:10]=255;g[15:17,15:17]=255
 masks={"large":np.indices((20,20))[0]<10,"small":np.zeros((20,20),bool)}
 masks["small"][15:17,15:17]=1
 r=attribute_role_gaps(a,g,masks)
 assert r[0].role=="large" and r[0].weighted_gap>r[1].weighted_gap
def test_empty_mask_is_ignored_and_deterministic():
 a=np.zeros((8,8,3),np.uint8);m={"z":np.zeros((8,8),bool),"a":np.ones((8,8),bool)}
 x=attribute_role_gaps(a,a,m);y=attribute_role_gaps(a,a,m)
 assert x==y and len(x)==1 and x[0].role=="a"
def test_shape_mismatch_fails():
 import pytest
 with pytest.raises(ValueError):attribute_role_gaps(np.zeros((2,2,3),np.uint8),np.zeros((3,3,3),np.uint8),{})
