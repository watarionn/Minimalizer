import numpy as np
from minimalizer_zerobase.refine.candidate_gate import evaluate_candidate
from minimalizer_zerobase.refine.combined_evidence import ObserverEvidence
from minimalizer_zerobase.refine.evaluation import ABMetrics,Decision
from minimalizer_zerobase.refine.semantic_ownership import evaluate_ownership_retention

def m(obj,identity=.99,sil=.99): return ABMetrics(obj,identity,sil,deterministic=True)
def o(dino,hair=.8,face=.8,limb=.8,accessory=.8): return ObserverEvidence(dino,{"hair":hair,"face-skin":face,"limb":limb,"accessory":accessory})
def own(ok=True):
    a=np.zeros((8,8),bool); a[2:6,2:6]=1
    b=a.copy() if ok else np.zeros_like(a)
    return evaluate_ownership_retention({"face":a},{"face":b},critical_parts=("face",))

def test_safe_objective_improvement_with_stable_observers_adopts():
    assert evaluate_candidate(m(1),m(.8),o(.6),o(.605),ownership=own()).decision is Decision.ADOPT
def test_identity_guard_cannot_be_overridden():
    assert evaluate_candidate(m(1),m(.8,identity=.9),o(.5),o(.9),ownership=own()).decision is Decision.REJECT
def test_dino_regression_rejects():
    assert evaluate_candidate(m(1),m(.8),o(.6),o(.4),ownership=own()).decision is Decision.REJECT
def test_missing_dino_holds():
    assert evaluate_candidate(m(1),m(.8),o(None),o(None),ownership=own()).decision is Decision.HOLD
def test_ownership_regression_rejects_even_if_dino_improves():
    assert evaluate_candidate(m(1),m(.8),o(.5),o(.8),ownership=own(False)).decision is Decision.REJECT
def test_missing_ownership_holds():
    assert evaluate_candidate(m(1),m(.8),o(.6),o(.61)).decision is Decision.HOLD
def test_sam_named_part_regression_is_diagnostic_not_veto():
    assert evaluate_candidate(m(1),m(.8),o(.6,face=.9),o(.605,face=.2),ownership=own()).decision is Decision.ADOPT
