from pathlib import Path

def test_sa1030_runner_is_real_input_bound():
    text = Path("tools/run_sa1030_real_gc001_benchmark.py").read_text(encoding="utf-8")
    assert "simplify_composed_scene" in text
    assert "build_source_constraints_from_files" in text
    assert "production_promotion" in text
    assert "phase11_stage_sha256" in text
