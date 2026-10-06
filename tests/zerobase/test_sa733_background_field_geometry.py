import cv2,numpy as np
from minimalizer_zerobase.semantic_abstraction.background_field_geometry import *\nfrom minimalizer_zerobase.semantic_abstraction.background_field_geometry import _coarsest_safe_polygon
def test_background_fields_never_overlap_subject():
 im=np.zeros((40,40,3),np.uint8);im[:]=[20,30,40];s=np.zeros((40,40),bool);s[10:30,14:26]=1;im[:,20:]=[180,90,30]
 rows=reauthor_background_fields(im,s)
 assert len(rows)<=3
 assert all(r.subject_overlap==0 for r in rows)
 assert all(r.source_coverage>=MIN_SOURCE_COVERAGE for r in rows)
def test_deterministic_fields():
 im=np.zeros((30,30,3),np.uint8);im[:15]=[10,20,30];im[15:]=[150,120,90];s=np.zeros((30,30),bool);s[8:22,10:20]=1
 a=reauthor_background_fields(im,s);b=reauthor_background_fields(im,s)
 assert [(x.rgb,x.source_area,x.retained_area,len(x.polygon)) for x in a]==[(x.rgb,x.source_area,x.retained_area,len(x.polygon)) for x in b]
def test_small_background_returns_empty():
 im=np.zeros((10,10,3),np.uint8);s=np.ones((10,10),bool);s[:2,:2]=0
 assert reauthor_background_fields(im,s)==()
def test_uniform_field_wrapping_subject_fails_closed():
 im=np.full((80,80,3),[180,90,30],np.uint8);s=np.zeros((80,80),bool);s[20:60,28:52]=1
 assert reauthor_background_fields(im,s,max_fields=1)==()
def test_adaptive_contour_preserves_open_concavity():
 comp=np.zeros((80,80),bool);comp[:,0:18]=1;comp[0:18,0:62]=1;comp[62:80,0:62]=1
 subject=np.zeros((80,80),bool);subject[24:56,20:50]=1
 cs,_=cv2.findContours(comp.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
 chosen=_coarsest_safe_polygon(max(cs,key=cv2.contourArea),comp,subject)
 assert chosen is not None
 poly,_,_,coverage,expansion,overlap=chosen
 assert overlap==0 and coverage>=MIN_SOURCE_COVERAGE and expansion<=MAX_EXPANSION_RATIO and len(poly)>=3
