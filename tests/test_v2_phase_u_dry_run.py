from minimalize_engine.v2 import resolve_browser_route


def _route(**overrides):
    request = dict(
        rollout_state="v2_standard_opt_in",
        mode="standard",
        output_format="png",
        background_mode="white",
        source_has_transparency=False,
        ignore_source_alpha=False,
        user_selected_v2=True,
    )
    request.update(overrides)
    return resolve_browser_route(**request)


def test_phase_u_opt_in_dry_run_routes_only_eligible_standard_png_to_v2():
    assert _route() == "v2"
    assert _route(user_selected_v2=False) == "legacy"
    assert _route(output_format="svg") == "legacy"
    assert _route(background_mode="transparent") == "legacy"
    assert _route(background_mode="source") == "legacy"
    assert _route(source_has_transparency=True) == "legacy"
    assert _route(ignore_source_alpha=True) == "legacy"


def test_phase_u_specialized_modes_remain_legacy_even_when_v2_is_selected():
    assert _route(mode="rinka_reference") == "legacy"
    assert _route(mode="color_strip") == "legacy"


def test_phase_u_rollback_returns_every_browser_request_to_legacy():
    cases = (
        {},
        {"output_format": "svg"},
        {"background_mode": "transparent"},
        {"source_has_transparency": True},
        {"mode": "rinka_reference"},
        {"mode": "color_strip"},
    )
    for case in cases:
        assert _route(rollout_state="legacy_default", **case) == "legacy"
