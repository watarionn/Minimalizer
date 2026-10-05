import numpy as np
from minimalizer_zerobase.semantic_abstraction.feature_local_eyewear import *

def test_contract_is_frozen():
 assert FEATURE_LOCAL_VERSION=="sa7.10-v1" and SIMILARITY_THRESHOLD==.72

def test_local_similarity_forms_bounded_component():
 f=np.zeros((4,4,3),np.float32);f[:,:,1]=1;p=np.array([1,0,0],np.float32);a=np.ones((4,4),bool)
 f[1,1]=p;f[1,2]=p
 r=feature_local_regions(f,authority_grid=a,prototype=p,output_shape=(40,40))
 assert len(r)==1 and r[0].mask.sum()==200 and r[0].observer_role=="feature_local"

def test_single_cell_noise_fails_closed():
 f=np.zeros((4,4,2),np.float32);f[:,:,1]=1;p=np.array([1,0],np.float32);a=np.ones((4,4),bool);f[1,1]=p
 assert feature_local_regions(f,authority_grid=a,prototype=p,output_shape=(40,40))==()

def test_oversized_component_fails_closed():
 f=np.zeros((4,4,2),np.float32);p=np.array([1,0],np.float32);f[:]=p;a=np.ones((4,4),bool)
 assert feature_local_regions(f,authority_grid=a,prototype=p,output_shape=(40,40))==()

def test_outside_authority_is_not_evidence():
 f=np.zeros((4,4,2),np.float32);f[:,:,1]=1;p=np.array([1,0],np.float32);a=np.zeros((4,4),bool);f[1,1]=p;f[1,2]=p
 assert feature_local_regions(f,authority_grid=a,prototype=p,output_shape=(40,40))==()

def test_deterministic():
 f=np.zeros((4,4,2),np.float32);f[:,:,1]=1;p=np.array([1,0],np.float32);a=np.ones((4,4),bool);f[2,1]=p;f[2,2]=p
 x=feature_local_regions(f,authority_grid=a,prototype=p,output_shape=(40,40));y=feature_local_regions(f,authority_grid=a,prototype=p,output_shape=(40,40))
 assert [(z.evidence_id,z.confidence,z.mask.tobytes()) for z in x]==[(z.evidence_id,z.confidence,z.mask.tobytes()) for z in y]

def test_contrast_window_threshold_is_frozen_from_non_target_holdout():
 assert np.isclose(CONTRAST_WINDOW_THRESHOLD,-0.0118829645)

def test_contrast_windows_emit_only_passing_bounded_regions():
 r=contrast_window_evidence(np.array([.03,-.06]),((10,10,30,20),(40,10,60,20)),output_shape=(80,80))
 assert len(r)==1 and r[0].mask[10:20,10:30].all() and r[0].observer_role=="feature_local"
