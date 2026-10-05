import numpy as np
from minimalizer_zerobase.production.structural_motifs import garment_panels
def fixture():
 a=np.full((60,60,3),240,np.uint8);g=np.zeros((60,60),bool);g[10:55,10:50]=1
 a[10:28,10:50]=(35,45,70);a[28:55,10:30]=(225,225,220);a[28:55,30:50]=(80,90,110)
 return a,g
def test_garment_panels_recover_multiple_large_masses():
 a,g=fixture();p=garment_panels(a,g)
 assert 2<=len(p)<=4
 assert all(not np.any(m&~g) for m,_ in p)
def test_garment_panels_ignore_tiny_trim():
 a,g=fixture();a[12:14,12:14]=(255,0,0);p=garment_panels(a,g)
 assert all(m.sum()>=g.sum()*.06 for m,_ in p)
def test_garment_panels_are_disjoint_and_deterministic():
 a,g=fixture();x=garment_panels(a,g);y=garment_panels(a,g)
 u=np.zeros_like(g)
 for m,_ in x:
  assert not np.any(u&m);u|=m
 assert len(x)==len(y) and all(np.array_equal(p[0],q[0]) and p[1]==q[1] for p,q in zip(x,y))
