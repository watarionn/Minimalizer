import json
from copy import deepcopy
import pytest
from minimalizer_zerobase.analyzers.contracts import Evidence, Provenance
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.production import ProductionPipeline, ProductionPipelinePolicy

SPACE = CoordinateSpace(100, 100)
PROV = Provenance("test-baseline", "1")

def evidence():
    return [
        Evidence("e-face", "region", SPACE, PROV, .9, "face",
                 {"bbox":[10,10,30,30]}, {"base_color":[240,190,160]}),
        Evidence("e-shirt", "region", SPACE, PROV, .9, "shirt",
                 {"bbox":[10,50,50,35]}, {"base_color":[30,80,180]}),
    ]

def test_no_network_baseline_pipeline_is_deterministic_and_immutable(tmp_path):
    records = evidence()
    before = deepcopy([x.to_dict() for x in records])
    pipeline = ProductionPipeline()
    first = pipeline.run(records, tmp_path / "a")
    second = pipeline.run(reversed(records), tmp_path / "b")
    assert first.vector_scene.to_json() == second.vector_scene.to_json()
    assert [x.to_dict() for x in records] == before
    assert len(first.vector_scene.primitives) == 2
def test_stage_artifacts_and_replay_are_exact(tmp_path):
    root = tmp_path / "capture"
    pipeline = ProductionPipeline()
    original = pipeline.run(evidence(), root)
    expected = {
        "01_evidence.json", "02_fused_scene.json", "03_reconstructed_scene.json",
        "04_importance_scene.json", "05_palette_scene.json", "06_candidates.json",
        "07_optimization.json", "08_vector_scene.json", "09_vector_scene.svg", "manifest.json",
    }
    assert {x.name for x in root.iterdir()} == expected
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["producer"] == "ProductionPipeline"
    replayed = pipeline.replay(root)
    assert replayed.vector_scene.to_json() == original.vector_scene.to_json()
    assert replayed.optimization.to_json() == original.optimization.to_json()
    assert replayed.svg == original.svg
    assert (root / "09_vector_scene.svg").read_text(encoding="utf-8") == original.svg

def test_missing_material_evidence_fails_closed():
    record = Evidence("e", "region", SPACE, PROV, .8, "shirt", {"bbox":[0,0,20,20]})
    with pytest.raises(ValueError, match="base_color"):
        ProductionPipeline().run([record])

def test_explicit_fallback_is_deterministic_when_enabled():
    record = Evidence("e", "region", SPACE, PROV, .8, "shirt", {"bbox":[0,0,20,20]})
    pipeline = ProductionPipeline(ProductionPipelinePolicy(require_material_evidence=False))
    out = pipeline.run([record])
    assert out.vector_scene.primitives[0].fill_ref == "#808080"

def test_real_slic_baseline_can_feed_pipeline_without_network():
    import numpy as np
    from minimalizer_zerobase.analyzers.slic_regions import SLICRegionAdapter
    image = np.zeros((32, 32, 3), dtype=np.uint8)
    image[:, :16] = [220, 80, 60]
    image[:, 16:] = [30, 120, 210]
    records = SLICRegionAdapter(n_segments=4, compactness=10).analyze(image, CoordinateSpace(32, 32))
    assert all("base_color" in x.normalization for x in records)
    out = ProductionPipeline().run(records)
    assert out.vector_scene.primitives
    assert out.svg.startswith("<svg ")
