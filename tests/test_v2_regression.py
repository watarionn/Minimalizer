from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import numpy as np
import pytest

from minimalize_engine.v2.pipeline import PipelineConfig, minimalize_v2
from minimalize_engine.v2.regression import (
    RegressionConfig,
    VISUAL_REGRESSION_CORPUS_V1,
    algorithm_digest,
    check_debug_observational,
    check_determinism,
    run_regression_case,
    validate_invariants,
    validate_visual_regression_corpus,
)


def _image() -> np.ndarray:
    image = np.zeros((48, 48, 3), dtype=np.uint8)
    image[:, :24] = (230, 80, 90)
    image[:, 24:] = (50, 90, 210)
    image[12:36, 18:30] = (245, 220, 70)
    return image


def test_visual_regression_corpus_contract_is_exact():
    assert len(VISUAL_REGRESSION_CORPUS_V1) == 18
    cases = {name: Path(f"{name}.png") for name in VISUAL_REGRESSION_CORPUS_V1}
    validate_visual_regression_corpus(cases)
    bad = dict(cases)
    bad.pop(VISUAL_REGRESSION_CORPUS_V1[0])
    with pytest.raises(ValueError):
        validate_visual_regression_corpus(bad)


def test_pipeline_config_is_json_serializable():
    payload = json.dumps(asdict(PipelineConfig()), sort_keys=True)
    assert '"region_merge"' in payload
    assert '"detail_budget"' in payload


def test_algorithm_digest_and_determinism_are_stable():
    image = _image()
    first = minimalize_v2(image, presets=("minimal",))
    second = minimalize_v2(image, presets=("minimal",))
    assert algorithm_digest(first, "minimal") == algorithm_digest(second, "minimal")
    assert check_determinism(image, preset="minimal")


def test_regression_case_writes_manifest_metrics_and_debug(tmp_path):
    result = run_regression_case(
        _image(),
        regression_config=RegressionConfig(artifact_level="summary"),
        output_dir=tmp_path,
        code_revision="test-revision",
    )
    assert result.manifest.code_revision == "test-revision"
    assert result.manifest.preset == "minimal"
    assert not result.invariant_failures
    assert result.metrics.runtime_seconds >= 0.0
    for name in ("manifest", "metrics", "invariants", "summary", "decision_log"):
        assert name in result.debug_artifacts
        assert Path(result.debug_artifacts[name]).exists()


def test_debug_on_off_is_observational_only(tmp_path):
    assert check_debug_observational(
        _image(), preset="minimal", output_dir=tmp_path
    )
    assert (tmp_path / "final.png").exists()
    assert (tmp_path / "decision_log.json").exists()


def test_hard_invariants_pass_for_synthetic_pipeline():
    result = minimalize_v2(_image(), presets=("minimal",))
    checks = validate_invariants(result, preset="minimal", config=PipelineConfig())
    failures = [item for item in checks if not item.passed]
    assert failures == []


def test_global_invariant_contract_names_are_covered():
    result = minimalize_v2(_image(), presets=("minimal",))
    names = {item.name for item in validate_invariants(
        result, preset="minimal", config=PipelineConfig()
    )}
    required = {
        "initial_labels_immutable_contract", "region_ids_never_reused",
        "region_adjacency_symmetric", "edge_keys_canonical",
        "region_graph_has_no_self_edges", "region_stats_finite",
        "region_colors_from_analysis_lab", "structural_lab_not_used_as_final_color",
        "shared_contour_boundaries_agree", "contours_have_no_self_intersection",
        "contour_preserves_region_count", "primitive_fitting_preserves_region_count",
        "critical_neighbor_leakage_guard", "every_region_has_palette_assignment",
        "detail_budget_has_no_core_coverage_holes", "preset_hierarchy_nested",
    }
    assert required <= names
