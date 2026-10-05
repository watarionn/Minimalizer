import cv2,numpy as np
from minimalizer_zerobase.semantic_abstraction.eyewear_geometry_witness import *
def scene(pair=True,bridge=True):
 im=np.full((120,160,3),220,np.uint8);a=np.ones((120,160),bool);f=np.zeros((120,160),bool);f[35:105,40:120]=1
 if pair:
  cv2.ellipse(im,(62,55),(17,10),0,0,360,(20,20,20),3);cv2.ellipse(im,(98,55),(17,10),0,0,360,(20,20,20),3)
  if bridge:cv2.line(im,(79,55),(81,55),(20,20,20),3)
 return im,a,f
def test_paired_closed_geometry_with_bridge_passes():
 im,a,f=scene();r=observe_geometry_witness(im,a,f);assert r.paired and r.bridge_supported and r.confidence>=MIN_PAIR_SCORE
def test_single_closed_shape_fails():
 im,a,f=scene(False);cv2.ellipse(im,(80,55),(17,10),0,0,360,(20,20,20),3);assert not observe_geometry_witness(im,a,f).paired
def test_eye_like_filled_marks_without_closed_ring_fail():
 im,a,f=scene(False);cv2.circle(im,(62,55),4,(20,20,20),-1);cv2.circle(im,(98,55),4,(20,20,20),-1);assert not observe_geometry_witness(im,a,f).paired
def test_missing_face_fails_closed():
 im,a,f=scene();f[:]=0;assert not observe_geometry_witness(im,a,f).paired
def test_deterministic():
 im,a,f=scene();x=observe_geometry_witness(im,a,f);y=observe_geometry_witness(im,a,f);assert x.pair_score==y.pair_score and np.array_equal(x.mask,y.mask)
