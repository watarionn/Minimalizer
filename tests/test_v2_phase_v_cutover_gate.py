import json
from pathlib import Path

from minimalize_engine.v2 import build_browser_migration_contract, resolve_browser_route

ROOT = Path(__file__).resolve().parents[1]
RC_PATH = ROOT / "docs" / "architecture" / "MINIMALIZER_2_CALIBRATION_05_PHASE_U_RC.json"


def test_phase_v_requires_a_passing_phase_u_release_candidate():
    rc = json.loads(RC_PATH.read_text(encoding="utf-8"))
    assert rc["result"] == "pass"
    assert rc["cutover_performed"] is False
    assert rc["rollback_verified"] is True
    assert rc["ready_for_explicit_cutover_decision"] is True


def test_phase_v_cutover_keeps_the_verified_rollback_contract():
    contract = build_browser_migration_contract().to_dict()
    assert contract["current_state"] == "v2_standard_default"
    assert contract["rollback_target"] == "legacy_default"
    assert contract["rollback_requires_data_migration"] is False
    assert contract["automatic_error_fallback"] is False


def test_phase_v_default_candidate_preserves_compatibility_routing():
    base = dict(
        rollout_state="v2_standard_default",
        mode="standard",
        output_format="png",
    )
    assert resolve_browser_route(**base) == "v2"
    assert resolve_browser_route(**base, background_mode="source") == "legacy"
    assert resolve_browser_route(**base, source_has_transparency=True) == "legacy"
    assert resolve_browser_route(**base, ignore_source_alpha=True) == "legacy"
    assert resolve_browser_route(**(base | {"output_format": "svg"})) == "legacy"
    assert resolve_browser_route(**(base | {"mode": "rinka_reference"})) == "legacy"
    assert resolve_browser_route(**(base | {"mode": "color_strip"})) == "legacy"


def test_phase_v_browser_bundle_is_cut_over_to_v2_default():
    source = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
    assert 'const LOCAL_WORKER_BASE = "http://127.0.0.1:28765"' in source
    assert 'const LOCAL_WORKER_STORAGE_KEY = "minimalizer.localWorkerEnabled"' in source
    assert 'new URLSearchParams(window.location.search).get("localWorker")' in source
    assert "const LOCAL_WORKER_HEALTH_TIMEOUT_MS = 15000" in source
    assert "const probe = await probeLocalWorker()" in source
    assert '"Railway fallback"' in source
    assert "ローカルネットワークアクセスを許可してください" in source
    assert "await requestStandardV2()" in source
    assert 'fetch("/api/v2/minimalize"' in source
    assert 'form.append("preset", "minimal")' in source
