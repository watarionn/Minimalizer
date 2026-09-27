import json
from pathlib import Path
from minimalizer_zerobase.evaluation.quality_gate import FinalQualityGate
from minimalizer_zerobase.production import ProductionPipeline
from test_production_pipeline import evidence

ROOT = Path(__file__).parents[2]
MANIFEST = ROOT / "docs" / "zerobase" / "approved78_manifest.json"

def capture(tmp_path):
    root = tmp_path / "capture"
    pipeline = ProductionPipeline()
    original = pipeline.run(evidence(), root)
    replay = pipeline.replay(root)
    return root, original, replay

def test_final_gate_foundation_passes_but_migration_fails_closed_without_approved78(tmp_path):
    root, original, replay = capture(tmp_path)
    result = FinalQualityGate().evaluate(
        repo_root=ROOT, artifact_root=root, approved78_manifest=MANIFEST,
        production_boundary_clean=True,
        renderer_deterministic=original.svg == replay.svg,
        replay_deterministic=original.vector_scene.to_json() == replay.vector_scene.to_json(),
        notices_present=True,
    )
    assert result.foundation_ready is True
    assert result.migration_ready is False
    assert result.approved78_replayable_cases == 0

def test_missing_stage_artifact_fails_release_critical_gate(tmp_path):
    root, original, replay = capture(tmp_path)
    (root / "07_optimization.json").unlink()
    result = FinalQualityGate().evaluate(
        repo_root=ROOT, artifact_root=root, approved78_manifest=MANIFEST,
        production_boundary_clean=True, renderer_deterministic=True,
        replay_deterministic=True, notices_present=True,
    )
    assert result.foundation_ready is False
    assert result.migration_ready is False

def test_missing_notice_fails_foundation_gate(tmp_path):
    root, original, replay = capture(tmp_path)
    result = FinalQualityGate().evaluate(
        repo_root=ROOT, artifact_root=root, approved78_manifest=MANIFEST,
        production_boundary_clean=True, renderer_deterministic=True,
        replay_deterministic=True, notices_present=False,
    )
    assert result.foundation_ready is False

def test_result_serialization_is_deterministic(tmp_path):
    root, original, replay = capture(tmp_path)
    kwargs = dict(repo_root=ROOT, artifact_root=root, approved78_manifest=MANIFEST,
                  production_boundary_clean=True, renderer_deterministic=True,
                  replay_deterministic=True, notices_present=True)
    gate = FinalQualityGate()
    assert gate.evaluate(**kwargs).to_json() == gate.evaluate(**kwargs).to_json()
