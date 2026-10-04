from minimalizer_zerobase.refine.combined_evidence import *

def ev(dino,**regions): return ObserverEvidence(dino,regions)

def test_both_observers_stable_allows_adoption_evidence():
    r=compare_observer_evidence(ev(.60,hair=.90,**{"face-skin":.84},limb=.39,accessory=.69),ev(.605,hair=.91,**{"face-skin":.85},limb=.40,accessory=.70))
    assert r.dino is EvidenceTrend.STABLE
    assert r.abstraction is EvidenceTrend.STABLE
    assert observer_evidence_allows_adoption(r)

def test_dino_regression_vetoes_even_if_sam_improves():
    r=compare_observer_evidence(ev(.60,hair=.70),ev(.50,hair=.90),critical_regions=("hair",))
    assert r.dino is EvidenceTrend.REGRESSED
    assert not observer_evidence_allows_adoption(r)

def test_named_region_regression_vetoes_even_if_dino_improves():
    r=compare_observer_evidence(ev(.50,hair=.90),ev(.60,hair=.70),critical_regions=("hair",))
    assert r.abstraction is EvidenceTrend.REGRESSED
    assert not observer_evidence_allows_adoption(r)

def test_missing_dino_holds_fail_closed():
    r=compare_observer_evidence(ev(None,hair=.9),ev(None,hair=.9),critical_regions=("hair",))
    assert r.dino is EvidenceTrend.UNAVAILABLE
    assert not observer_evidence_allows_adoption(r)

def test_missing_sam_region_does_not_fake_improvement():
    r=compare_observer_evidence(ev(.5,hair=.9),ObserverEvidence(.51,{}),critical_regions=("hair",))
    assert r.abstraction is EvidenceTrend.UNAVAILABLE
