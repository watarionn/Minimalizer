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
    observer=SamObserver(lambda _, _concepts: (RegionObservation("subject", .5),))
    assert observer.observe(image)[0].label == "subject"
    assert image["pixels"] == before
    try:
        SamObserver()
    except SamUnavailable:
        pass
    else:
        raise AssertionError("expected SamUnavailable")


def test_hair_damage_is_weighted_more_than_background_damage():
    hair=weighted_regional_loss({"hair":.5,"background":0.0},{"hair":4,"background":1})
    bg=weighted_regional_loss({"hair":0.0,"background":.5},{"hair":4,"background":1})
    assert hair > bg

def test_concept_alignment_is_fail_closed():
    observer=SamObserver(lambda _image,_concepts:(RegionObservation("subject",.5),))
    try: observer.observe({},("subject","hair"))
    except ValueError as exc: assert "align" in str(exc)
    else: raise AssertionError("expected ValueError")

def test_spatial_iou_detects_relocation_despite_equal_coverage():
    from minimalizer_zerobase.refine.regions import spatial_iou
    ref=RegionObservation("hair",.5,spatial_mask=((1,1,0,0),(1,1,0,0)))
    moved=RegionObservation("hair",.5,spatial_mask=((0,0,1,1),(0,0,1,1)))
    assert spatial_iou(ref,moved) == 0.0

def test_spatial_iou_identical_masks_pass():
    from minimalizer_zerobase.refine.regions import spatial_iou
    mask=((1,0),(1,1))
    assert spatial_iou(RegionObservation("hair",.75,spatial_mask=mask),RegionObservation("hair",.75,spatial_mask=mask)) == 1.0

def test_spatial_guard_fails_closed_when_mask_missing():
    from minimalizer_zerobase.refine.regions import regional_guard_passes
    assert not regional_guard_passes({"hair":1.0},spatial={"hair":None})
