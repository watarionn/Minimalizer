import numpy as np
from minimalizer_zerobase.production.structural_motifs import collar_shape_segments
def fixture():
 a=np.full((60,60,3),220,np.uint8);g=np.zeros((60,60),bool);g[18:55,10:50]=1;h=np.zeros_like(g);h[3:20,22:38]=1
 for y in range(19,36):
  x1=22-(y-19)//3;x2=37+(y-19)//3
  a[y,max(10,x1-2):x1+2]=(30,40,60);a[y,x2:min(50,x2+4)]=(30,40,60)
 return a,g,h
def test_collar_segments_bounded_and_inside_authority():
 a,g,h=fixture();xs=collar_shape_segments(a,g,h)
 assert 1<=len(xs)<=2
 assert all(not np.any(x&~g) for x in xs)
def test_collar_segments_are_upper_garment():
 a,g,h=fixture();xs=collar_shape_segments(a,g,h)
 gy=np.where(g)[0].mean()
 assert all(np.where(x)[0].mean()<gy for x in xs)
def test_collar_grammar_deterministic():
 a,g,h=fixture();x=collar_shape_segments(a,g,h);y=collar_shape_segments(a,g,h)
 assert len(x)==len(y) and all(np.array_equal(p,q) for p,q in zip(x,y))
