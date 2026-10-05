import numpy as np
from minimalizer_zerobase.production.structural_motifs import major_color_masses
def test_major_masses_preserve_large_connected_regions():
 a=np.full((40,40,3),240,np.uint8);m=np.zeros((40,40),bool);m[5:35,5:35]=1
 a[5:20,5:35]=(30,40,60);a[20:35,5:35]=(180,80,50)
 xs=major_color_masses(a,m,max_masses=3,min_ratio=.1)
 assert len(xs)>=2
 assert all(not np.any(mm&~m) for mm,_ in xs)
def test_small_noise_is_not_reserved():
 a=np.full((30,30,3),80,np.uint8);m=np.zeros((30,30),bool);m[3:27,3:27]=1
 a[5:7,5:7]=(250,0,0)
 xs=major_color_masses(a,m,max_masses=3,min_ratio=.1)
 assert all(mm.sum()>=m.sum()*.1 for mm,_ in xs)
def test_major_masses_deterministic():
 a=np.full((30,30,3),100,np.uint8);m=np.zeros((30,30),bool);m[4:26,4:26]=1
 x=major_color_masses(a,m);y=major_color_masses(a,m)
 assert len(x)==len(y) and all(np.array_equal(p[0],q[0]) and p[1]==q[1] for p,q in zip(x,y))
