import numpy as np
from minimalizer_zerobase.semantic_abstraction.palette_role_subdivision import *
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
