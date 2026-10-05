import numpy as np
from minimalizer_zerobase.production.accent_region_observer import propose_accent_regions

def test_accent_regions_are_semantic_free_and_deterministic():
    im=np.full((32,32,3),[180,150,130],dtype=np.uint8)
    im[16:24,12:20]=[20,210,50]
    mask=np.ones((32,32),dtype=np.uint8)
    a=propose_accent_regions(im,mask); b=propose_accent_regions(im,mask)
    assert a==b and a
    assert all(x["semantic_label"] is None and x["authority"] is False for x in a)

def test_accent_region_localizes_contrasting_cell():
    im=np.full((16,16,3),[120,120,120],dtype=np.uint8)
    im[8:12,8:12]=[250,20,180]
    mask=np.ones((16,16),dtype=np.uint8)
    rows=propose_accent_regions(im,mask)
    assert rows
    x,y,w,h=rows[0]["bbox"]
    assert x>=8 and y>=8

def test_empty_subject_returns_no_hypotheses():
    im=np.zeros((8,8,3),dtype=np.uint8)
    assert propose_accent_regions(im,np.zeros((8,8),dtype=np.uint8))==[]
