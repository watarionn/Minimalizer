import numpy as np

from minimalizer_zerobase.semantic_abstraction.palette_role_subdivision import (
    PALETTE_SUBDIVISION_VERSION,
    observe_palette_role_masses,
)


def test_source_only_dominant_roles_are_bounded():
    im=np.zeros((20,20,3),np.uint8);m=np.zeros((20,20),bool);m[2:18,2:18]=1
    im[m]=[220,80,30];im[8:18,2:18]=[120,30,20];im[15:18,15:18]=[0,255,0]
    r=observe_palette_role_masses(im,m,"hair")
    assert 1<=len(r)<=3 and all(x.semantic_part=="hair" for x in r)
    assert all(np.all(x.mask<=m) for x in r)


def test_tiny_noise_not_promoted():
    im=np.full((20,20,3),100,np.uint8);m=np.ones((20,20),bool);im[0,0]=[255,0,0]
    r=observe_palette_role_masses(im,m,"major_clothing")
    assert len(r)==1


def test_deterministic():
    rng=np.random.default_rng(4);im=rng.integers(0,255,(30,30,3),dtype=np.uint8);m=np.ones((30,30),bool)
    a=observe_palette_role_masses(im,m,"hair");b=observe_palette_role_masses(im,m,"hair")
    assert [(x.rgb,x.source_ratio,int(x.mask.sum())) for x in a]==[(x.rgb,x.source_ratio,int(x.mask.sum())) for x in b]
    assert all(np.array_equal(x.mask,y.mask) for x,y in zip(a,b))


def test_compatibility_mass_keeps_all_disconnected_fields_of_same_role():
    im=np.zeros((32,32,3),np.uint8)
    m=np.zeros((32,32),bool)
    m[2:12,2:12]=True
    m[20:30,20:30]=True
    im[m]=[220,80,30]
    r=observe_palette_role_masses(im,m,"hair",max_roles=1)
    assert len(r)==1
    assert int(r[0].mask.sum())==200
    assert np.all(r[0].mask[m])
    assert PALETTE_SUBDIVISION_VERSION=="sa8-compat-v1"


def test_palette_role_count_does_not_cap_disconnected_mass_fields():
    im=np.zeros((40,40,3),np.uint8)
    m=np.zeros((40,40),bool)
    for y,x in ((2,2),(2,26),(26,2),(26,26)):
        m[y:y+10,x:x+10]=True
        im[y:y+10,x:x+10]=[180,60,30]
    r=observe_palette_role_masses(im,m,"major_clothing",max_roles=1)
    assert len(r)==1
    assert int(r[0].mask.sum())==400
