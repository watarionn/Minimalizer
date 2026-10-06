import numpy as np
from minimalizer_zerobase.production.palette_budget_regions import propose_palette_budget_regions

def test_sa8_regions_are_source_subsets_and_bounded():
 a=np.zeros((40,40,3),np.uint8);m=np.zeros((40,40),bool)
 for y,x in ((2,2),(2,26),(26,2),(26,26)):m[y:y+10,x:x+10]=1;a[y:y+10,x:x+10]=[180,60,30]
 r=propose_palette_budget_regions(a,m,"hair",palette_role_budget=1,primitive_budget=2)
 assert len(r)==2
 assert all(np.all(x.mask<=m) for x in r)
 assert all(x.area==int(x.mask.sum()) for x in r)
