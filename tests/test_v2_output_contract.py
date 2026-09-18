import inspect

from app.cli import build_parser
import web.app as web_app
from minimalize_engine.v2 import (
    OUTPUT_FORMAT_SCHEMA_VERSION,
    build_output_format_compatibility,
)


def test_output_format_contract_is_complete_and_preserves_defaults():
    report = build_output_format_compatibility()
    payload = report.to_dict()
    assert payload["schema_version"] == OUTPUT_FORMAT_SCHEMA_VERSION
    assert payload["preserves_current_default"] is True
    actual = {
        (item.surface, item.output_format): item.route_on_v2_default
        for item in report.policies
    }
    assert actual == {
        ("web", "png"): "v2",
        ("web", "svg"): "legacy",
        ("cli", "png"): "v2",
        ("cli", "svg"): "legacy",
        ("cli", "webp"): "legacy",
    }


def test_output_format_contract_matches_current_public_surfaces():
    web_params = inspect.signature(web_app.minimalize_image).parameters
    assert web_params["output_format"].default == "svg"

    actions = {action.dest: action for action in build_parser()._actions}
    assert "output" in actions
    assert "png" in actions
    assert "webp" in actions
    assert actions["output"].default == "minimalized.svg"

    report = build_output_format_compatibility()
    web_formats = {item.output_format for item in report.policies if item.surface == "web"}
    cli_formats = {item.output_format for item in report.policies if item.surface == "cli"}
    assert web_formats == {"svg", "png"}
    assert cli_formats == {"svg", "png", "webp"}
