import pytest
from minimalizer_zerobase.production.diffmin import (
 DIFFMIN_GUARDED,DiffMinEvidence,GuardedDiffMinSwitch,
)

def ev(**kw):
 d=dict(hard_guards_pass=True,silhouette_iou=.999,baseline_dino_score=.5,candidate_dino_score=.501);d.update(kw);return DiffMinEvidence(**d)

def test_diffmin_is_off_by_default(monkeypatch):
 monkeypatch.delenv("MINIMALIZER_DIFFMIN",raising=False)
 x=GuardedDiffMinSwitch().decide(ev());assert not x.apply_candidate and x.rollback_to_baseline and x.reason=="disabled-by-default"

@pytest.mark.parametrize("e,reason",[
 (ev(hard_guards_pass=False),"hard-guard-failed"),
 (ev(silhouette_iou=.98),"scene-silhouette-regressed"),
 (ev(candidate_dino_score=None),"observer-evidence-missing"),
 (ev(candidate_dino_score=.5),"observer-not-improved"),
 (ev(candidate_dino_score=.49),"observer-not-improved"),
])
def test_guarded_diffmin_fails_closed(e,reason):
 x=GuardedDiffMinSwitch(DIFFMIN_GUARDED).decide(e);assert not x.apply_candidate and x.rollback_to_baseline and x.reason==reason

def test_guarded_diffmin_applies_only_observer_positive_candidate():
 x=GuardedDiffMinSwitch(DIFFMIN_GUARDED).decide(ev());assert x.apply_candidate and not x.rollback_to_baseline

def test_unknown_diffmin_mode_fails_closed():
 with pytest.raises(ValueError,match="unsupported DiffMin mode"):GuardedDiffMinSwitch("always")

