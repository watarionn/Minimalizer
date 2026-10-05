import numpy as np
from minimalizer_zerobase.production.feature_survival_gate import extract_feature_signatures,feature_survival_report
def img():
 a=np.full((40,40,3),240,np.uint8);a[5:35,8:32]=(40,50,70);a[14:28,17:23]=(150,190,10);return a
def test_signature_is_deterministic():
 a=img();assert extract_feature_signatures(a)==extract_feature_signatures(a.copy())
def test_survival_passes_same_features():
 a=img();r=feature_survival_report(a,a.copy());assert r.pass_gate and not r.missing
def test_missing_compact_contrast_feature_fails():
 a=img();b=a.copy();b[14:28,17:23]=(40,50,70);r=feature_survival_report(a,b);assert not r.pass_gate;assert r.missing
def test_small_noise_is_ignored():
 a=img();b=a.copy();b[0,0]=(255,0,255);assert feature_survival_report(a,b).pass_gate
def test_position_shift_can_be_regression():
 a=img();b=np.full_like(a,240);b[5:35,8:32]=(40,50,70);b[1:15,1:7]=(150,190,10);assert not feature_survival_report(a,b,match_threshold=.10).pass_gate
