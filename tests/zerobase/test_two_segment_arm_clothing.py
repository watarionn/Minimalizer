import numpy as np
from minimalizer_zerobase.production.structural_motifs import two_segment_arm_masks,clothing_authority
def test_two_segment_arm_preserves_mass_and_authority():
 arm=np.zeros((40,40),bool);arm[5:35,8:14]=1
 torso=np.zeros_like(arm);torso[2:18,12:30]=1
 near,far=two_segment_arm_masks(arm,torso)
 assert np.all(near<=arm) and np.all(far<=arm)
 assert not np.any(near&far)
 assert (near|far).sum()==arm.sum()
 assert near.any() and far.any()
def test_near_segment_is_closer_to_torso():
 arm=np.zeros((40,40),bool);arm[5:35,8:14]=1
 torso=np.zeros_like(arm);torso[2:12,12:30]=1
 near,far=two_segment_arm_masks(arm,torso)
 ny=np.where(near)[0].mean();fy=np.where(far)[0].mean()
 assert ny<fy
def test_clothing_authority_unions_masks():
 t=np.zeros((10,10),bool);t[2:8,3:7]=1
 c=np.zeros_like(t);c[1:4,1:5]=1
 out=clothing_authority(t,c)
 assert np.array_equal(out,t|c)
