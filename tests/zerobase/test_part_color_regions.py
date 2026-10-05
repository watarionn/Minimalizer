import numpy as np
from minimalizer_zerobase.production.part_color_regions import extract_part_color_regions
def test_keeps_connected_major_and_accent_regions_inside_part():
 a=np.full((40,40,3),255,np.uint8);m=np.zeros((40,40),bool);m[5:35,5:35]=1
 a[m]=[30,40,60];a[8:20,8:20]=[240,240,235];a[12:30,19:23]=[90,220,20]
 r=extract_part_color_regions(a,m,max_regions=3)
 cols=[x.rgb for x in r]
 assert len(r)==3
 assert any(c[1]>150 and c[0]<150 for c in cols)
 assert all(np.all(x.mask<=m) for x in r)
def test_deterministic():
 a=np.zeros((20,20,3),np.uint8);m=np.ones((20,20),bool);a[:10]=[220,80,20];a[10:]=[20,30,60]
 assert [(x.rgb,x.area) for x in extract_part_color_regions(a,m)]==[(x.rgb,x.area) for x in extract_part_color_regions(a,m)]
