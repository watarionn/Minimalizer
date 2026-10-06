import numpy as np
from minimalizer_zerobase.semantic_abstraction.background_field_geometry import *
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
