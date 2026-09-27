from copy import deepcopy
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.importance import ImportanceEngine, ImportancePolicy
from minimalizer_zerobase.scene.models import Region, Scene, Subject

SPACE = CoordinateSpace(100, 100)

def region(rid, role, bbox, confidence=.5):
    return Region(rid, role, confidence=confidence, geometry={"bbox": bbox})

def scene(*regions, subjects=()):
    return Scene(SPACE, "test", "1", regions=regions, subjects=subjects)

def test_decisions_are_inspectable_and_deterministic():
    source = scene(region("hair", "hair", [0, 0, 50, 50], .9),
                   region("noise", "noise", [0, 0, 2, 2], .2))
    engine = ImportanceEngine()
    a = engine.evaluate(source)
    b = engine.evaluate(scene(*reversed(source.regions)))
    assert a == b
    assert a[0].region_id == "hair"
    assert a[0].semantic == .9
    assert a[0].spatial_mass == 1.0
    assert a[0].rationale == ("semantic", "spatial_mass", "confidence")

def test_subject_membership_and_identity_accent_are_explicit_dimensions():
    accent = region("a", "identity_accent", [0, 0, 5, 5], .4)
    subject = Subject("s", "person", ("a",))
    decision = ImportanceEngine().evaluate(scene(accent, subjects=(subject,)))[0]
    assert decision.subject == 1.0
    assert decision.identity_accent == 1.0
    assert "identity_accent" in decision.rationale

def test_apply_updates_importance_without_mutating_source():
    source = scene(region("coat", "coat", [0, 0, 60, 60], .8),
                   subjects=(Subject("s", "person", ("coat",)),))
    before = deepcopy(source.to_dict())
    out = ImportanceEngine().apply(source)
    assert source.to_dict() == before
    assert out.regions[0].importance > 0
    assert out.subjects[0].importance == out.regions[0].importance
    assert out.producer == "ImportanceEngine"
    assert out.provenance["importance"]["decisions"][0]["region_id"] == "coat"

def test_policy_override_and_threshold_validation():
    policy = ImportancePolicy(semantic_weights={"background": 1.0},
                              preserve_threshold=.4, protect_threshold=.6)
    decision = ImportanceEngine(policy).evaluate(scene(region("b", "background", [0, 0, 80, 80], 1)))[0]
    assert decision.semantic == 1.0
    assert decision.tier in {"preserve", "protect"}

def test_unknown_semantic_is_neutral_not_silently_discarded():
    decision = ImportanceEngine().evaluate(scene(region("x", "novel_part", [0, 0, 10, 10], .5)))[0]
    assert decision.semantic == .5

def test_real_reconstructed_scene_can_be_scored_without_analyzer_types():
    import numpy as np
    from minimalizer_zerobase.analyzers.slic_regions import SLICRegionAdapter
    from minimalizer_zerobase.scene.fusion import EvidenceFusion
    from minimalizer_zerobase.regions.reconstruction import RegionReconstructor
    image = np.zeros((24, 24, 3), dtype=np.uint8)
    evidence = SLICRegionAdapter(n_segments=4).analyze(image, CoordinateSpace(24, 24))
    reconstructed = RegionReconstructor().reconstruct(EvidenceFusion().fuse(evidence))
    out = ImportanceEngine().apply(reconstructed)
    assert out.regions
    assert all(0 <= r.importance <= 1 for r in out.regions)
    assert "importance" in out.provenance
