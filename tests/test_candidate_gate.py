from minimalizer_zerobase.refine.candidate_gate import evaluate_candidate
from minimalizer_zerobase.refine.combined_evidence import ObserverEvidence
from minimalizer_zerobase.refine.evaluation import ABMetrics,Decision

def m(obj,identity=.99,sil=.99): return ABMetrics(obj,identity,sil,deterministic=True)
def o(dino,hair=.8,face=.8,limb=.8,accessory=.8): return ObserverEvidence(dino,{"hair":hair,"face-skin":face,"limb":limb,"accessory":accessory})

def test_safe_objective_improvement_with_stable_observers_adopts():
    r=evaluate_candidate(m(1.0),m(.8),o(.6),o(.605))
    assert r.decision is Decision.ADOPT

def test_identity_guard_cannot_be_overridden_by_observers():
    r=evaluate_candidate(m(1.0),m(.8,identity=.9),o(.5),o(.9,.95,.95,.95,.95))
    assert r.decision is Decision.REJECT

def test_dino_regression_rejects_objective_win():
    r=evaluate_candidate(m(1.0),m(.8),o(.6),o(.4))
    assert r.decision is Decision.REJECT

def test_missing_dino_holds_not_adopts():
    r=evaluate_candidate(m(1.0),m(.8),ObserverEvidence(None,{"hair":.8}),ObserverEvidence(None,{"hair":.8}))
    assert r.decision is Decision.HOLD
