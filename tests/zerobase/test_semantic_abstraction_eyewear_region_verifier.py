import cv2,numpy as np
from minimalizer_zerobase.semantic_abstraction.eyewear_region_verifier import *
def base():
 im=np.full((140,180,3),220,np.uint8);a=np.ones((140,180),bool);c=np.zeros((140,180),bool);c[35:90,35:145]=1;return im,a,c
def test_glasses_candidate_passes():
 im,a,c=base();cv2.ellipse(im,(70,60),(22,13),0,0,360,(20,20,20),3);cv2.ellipse(im,(110,60),(22,13),0,0,360,(20,20,20),3);cv2.line(im,(92,60),(88,60),(20,20,20),3)
 r=verify_eyewear_region(im,c,a);assert r.accepted and r.bridge_supported
def test_eye_dots_fail():
 im,a,c=base();cv2.circle(im,(70,60),5,(20,20,20),-1);cv2.circle(im,(110,60),5,(20,20,20),-1);assert not verify_eyewear_region(im,c,a).accepted
def test_single_loop_fails():
 im,a,c=base();cv2.ellipse(im,(90,60),(25,15),0,0,360,(20,20,20),3);assert not verify_eyewear_region(im,c,a).accepted
def test_huge_candidate_fails():
 im,a,c=base();c[:]=1;assert verify_eyewear_region(im,c,a).reason=="too_large"
def test_verifier_never_invents_geometry():
 im,a,c=base();cv2.ellipse(im,(70,60),(22,13),0,0,360,(20,20,20),3);cv2.ellipse(im,(110,60),(22,13),0,0,360,(20,20,20),3);cv2.line(im,(92,60),(88,60),(20,20,20),3)
 r=verify_eyewear_region(im,c,a);assert np.array_equal(r.mask,c&a)
