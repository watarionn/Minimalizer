from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path

import numpy as np

from minimalize_engine.v2 import PipelineConfig, minimalize_v2
from minimalize_engine.v2.regression import (
    KNOWN_ISSUE_CASES,
    SMOKE_CORPUS_V1,
    VISUAL_REGRESSION_CORPUS_V1,
    RegressionConfig,
    check_determinism,
    config_hash,
    run_regression_case,
)


def _synthetic_image(height: int = 32, width: int = 40) -> np.ndarray:
    image = np.full((height, width, 3), 238, dtype=np.uint8)
    image[:, : width // 2] = (218, 72, 92)
    image[: height // 2, width // 2 :] = (62, 96, 212)
    image[height // 2 :, width // 2 :] = (228, 190, 62)
    image[8:24, 13:27] = (72, 170, 118)
    return image


def test_pipeline_config_is_json_serializable_and_hash_stable():
    config = PipelineConfig()
    json.dumps(asdict(config), sort_keys=True)
    assert config_hash(config) == config_hash(config)


def test_canonical_corpus_constants_are_complete():
    assert len(VISUAL_REGRESSION_CORPUS_V1) == 18
    assert len(set(VISUAL_REGRESSION_CORPUS_V1)) == 18
    assert set(SMOKE_CORPUS_V1) <= set(VISUAL_REGRESSION_CORPUS_V1)
    assert len(KNOWN_ISSUE_CASES) == 5


def test_minimalize_v2_builds_shared_nested_hierarchy():
    image = _synthetic_image()
    result = minimalize_v2(
        image,
        presets=("minimal", "ultra_minimal"),
        config=PipelineConfig(),
    )
    assert set(result.presets) == {"minimal", "ultra_minimal"}
    family = result.cut_family
    assert family.detailed.region_count >= family.balanced.region_count
    assert family.balanced.region_count >= family.minimal.region_count
    assert family.minimal.region_count >= family.ultra_minimal.region_count
    for preset, pipeline in result.presets.items():
        assert pipeline.preset == preset
        assert len(pipeline.scene.shapes) == len(pipeline.selection.region_ids)
        assert pipeline.detail_budget.metrics.draw_geometry_count == len(
            pipeline.selection.region_ids
        )


def test_regression_case_records_manifest_metrics_and_invariants(tmp_path: Path):
    image = _synthetic_image()
    config = RegressionConfig(artifact_level="summary", main_preset="minimal")
    result = run_regression_case(
        image,
        regression_config=config,
        output_dir=tmp_path,
        code_revision="test-revision",
    )
    assert result.manifest.code_revision == "test-revision"
    assert result.manifest.preset == "minimal"
    assert result.manifest.config_hash
    assert result.metrics.initial_region_count >= result.metrics.selected_region_count
    assert result.metrics.runtime_seconds >= 0.0
    assert "preprocessing" in result.metrics.phase_timings
    assert result.invariant_failures == ()
    assert Path(result.debug_artifacts["manifest"]).exists()
    assert Path(result.debug_artifacts["metrics"]).exists()
    assert Path(result.debug_artifacts["summary"]).exists()


def test_standard_debug_is_observational_and_writes_stage_views(tmp_path: Path):
    image = _synthetic_image(28, 36)
    result = run_regression_case(
        image,
        regression_config=RegressionConfig(
            artifact_level="standard", main_preset="minimal"
        ),
        output_dir=tmp_path,
        code_revision="test-revision",
    )
    assert result.invariant_failures == ()
    expected = {
        "Source", "Analysis", "Structural", "Raw Edge", "Structural Edge",
        "Superpixels", "RAG", "Merge Hierarchy", "Hierarchy Cut",
        "Merged Regions", "Contour", "Primitive", "Palette", "Budget", "Final",
    }
    assert expected <= set(result.debug_artifacts)
    for name in expected:
        assert Path(result.debug_artifacts[name]).exists()


def test_same_input_and_config_are_deterministic():
    assert check_determinism(
        _synthetic_image(24, 32),
        pipeline_config=PipelineConfig(),
        preset="minimal",
    )


def test_pipeline_rejects_duplicate_or_unknown_presets():
    image = _synthetic_image(20, 24)
    try:
        minimalize_v2(image, presets=("minimal", "minimal"))
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("duplicate presets must fail")
    try:
        minimalize_v2(image, presets=("mystery",))
    except ValueError as exc:
        assert "unknown" in str(exc)
    else:
        raise AssertionError("unknown preset must fail")
