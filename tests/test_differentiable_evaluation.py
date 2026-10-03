from minimalizer_zerobase.refine.evaluation import ABMetrics,Decision,evaluate_ab

def m(**kw):
    d=dict(objective=1.0,identity_ratio=1.0,silhouette_ratio=1.0,regional_retention={"subject":1.0,"hair":1.0},regional_spatial_iou={"subject":1.0,"hair":1.0},deterministic=True)
    d.update(kw); return ABMetrics(**d)

def test_missing_real_observer_evidence_holds():
    assert evaluate_ab(m(),m(objective=.8,regional_retention=None)).decision is Decision.HOLD

def test_local_regression_rejects_even_when_objective_wins():
    r=evaluate_ab(m(),m(objective=.8,regional_retention={"subject":.99,"hair":.5}))
    assert r.decision is Decision.REJECT

def test_identity_regression_rejects():
    assert evaluate_ab(m(),m(objective=.8,identity_ratio=.8)).decision is Decision.REJECT

def test_complete_guarded_win_can_adopt():
    assert evaluate_ab(m(),m(objective=.8)).decision is Decision.ADOPT

def test_nondeterminism_rejects():
    assert evaluate_ab(m(),m(objective=.8,deterministic=False)).decision is Decision.REJECT

def test_equal_coverage_but_spatial_relocation_rejects():
    candidate=m(objective=.8)
    candidate=ABMetrics(**{**candidate.__dict__,"regional_spatial_iou":{"subject":.99,"hair":.2}})
    assert evaluate_ab(m(),candidate).decision is Decision.REJECT

def test_missing_spatial_evidence_holds():
    assert evaluate_ab(m(),m(objective=.8)).decision is Decision.HOLD

def test_complete_spatially_guarded_win_can_adopt():
    candidate=m(objective=.8)
    candidate=ABMetrics(**{**candidate.__dict__,"regional_spatial_iou":{"subject":.99,"hair":.91}})
    assert evaluate_ab(m(),candidate).decision is Decision.ADOPT
