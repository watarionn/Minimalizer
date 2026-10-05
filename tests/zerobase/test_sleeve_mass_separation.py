import numpy as np
from minimalizer_zerobase.production.structural_motifs import sleeve_forearm_masses
def test_sleeve_forearm_split_preserves_arm():
 a=np.full((50,50,3),230,np.uint8);m=np.zeros((50,50),bool);m[8:42,8:16]=1;t=np.zeros_like(m);t[3:18,14:34]=1
 a[8:24,8:16]=(30,40,65);a[24:42,8:16]=(205,160,135)
 s,f=sleeve_forearm_masses(a,m,t)
 assert s.any() and f.any();assert not np.any(s&f);assert np.array_equal(s|f,m)
def test_sleeve_is_torso_side():
 a=np.full((50,50,3),100,np.uint8);m=np.zeros((50,50),bool);m[8:42,8:16]=1;t=np.zeros_like(m);t[2:15,14:34]=1
 a[8:22,8:16]=(20,30,50);a[22:42,8:16]=(200,160,130)
 s,f=sleeve_forearm_masses(a,m,t)
 assert np.where(s)[0].mean()<np.where(f)[0].mean()
def test_split_is_deterministic():
 a=np.full((30,30,3),120,np.uint8);m=np.zeros((30,30),bool);m[4:26,5:11]=1;t=np.zeros_like(m);t[2:12,10:22]=1
 x=sleeve_forearm_masses(a,m,t);y=sleeve_forearm_masses(a,m,t)
 assert all(np.array_equal(p,q) for p,q in zip(x,y))
