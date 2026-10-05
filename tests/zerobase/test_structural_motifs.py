import numpy as np
from minimalizer_zerobase.production.structural_motifs import arm_axis_band,clothing_major_regions
def test_arm_band_stays_inside_authority():
 m=np.zeros((50,50),bool)
 for y in range(8,43):
  x=10+y//3;m[y,max(0,x-4):min(50,x+5)]=1
 out=arm_axis_band(m)
 assert out.any() and np.all(out<=m) and out.sum()>=m.sum()*.38
def test_clothing_regions_keep_large_color_masses():
 a=np.full((40,40,3),240,np.uint8);m=np.zeros((40,40),bool);m[5:35,8:32]=1
 a[5:20,8:32]=(30,40,60);a[20:35,8:32]=(220,220,215)
 r=clothing_major_regions(a,m,max_regions=4)
 assert len(r)>=2
 assert all(np.all(x[0]<=m) for x in r)
def test_structural_motifs_are_deterministic():
 a=np.full((20,20,3),100,np.uint8);m=np.zeros((20,20),bool);m[3:17,5:15]=1
 x=clothing_major_regions(a,m);y=clothing_major_regions(a,m)
 assert [(z[1],int(z[0].sum())) for z in x]==[(z[1],int(z[0].sum())) for z in y]
