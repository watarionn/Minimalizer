from minimalizer_zerobase.refine.regions import RegionObservation, RegionGuardPolicy, regional_retention, regional_guard_passes, weighted_regional_loss
from minimalizer_zerobase.refine.sam_observer import SamObserver, SamUnavailable

def test_regional_retention_detects_local_collapse():
    ref=(RegionObservation("subject", .50), RegionObservation("hair", .20))
    cand=(RegionObservation("subject", .49), RegionObservation("hair", .10))
    r=regional_retention(ref,cand)
    assert r["subject"] == .98
    assert r["hair"] == .5
    assert not regional_guard_passes(r)

def test_low_confidence_reference_is_not_a_guard():
    policy=RegionGuardPolicy(min_confidence=.6)
    ref=(RegionObservation("hair", .2, .2),)
    cand=()
    assert regional_guard_passes(regional_retention(ref,cand,policy=policy),policy=policy)

def test_weighted_regional_loss_prioritizes_important_region():
    losses={"hair": .4, "background": .4}
    assert weighted_regional_loss(losses,{"hair": 3, "background": 1}) == .4
    assert weighted_regional_loss({"hair": .1, "background": .5},{"hair": 3,"background": 1}) < .5

def test_sam_adapter_is_read_only_and_optional():
    image={"pixels":[1,2,3]}
    before=list(image["pixels"])
    observer=SamObserver(lambda _: (RegionObservation("subject", .5),))
    assert observer.observe(image)[0].label == "subject"
    assert image["pixels"] == before
    try:
        SamObserver()
    except SamUnavailable:
        pass
    else:
        raise AssertionError("expected SamUnavailable")
