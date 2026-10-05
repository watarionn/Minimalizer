import numpy as np
from minimalizer_zerobase.production.authorized_palette import extract_authorized_palette_roles

def test_topology_excludes_zero_occupancy_cells_from_palette():
    im=np.zeros((8,8,3),dtype=np.uint8)
    im[:,:4]=[240,20,20]
    im[:,4:]=[20,20,240]
    mask={"x":{"authorized":True,"bbox":[0,0,8,8],"mask_descriptor":{"grid":[4,4],"occupancy":[[1,1,0,0]]*4}}}
    a=extract_authorized_palette_roles(im,mask)
    assert a["x"]["dominant"].startswith("#f")
    assert a["x"]["dominant"]!="#1414f0"

def test_topology_palette_is_deterministic():
    rng=np.random.default_rng(7); im=rng.integers(0,256,(16,16,3),dtype=np.uint8)
    mask={"x":{"authorized":True,"bbox":[0,0,16,16],"mask_descriptor":{"grid":[4,4],"occupancy":[[.1,.2,.3,.4]]*4}}}
    assert extract_authorized_palette_roles(im,mask)==extract_authorized_palette_roles(im,mask)
