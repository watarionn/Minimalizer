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
    assert budget.max_concurrent_jobs == 1
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
    assert checks["max_concurrent_jobs"] is False


def test_production_v2_guidance_reuses_rembg_session(monkeypatch):
    import numpy as np
    import web.service as web_service

    web_service._REMBG_SESSION = None
    session = object()
    session_options = object()
    guidance = object()
    sessions = []
    builds = []

    monkeypatch.setattr(
        web_service,
        "create_rembg_session",
        lambda config, **kwargs: sessions.append((config.model, kwargs.get("sess_opts"))) or session,
    )
    monkeypatch.setattr(web_service, "_production_rembg_session_options", lambda: session_options)
    monkeypatch.setattr(
        web_service,
        "load_image",
        lambda path: np.zeros((2, 2, 3), dtype=np.uint8),
    )
    monkeypatch.setattr(
        web_service,
        "build_rembg_guidance",
        lambda source, *, config, session: builds.append((config.model, session)) or guidance,
    )

    assert web_service._production_v2_guidance("first.png") is guidance
    assert web_service._production_v2_guidance("second.png") is guidance
    assert sessions == [("u2netp", session_options)]
    assert builds == [("u2netp", session), ("u2netp", session)]


def test_production_v2_guidance_falls_back_to_none(monkeypatch):
    import web.service as web_service

    web_service._REMBG_SESSION = None
    web_service._REMBG_FAILURE_LOGGED = False

    monkeypatch.setattr(web_service, "_production_rembg_session_options", lambda: object())

    def fail_session(config, **kwargs):
        raise RuntimeError("rembg unavailable")

    monkeypatch.setattr(web_service, "create_rembg_session", fail_session)
    assert web_service._production_v2_guidance("ignored.png") is None


def test_minimalize_v2_path_passes_production_guidance(monkeypatch):
    import web.service as web_service

    guidance = object()
    captured = {}

    monkeypatch.setattr(web_service, "_production_v2_guidance", lambda path: guidance)

    def fake_minimalize_file_png(input_path, **kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(web_service, "minimalize_file_png", fake_minimalize_file_png)
    web_service.minimalize_v2_path("ignored.png")

    assert captured["guidance"] is guidance
