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


def test_production_v2_guidance_uses_ephemeral_worker_per_call(monkeypatch, tmp_path):
    import subprocess
    from pathlib import Path

    import numpy as np
    from PIL import Image
    import web.service as web_service

    source_path = tmp_path / "source.png"
    Image.new("RGB", (2, 2), (120, 80, 40)).save(source_path)

    calls = []

    def fake_run(command, **kwargs):
        calls.append((list(command), dict(kwargs)))
        output_path = Path(command[command.index("--output") + 1])
        Image.new("L", (2, 2), 128).save(output_path)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(web_service.subprocess, "run", fake_run)

    first = web_service._production_v2_guidance(source_path)
    second = web_service._production_v2_guidance(source_path)

    assert len(calls) == 2
    for command, kwargs in calls:
        assert command[:3] == [web_service.sys.executable, "-m", "web.rembg_worker"]
        assert command[command.index("--model") + 1] == "u2netp"
        assert kwargs["check"] is True
        assert kwargs["timeout"] == 120
    assert first.subject_provider == "rembg"
    assert first.subject_model == "u2netp"
    assert first.subject_prob.shape == (2, 2)
    assert np.allclose(first.subject_prob, 128 / 255.0)
    assert np.array_equal(first.subject_prob, second.subject_prob)
    assert not hasattr(web_service, "_REMBG_SESSION")


def test_production_v2_guidance_falls_back_to_none(monkeypatch, tmp_path):
    import subprocess

    from PIL import Image
    import web.service as web_service

    source_path = tmp_path / "source.png"
    Image.new("RGB", (2, 2), (120, 80, 40)).save(source_path)
    web_service._REMBG_FAILURE_LOGGED = False

    def fail_worker(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(web_service.subprocess, "run", fail_worker)
    assert web_service._production_v2_guidance(source_path) is None


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
