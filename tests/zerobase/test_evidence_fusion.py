from minimalizer_zerobase.analyzers.contracts import Evidence, Provenance
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.scene.fusion import EvidenceFusion, FusionPolicy

SPACE = CoordinateSpace(width=100, height=100)
PROV_A = Provenance("adapter-a", "1")
PROV_B = Provenance("adapter-b", "1")

def ev(eid, bbox, *, label=None, confidence=None, provenance=PROV_A):
    return Evidence(eid, "region", SPACE, provenance, confidence=confidence,
                    semantic_label=label, geometry={"bbox": bbox})

def test_fusion_groups_overlapping_evidence_and_preserves_provenance_ids():
    scene = EvidenceFusion().fuse([
        ev("b", [11, 10, 20, 20], confidence=.7, provenance=PROV_B),
        ev("a", [10, 10, 20, 20], label="person", confidence=.9),
    ])
    assert len(scene.regions) == 1
    assert scene.regions[0].evidence_ids == ("a", "b")
    assert scene.regions[0].semantic_role == "person"
    assert scene.regions[0].confidence == .9
    assert scene.subjects[0].region_ids == ("region-0000",)

def test_fusion_is_replay_stable_and_input_order_independent():
    records = [ev("z", [60, 60, 10, 10]), ev("a", [10, 10, 20, 20], label="person")]
    fusion = EvidenceFusion()
    assert fusion.fuse(records).to_json() == fusion.fuse(reversed(records)).to_json()

def test_tie_break_prefers_producer_then_evidence_id_at_equal_confidence():
    records = [
        ev("z", [10, 10, 20, 20], label="hat", confidence=.8, provenance=PROV_B),
        ev("y", [10, 10, 20, 20], label="person", confidence=.8, provenance=PROV_A),
    ]
    scene = EvidenceFusion().fuse(records)
    assert scene.regions[0].semantic_role == "person"

def test_conflict_prefers_higher_confidence_semantic_label():
    scene = EvidenceFusion().fuse([
        ev("low", [10, 10, 20, 20], label="hat", confidence=.4),
        ev("high", [10, 10, 20, 20], label="person", confidence=.9),
    ])
    assert scene.regions[0].semantic_role == "person"

def test_rejects_duplicate_ids_and_coordinate_space_conflict():
    fusion = EvidenceFusion(FusionPolicy(overlap_threshold=.5))
    try:
        fusion.fuse([ev("same", [0, 0, 10, 10]), ev("same", [0, 0, 10, 10])])
        assert False, "duplicate id should fail"
    except ValueError as exc:
        assert "unique" in str(exc)
    other = CoordinateSpace(width=200, height=100)
    conflicting = Evidence("other", "region", other, PROV_A, geometry={"bbox":[0,0,10,10]})
    try:
        fusion.fuse([ev("base", [0,0,10,10]), conflicting])
        assert False, "coordinate conflict should fail"
    except ValueError as exc:
        assert "coordinate space" in str(exc)

def test_nonmerged_regions_emit_deterministic_overlap_relation():
    fusion = EvidenceFusion(FusionPolicy(overlap_threshold=.8))
    scene = fusion.fuse([
        ev("left", [10, 10, 20, 20]),
        ev("right", [20, 10, 20, 20]),
    ])
    assert len(scene.regions) == 2
    assert scene.relations[0].kind == "overlaps"
    assert scene.relations[0].source_id == "region-0000"
    assert scene.relations[0].target_id == "region-0001"
    assert scene.relations[0].confidence == .5

def test_real_baseline_adapter_evidence_can_fuse_without_adapter_types():
    import numpy as np
    from minimalizer_zerobase.analyzers.slic_regions import SLICRegionAdapter
    image = np.zeros((20, 20, 3), dtype=np.uint8)
    evidence = SLICRegionAdapter(n_segments=4).analyze(image, CoordinateSpace(20, 20))
    scene = EvidenceFusion().fuse(evidence)
    assert scene.regions
    assert all(region.evidence_ids for region in scene.regions)
    assert scene.producer == "EvidenceFusion"
