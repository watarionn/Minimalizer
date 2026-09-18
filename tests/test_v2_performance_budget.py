from minimalize_engine.v2 import (
    PERFORMANCE_BUDGET_SCHEMA_VERSION,
    PerformanceBudget,
    PerformanceMeasurement,
    evaluate_performance_budget,
)


def test_default_performance_budget_is_versioned_and_fixed():
    budget = PerformanceBudget()
    assert PERFORMANCE_BUDGET_SCHEMA_VERSION == "minimalizer-v2-performance-budget-v1"
    assert budget.case_count == 5
    assert budget.repeats == 2
    assert budget.confirmation_batches == 3
    assert budget.max_analysis_side == 400
    assert budget.web_workers == 1
    assert budget.max_concurrent_jobs == 2
    assert budget.mean_v2_seconds_max == 5.0
    assert budget.max_case_v2_seconds_max == 5.5
    assert budget.mean_case_ratio_max == 7.0
    assert budget.max_case_ratio_max == 9.0


def test_performance_budget_passes_only_when_every_latency_check_passes():
    measurement = PerformanceMeasurement(
        mean_legacy_seconds=0.75,
        mean_v2_seconds=4.6,
        max_case_v2_seconds=5.2,
        mean_case_ratio=6.4,
        max_case_ratio=8.2,
        case_count=5,
        repeats=2,
    )
    result = evaluate_performance_budget(measurement)
    assert result.passed is True
    assert all(dict(result.checks).values())


def test_performance_budget_fails_on_single_case_tail_even_if_mean_passes():
    measurement = PerformanceMeasurement(
        mean_legacy_seconds=0.75,
        mean_v2_seconds=4.7,
        max_case_v2_seconds=5.6,
        mean_case_ratio=6.5,
        max_case_ratio=8.0,
        case_count=5,
        repeats=2,
    )
    result = evaluate_performance_budget(measurement)
    checks = dict(result.checks)
    assert result.passed is False
    assert checks["mean_v2_seconds"] is True
    assert checks["max_case_v2_seconds"] is False


def test_v2_analysis_cap_is_explicit_and_preserves_uncapped_default(monkeypatch):
    from minimalize_engine.v2.pipeline import PipelineConfig
    import web.service as web_service

    assert PipelineConfig().analysis_max_side == 768
    calls = []

    def fake_minimalize_file_png(input_path, **kwargs):
        calls.append(kwargs.get("config"))
        return object()

    monkeypatch.setattr(web_service, "minimalize_file_png", fake_minimalize_file_png)
    web_service.minimalize_v2_path("ignored.png")
    web_service.minimalize_v2_path("ignored.png", analysis_max_side_cap=400)

    assert calls[0] is None
    assert calls[1] is not None
    assert calls[1].analysis_max_side == 400


def test_performance_budget_rejects_resource_envelope_increase():
    measurement = PerformanceMeasurement(
        mean_legacy_seconds=0.75,
        mean_v2_seconds=4.4,
        max_case_v2_seconds=4.8,
        mean_case_ratio=6.0,
        max_case_ratio=7.5,
        case_count=5,
        repeats=2,
        analysis_max_side=401,
        web_workers=1,
        max_concurrent_jobs=2,
    )
    result = evaluate_performance_budget(measurement)
    checks = dict(result.checks)
    assert result.passed is False
    assert checks["analysis_max_side"] is False
    assert checks["web_workers"] is True
    assert checks["max_concurrent_jobs"] is True
