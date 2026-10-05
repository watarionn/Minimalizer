import numpy as np
from minimalizer_zerobase.production.graph_macro_renderer import _strengthened_accent_mask
def test_accent_strength_grows_inside_authority():
 authority=np.zeros((20,20),bool);authority[3:17,3:17]=1
 m=np.zeros_like(authority);m[9:11,9:11]=1
 out=_strengthened_accent_mask(m,authority,target_ratio=1.5)
 assert out.sum()>=m.sum()
 assert out.sum()<=authority.sum()
 assert np.all(out<=authority)
def test_accent_strength_is_deterministic():
 authority=np.ones((12,12),bool);m=np.zeros_like(authority);m[5:7,5:7]=1
 assert np.array_equal(_strengthened_accent_mask(m,authority),_strengthened_accent_mask(m,authority))
