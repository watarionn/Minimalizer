import numpy as np
from minimalizer_zerobase.production.semantic_contour import semantic_contour
def test_semantic_contour_preserves_concavity_not_bbox():
 m=np.zeros((40,40),bool);m[5:35,5:12]=1;m[28:35,5:32]=1
 p=semantic_contour(m,12)
 assert 4 < len(p) <= 12
 xs={x for x,y in p};ys={y for x,y in p}
 assert len(xs)>2 and len(ys)>2
def test_deterministic():
 m=np.zeros((20,20),bool);m[3:17,4:15]=1;m[8:12,10:18]=1
 assert semantic_contour(m,10)==semantic_contour(m,10)
