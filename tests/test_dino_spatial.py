import numpy as np
import pytest
from minimalizer_zerobase.refine.dino_spatial import observation_from_feature_map,compare_dino_spatial

def test_identical_dense_features_score_one():
    x=np.arange(4*4*3,dtype=np.float32).reshape(4,4,3)+1
    s=compare_dino_spatial(observation_from_feature_map(x),observation_from_feature_map(x))
    assert s.score == pytest.approx(1.0)

def test_local_feature_damage_is_visible_even_when_global_mean_matches():
    a=np.zeros((4,4,2),dtype=np.float32); a[:2,:,0]=1; a[2:,:,1]=1
    b=a.copy(); b[:2]=b[:2,::-1]
    b[0,0]=[0,1]; b[0,1]=[1,0]
    s=compare_dino_spatial(observation_from_feature_map(a),observation_from_feature_map(b))
    assert s.aligned_patch_cosine < s.global_cosine

def test_spatial_relocation_is_penalized():
    a=np.zeros((4,4,2),dtype=np.float32); a[:2,:,0]=1; a[2:,:,1]=1
    b=np.flip(a,axis=0).copy()
    s=compare_dino_spatial(observation_from_feature_map(a),observation_from_feature_map(b))
    assert s.global_cosine == pytest.approx(1.0)
    assert s.aligned_patch_cosine < .1
    assert s.score < .6

def test_nonfinite_feature_map_fails_closed():
    x=np.zeros((2,2,2),dtype=np.float32); x[0,0,0]=np.nan
    with pytest.raises(ValueError,match="finite"):
        observation_from_feature_map(x)
