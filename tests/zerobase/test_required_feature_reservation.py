import numpy as np
from minimalizer_zerobase.production.structural_motifs import reserve_identity_accents
def test_reserves_compact_high_contrast_accent():
 a=np.full((60,60,3),(40,45,60),np.uint8);m=np.zeros((60,60),bool);m[10:55,10:50]=1
 a[22:34,28:34]=(80,210,30)
 r=reserve_identity_accents(a,m)
 assert r and any(np.any(x[0][22:34,28:34]) for x in r)
def test_ignores_tiny_noise_and_large_base():
 a=np.full((50,50,3),(30,40,60),np.uint8);m=np.zeros((50,50),bool);m[5:45,5:45]=1;a[7,7]=(255,0,0)
 r=reserve_identity_accents(a,m)
 assert all(x[0].sum()>=m.sum()*.003 for x in r)
def test_reservation_stays_inside_authority_and_is_deterministic():
 a=np.full((50,50,3),(30,40,60),np.uint8);m=np.zeros((50,50),bool);m[5:45,5:45]=1;a[20:30,22:28]=(200,180,20)
 x=reserve_identity_accents(a,m);y=reserve_identity_accents(a,m)
 assert len(x)==len(y)
 for p,q in zip(x,y):
  assert not np.any(p[0]&~m) and np.array_equal(p[0],q[0]) and p[1]==q[1]
