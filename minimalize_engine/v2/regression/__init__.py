from .compare import algorithm_digest, compare_metrics
from .debug import build_decision_log, build_decision_summary, write_debug_artifacts
from .metrics import compute_regression_metrics
from .runner import (
    KNOWN_ISSUE_CASES,
    SMOKE_CORPUS_V1,
    VISUAL_REGRESSION_CORPUS_V1,
    build_manifest,
    check_debug_observational,
    check_determinism,
    config_hash,
    load_rgb_file,
    resolve_code_revision,
    run_regression_case,
    run_regression_files,
    run_visual_regression_corpus,
    validate_visual_regression_corpus,
    validate_invariants,
)
from .types import (
    InvariantCheck,
    MetricDelta,
    RegressionCaseResult,
    RegressionConfig,
    RegressionManifest,
    RegressionMetrics,
)

__all__ = [
    "KNOWN_ISSUE_CASES", "SMOKE_CORPUS_V1", "VISUAL_REGRESSION_CORPUS_V1",
    "InvariantCheck", "MetricDelta", "RegressionCaseResult", "RegressionConfig",
    "RegressionManifest", "RegressionMetrics", "algorithm_digest",
    "build_decision_log", "build_decision_summary", "build_manifest", "check_debug_observational", "check_determinism",
    "compare_metrics", "compute_regression_metrics", "config_hash",
    "load_rgb_file", "resolve_code_revision", "run_regression_case",
    "run_regression_files", "run_visual_regression_corpus", "validate_visual_regression_corpus",
    "validate_invariants", "write_debug_artifacts",
]
