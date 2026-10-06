import numpy as np,pytest
from minimalizer_zerobase.semantic_abstraction.background_composition import *
def test_observes_background_without_golden():
 im=np.full((20,30,3),[20,40,60],np.uint8);s=np.zeros((20,30),bool);s[5:15,10:20]=1;im[s]=[200,100,50]
 r=observe_background_composition(im,s)
 assert r.subject_bbox==(10,5,20,15) and r.dominant_rgb==(20,40,60)
 assert .16<r.subject_area_ratio<.17 and r.border_background_ratio==1.0
def test_internal_hole_is_negative_space_but_not_palette_authority():
 im=np.full((20,20,3),[10,20,30],np.uint8);s=np.zeros((20,20),bool);s[3:17,3:17]=1;s[8:12,8:12]=0;im[8:12,8:12]=[250,0,0]
 r=observe_background_composition(im,s)
 assert r.dominant_rgb==(10,20,30)
def test_invalid_subject_fails():
 im=np.zeros((10,10,3),np.uint8)
 with pytest.raises(ValueError):observe_background_composition(im,np.zeros((10,10),bool))
