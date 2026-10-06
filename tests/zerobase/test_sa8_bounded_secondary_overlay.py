import numpy as np

from minimalizer_zerobase.production.bounded_secondary_overlay import propose_bounded_secondary_overlays


def _fixture():
    image=np.zeros((40,40,3),dtype=np.uint8)
    mask=np.zeros((40,40),dtype=bool)
    for y,x in ((2,2),(2,26),(26,2),(26,26)):
        mask[y:y+10,x:x+10]=True
        image[y:y+10,x:x+10]=[180,60,30]
    return image,mask


def test_established_coverage_is_not_replaced():
    image,mask=_fixture()
    established=np.zeros_like(mask);established[2:12,2:12]=True
    out=propose_bounded_secondary_overlays(image,mask,"hair",(established,),palette_role_budget=1,overlay_budget=4)
    assert out
    assert all(not np.any(item.uncovered_mask & established) for item in out)
    assert np.all(np.logical_or.reduce([item.uncovered_mask for item in out]) <= mask)


def test_only_positive_coverage_gain_is_selected():
    image,mask=_fixture()
    out=propose_bounded_secondary_overlays(image,mask,"hair",(mask.copy(),),palette_role_budget=1)
    assert out==()


def test_overlay_budget_is_hard():
    image,mask=_fixture()
    out=propose_bounded_secondary_overlays(image,mask,"hair",(),palette_role_budget=1,overlay_budget=2)
    assert len(out)==2


def test_minimum_gain_filters_small_secondary_fields():
    image,mask=_fixture()
    established=mask.copy();established[26:36,26:36]=False
    out=propose_bounded_secondary_overlays(
        image,mask,"hair",(established,),palette_role_budget=1,overlay_budget=2,min_coverage_gain_ratio=.30
    )
    assert out==()


def test_selection_is_deterministic():
    image,mask=_fixture()
    a=propose_bounded_secondary_overlays(image,mask,"hair",(),palette_role_budget=1,overlay_budget=3)
    b=propose_bounded_secondary_overlays(image,mask,"hair",(),palette_role_budget=1,overlay_budget=3)
    assert [(x.candidate.component_id,x.coverage_gain_pixels) for x in a]==[(x.candidate.component_id,x.coverage_gain_pixels) for x in b]


def test_zero_overlay_budget_fails_closed():
    image,mask=_fixture()
    assert propose_bounded_secondary_overlays(image,mask,"hair",(),overlay_budget=0)==()
