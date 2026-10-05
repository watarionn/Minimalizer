import numpy as np
from minimalizer_zerobase.evaluation.forbidden_face_detail_gate import forbidden_face_detail_ratio,passes_forbidden_face_gate
def test_flat_head_passes():
 a=np.full((30,30,3),(220,180,160),np.uint8);h=np.zeros((30,30),bool);h[5:25,8:22]=1
 assert passes_forbidden_face_gate(a,h)
def test_eye_like_internal_detail_fails():
 a=np.full((30,30,3),(220,180,160),np.uint8);h=np.zeros((30,30),bool);h[5:25,8:22]=1
 a[12:15,11:14]=(30,30,30);a[12:15,17:20]=(30,30,30)
 assert forbidden_face_detail_ratio(a,h)>.025
 assert not passes_forbidden_face_gate(a,h)
def test_outside_head_detail_is_ignored():
 a=np.full((30,30,3),(220,180,160),np.uint8);h=np.zeros((30,30),bool);h[5:25,8:22]=1;a[1:5,1:5]=(0,0,0)
 assert passes_forbidden_face_gate(a,h)
