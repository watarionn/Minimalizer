from copy import deepcopy
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.scene.models import Region, Scene, Subject
from minimalizer_zerobase.regions.reconstruction import ReconstructionPolicy, RegionReconstructor

SPACE = CoordinateSpace(100, 80)

def scene(*regions, subjects=()):
    return Scene(SPACE, "test", "1", subjects=subjects, regions=regions)

def region(rid, role, bbox, evidence=(), confidence=.5, **geometry):
    data = {"bbox": bbox, **geometry}
    return Region(rid, role, evidence, confidence=confidence, geometry=data)

def test_boundary_clips_to_canvas_and_drops_empty_regions():
    source = scene(
        region("a", "coat", [-5, 10, 20, 30], ("e1",)),
        region("b", "noise", [150, 10, 4, 4], ("e2",)),
    )
    out = RegionReconstructor().reconstruct(source)
    assert len(out.regions) == 1
    assert out.regions[0].geometry["bbox"] == [0.0, 10.0, 15.0, 30.0]
    assert out.regions[0].evidence_ids == ("e1",)

def test_components_split_is_deterministic_and_preserves_provenance():
    source = scene(region("r", "hair", [0, 0, 30, 10], ("z", "a"),
                          components=[[20, 0, 10, 10], [0, 0, 10, 10]]))
    recon = RegionReconstructor()
    first = recon.reconstruct(source)
    second = recon.reconstruct(source)
    assert first.to_json() == second.to_json()
    assert [r.geometry["bbox"] for r in first.regions] == [
        [0.0, 0.0, 10.0, 10.0], [20.0, 0.0, 10.0, 10.0]]
    assert all(r.evidence_ids == ("a", "z") for r in first.regions)

def test_same_semantic_overlap_merges_with_union_boundary():
    source = scene(
        region("a", "shirt", [10, 10, 20, 20], ("e1",), .6),
        region("b", "shirt", [15, 10, 20, 20], ("e2",), .9),
    )
    out = RegionReconstructor(ReconstructionPolicy(merge_overlap_threshold=.7)).reconstruct(source)
    assert len(out.regions) == 1
    merged = out.regions[0]
    assert merged.geometry["bbox"] == [10.0, 10.0, 25.0, 20.0]
    assert merged.evidence_ids == ("e1", "e2")
    assert merged.confidence == .9

def test_different_semantics_do_not_merge():
    source = scene(
        region("a", "skin", [10, 10, 20, 20]),
        region("b", "hair", [10, 10, 20, 20]),
    )
    assert len(RegionReconstructor().reconstruct(source).regions) == 2

def test_source_scene_is_not_mutated_and_subject_refs_are_remapped():
    source = scene(
        region("a", "person", [10, 10, 20, 20], ("e1",)),
        region("b", "person", [11, 10, 20, 20], ("e2",)),
        subjects=(Subject("s", "person", ("a", "b"), confidence=.8),),
    )
    before = deepcopy(source.to_dict())
    out = RegionReconstructor().reconstruct(source)
    assert source.to_dict() == before
    assert out.subjects[0].region_ids == ("region-0000",)
    assert out.provenance["region_reconstruction"]["source_region_ids"] == ["a", "b"]

def test_input_region_order_does_not_change_reconstruction():
    a = region("a", "coat", [10, 10, 20, 20], ("e1",))
    b = region("b", "coat", [11, 10, 20, 20], ("e2",))
    recon = RegionReconstructor()
    assert recon.reconstruct(scene(a, b)).to_json() == recon.reconstruct(scene(b, a)).to_json()

def test_real_slic_fusion_scene_reconstructs_without_analyzer_types():
    import numpy as np
    from minimalizer_zerobase.analyzers.slic_regions import SLICRegionAdapter
    from minimalizer_zerobase.scene.fusion import EvidenceFusion
    image = np.zeros((24, 24, 3), dtype=np.uint8)
    evidence = SLICRegionAdapter(n_segments=4).analyze(image, CoordinateSpace(24, 24))
    fused = EvidenceFusion().fuse(evidence)
    rebuilt = RegionReconstructor().reconstruct(fused)
    assert rebuilt.regions
    assert rebuilt.producer == "RegionReconstructor"
    assert all(r.evidence_ids for r in rebuilt.regions)
    assert "region_reconstruction" in rebuilt.provenance
