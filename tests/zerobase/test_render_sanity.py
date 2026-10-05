import numpy as np
from minimalizer_zerobase.production.render_sanity import evaluate_render_sanity

def test_rejects_white_or_tiny_foreground():
    a=np.full((100,100,3),255,np.uint8); a[:10,:10]=0
    r=evaluate_render_sanity(a)
    assert not r.passed and "foreground_too_sparse" in r.reason

def test_accepts_visible_multicolor_render():
    a=np.full((100,100,3),255,np.uint8); a[10:90,10:50]=[10,20,30];a[10:90,50:90]=[200,80,20]
    r=evaluate_render_sanity(a)
    assert r.passed and r.nonwhite_ratio > .6 and r.unique_color_count >= 3
