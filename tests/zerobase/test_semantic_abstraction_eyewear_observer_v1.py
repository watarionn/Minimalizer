import numpy as np
from minimalizer_zerobase.semantic_abstraction.eyewear_observer_v1 import *

def test_prompt_is_generic_and_frozen():
 assert EYEWEAR_PROMPT=="glasses. goggles. sunglasses. eyewear." and EYEWEAR_OBSERVER_VERSION=="sa7.9-v1"

def test_generic_eyewear_detection_emits_provenance_bbox():
 a=np.zeros((40,50),bool);a[5:35,5:45]=1;m=np.zeros_like(a);m[12:20,15:35]=1
 r=frozen_eyewear_records([EyewearDetection("goggles",.8,.9,m)],head_hair_authority=a,model_id="dino+sam")
 assert len(r)==1 and r[0]["semantic_label"]=="goggles" and r[0]["geometry"]["bbox"]==[15,12,20,8]
 assert r[0]["provenance"]["observer_version"]=="sa7.9-v1"

def test_non_eyewear_is_ignored():
 a=np.ones((20,20),bool);m=np.ones_like(a)
 assert frozen_eyewear_records([EyewearDetection("eyes",.99,.99,m)],head_hair_authority=a,model_id="x")==[]

def test_low_score_fails_closed():
 a=np.ones((20,20),bool);m=np.zeros_like(a);m[5:10,5:10]=1
 assert frozen_eyewear_records([EyewearDetection("glasses",.19,1,m)],head_hair_authority=a,model_id="x")==[]

def test_oversized_head_region_fails_closed():
 a=np.ones((20,20),bool);m=np.ones_like(a)
 assert frozen_eyewear_records([EyewearDetection("eyewear",.9,.9,m)],head_hair_authority=a,model_id="x")==[]

def test_source_mask_is_clipped_to_authority():
 a=np.zeros((20,20),bool);a[5:15,5:15]=1;m=np.zeros_like(a);m[3:10,3:10]=1
 r=frozen_eyewear_records([EyewearDetection("sunglasses",.9,.9,m)],head_hair_authority=a,model_id="x")
 assert r[0]["geometry"]["bbox"]==[5,5,5,5]
