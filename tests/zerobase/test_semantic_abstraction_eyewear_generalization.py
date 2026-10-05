import pytest
from minimalizer_zerobase.semantic_abstraction.eyewear_generalization import *
H="a"*64
def test_multi_holdout_pass_requires_worst_case_margin():
 r=evaluate_contrastive_holdouts((HoldoutScore(H,"positive",.20),HoldoutScore(H,"positive",.15),HoldoutScore(H,"negative",.02),HoldoutScore(H,"negative",-.1)))
 assert r.passed and r.margin==pytest.approx(.13)
def test_multi_holdout_fails_on_worst_negative():
 r=evaluate_contrastive_holdouts((HoldoutScore(H,"positive",.10),HoldoutScore(H,"positive",.08),HoldoutScore(H,"negative",.04),HoldoutScore(H,"negative",.07)))
 assert not r.passed and r.margin==pytest.approx(.01)
def test_requires_two_per_role():
 with pytest.raises(ValueError):evaluate_contrastive_holdouts((HoldoutScore(H,"positive",1),HoldoutScore(H,"negative",0)))
def test_requires_hash():
 with pytest.raises(ValueError):evaluate_contrastive_holdouts((HoldoutScore("x","positive",1),HoldoutScore(H,"positive",1),HoldoutScore(H,"negative",0),HoldoutScore(H,"negative",0)))
