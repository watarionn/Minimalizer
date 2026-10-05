import numpy as np
from minimalizer_zerobase.production.structural_motifs import global_mass_regions
def test_global_masses_prioritize_subject_scale_regions():
 a=np.full((50,50,3),240,np.uint8);p={}
 p["torso"]=np.zeros((50,50),bool);p["torso"][15:40,12:38]=1;a[15:28,12:38]=(30,40,70);a[28:40,12:38]=(220,220,215)
 p["hair"]=np.zeros((50,50),bool);p["hair"][4:17,15:35]=1;a[4:17,15:35]=(210,100,40)
 r=global_mass_regions(a,p,min_subject_ratio=.05)
 assert len(r)>=3 and all(m.sum()>=.05*(p["torso"]|p["hair"]).sum() for _,m,_ in r)
def test_global_masses_remain_inside_role_authority():
 a=np.zeros((30,30,3),np.uint8);m=np.zeros((30,30),bool);m[5:25,5:25]=1
 for role,x,_ in global_mass_regions(a,{"torso":m},min_subject_ratio=.02): assert not np.any(x&~m)
def test_global_masses_deterministic():
 a=np.zeros((30,30,3),np.uint8);m=np.zeros((30,30),bool);m[5:25,5:25]=1
 x=global_mass_regions(a,{"torso":m});y=global_mass_regions(a,{"torso":m})
 assert len(x)==len(y) and all(p[0]==q[0] and np.array_equal(p[1],q[1]) and p[2]==q[2] for p,q in zip(x,y))
