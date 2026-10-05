from __future__ import annotations
import numpy as np
import pytest
from minimalizer_zerobase.production.authorized_palette import extract_authorized_palette,PaletteRoleError

def test_palette_is_deterministic_and_uses_only_authorized_region():
    im=np.zeros((10,10,3),dtype=np.uint8);im[:]=[250,250,250]
    im[2:8,2:8]=[210,40,30];im[3:5,3:5]=[20,200,20]
    masks={"hair":{"authorized":True,"bbox":[2,2,6,6]}}
    a=extract_authorized_palette(im,masks);b=extract_authorized_palette(im,masks)
    assert a==b
    assert a["hair"].startswith("#")
    assert a["hair"]!="#fafafa"

def test_palette_does_not_create_features():
    im=np.full((4,4,3),100,dtype=np.uint8)
    assert set(extract_authorized_palette(im,{"hair":{"authorized":True,"bbox":[0,0,4,4]}}))=={"hair"}

def test_palette_rejects_unauthorized_region():
    im=np.zeros((4,4,3),dtype=np.uint8)
    with pytest.raises(PaletteRoleError):
        extract_authorized_palette(im,{"x":{"authorized":False,"bbox":[0,0,4,4]}})

def test_tie_break_is_deterministic():
    im=np.array([[[10,10,10],[250,250,250]]],dtype=np.uint8)
    x=extract_authorized_palette(im,{"x":{"authorized":True,"bbox":[0,0,2,1]}},bins_per_channel=2)
    assert x["x"]=="#0a0a0a"
