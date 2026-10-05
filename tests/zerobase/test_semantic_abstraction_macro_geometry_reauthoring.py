import cv2,numpy as np
from minimalizer_zerobase.semantic_abstraction.macro_geometry_reauthoring import *
def masks():
 h=np.zeros((120,100),np.uint8);c=np.zeros_like(h)
 cv2.ellipse(h,(50,30),(28,24),0,0,360,1,-1);h[20:22,10:12]=1
 cv2.rectangle(c,(28,52),(72,105),1,-1);c[70:72,5:7]=1
 return h,c
def test_macro_limits_and_roles():
 h,c=masks();r=reauthor_macro_geometry(hair_mask=h,clothing_mask=c)
 assert sum(x.semantic_part=="hair" for x in r)<=3 and sum(x.semantic_part=="major_clothing" for x in r)<=2
 assert {x.semantic_part for x in r}=={"hair","major_clothing"}
def test_small_noise_does_not_become_mass():
 h,c=masks();r=reauthor_macro_geometry(hair_mask=h,clothing_mask=c)
 assert len(r)==2
def test_polygons_are_coarse():
 h,c=masks();r=reauthor_macro_geometry(hair_mask=h,clothing_mask=c)
 assert all(3<=len(x.polygon)<=12 for x in r)
def test_deterministic():
 h,c=masks();a=reauthor_macro_geometry(hair_mask=h,clothing_mask=c);b=reauthor_macro_geometry(hair_mask=h,clothing_mask=c)
 assert all(np.array_equal(x.polygon,y.polygon) for x,y in zip(a,b))
