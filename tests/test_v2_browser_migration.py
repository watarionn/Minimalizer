from pathlib import Path

from minimalize_engine.v2 import (
    BROWSER_MIGRATION_SCHEMA_VERSION,
    build_browser_migration_contract,
    resolve_browser_route,
)

ROOT = Path(__file__).resolve().parents[1]


def test_browser_migration_contract_is_explicit_and_rollback_safe():
    report = build_browser_migration_contract()
    payload = report.to_dict()
    assert payload["schema_version"] == BROWSER_MIGRATION_SCHEMA_VERSION
    assert payload["current_state"] == "v2_standard_default"
    assert payload["legacy_endpoint"] == "/api/minimalize"
    assert payload["v2_endpoint"] == "/api/v2/minimalize"
    assert payload["specialized_modes"] == ["rinka_reference", "color_strip"]
    assert payload["rollback_target"] == "legacy_default"
    assert payload["rollback_requires_data_migration"] is False
    assert payload["automatic_error_fallback"] is False
    assert [item["state"] for item in payload["stages"]] == [
        "legacy_default", "v2_standard_opt_in", "v2_standard_default"
    ]


def test_browser_route_respects_rollout_and_specialized_modes():
    for mode in ("rinka_reference", "color_strip"):
        assert resolve_browser_route(
            rollout_state="v2_standard_default",
            mode=mode,
            output_format="png",
        ) == "legacy"
    assert resolve_browser_route(
        rollout_state="legacy_default",
        mode="standard",
        output_format="png",
    ) == "legacy"
    assert resolve_browser_route(
        rollout_state="v2_standard_opt_in",
        mode="standard",
        output_format="png",
        user_selected_v2=False,
    ) == "legacy"
    assert resolve_browser_route(
        rollout_state="v2_standard_opt_in",
        mode="standard",
        output_format="png",
        user_selected_v2=True,
    ) == "v2"


def test_browser_route_composes_output_and_alpha_contracts():
    base = dict(
        rollout_state="v2_standard_default",
        mode="standard",
    )
    assert resolve_browser_route(**base, output_format="png") == "v2"
    assert resolve_browser_route(**base, output_format="svg") == "legacy"
    assert resolve_browser_route(
        **base, output_format="png", background_mode="transparent"
    ) == "legacy"
    assert resolve_browser_route(
        **base, output_format="png", source_has_transparency=True
    ) == "legacy"
    assert resolve_browser_route(
        **base, output_format="png", ignore_source_alpha=True
    ) == "legacy"


def test_current_browser_bundle_routes_canonical_minimalization_to_v2():
    source = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
    assert 'const LOCAL_WORKER_BASE = "http://127.0.0.1:28765"' in source
    assert "await requestStandardV2()" in source
    assert 'fetch("/api/v2/minimalize"' in source
    assert 'form.append("preset", "minimal")' in source
    assert 'form.append("include_facets", "true")' in source
