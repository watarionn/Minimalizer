from __future__ import annotations

import inspect
import json

from app.cli import build_parser
import web.app as web_app
from minimalize_engine.v2 import (
    MIGRATION_SCHEMA_VERSION,
    build_migration_readiness,
)


def test_migration_readiness_is_machine_readable_and_blocked():
    report = build_migration_readiness()
    payload = report.to_dict()
    assert payload["schema_version"] == MIGRATION_SCHEMA_VERSION
    assert payload["scope"] == "legacy_standard_default_to_v2"
    assert payload["ready_for_default"] is False
    assert payload["blocker_count"] == 6
    assert payload["blocker_ids"] == [
        "web_control_mapping",
        "output_format_parity",
        "alpha_background_parity",
        "cli_control_mapping",
        "browser_ui_migration",
        "performance_budget",
    ]
    json.dumps(payload, sort_keys=True)


def test_migration_report_matches_exposed_entry_point_surfaces():
    legacy_web = set(inspect.signature(web_app.minimalize_image).parameters)
    v2_web = set(inspect.signature(web_app.minimalize_image_v2).parameters)
    assert {"level", "output_format", "colors", "max_shapes", "background"} <= legacy_web
    assert {"preset", "include_facets"} <= v2_web
    assert "level" not in v2_web
    assert "background" not in v2_web

    actions = {action.dest for action in build_parser()._actions}
    assert {"output", "png", "webp", "level", "colors", "max_shapes", "background"} <= actions
    assert {"v2_shadow_png", "v2_preset", "v2_no_facets"} <= actions


def test_specialized_web_modes_are_explicitly_out_of_scope():
    report = build_migration_readiness()
    item = next(item for item in report.items if item.id == "special_modes")
    assert item.status == "out_of_scope"
    assert "Rinka Reference" in item.legacy_contract
    assert "Color Strip" in item.legacy_contract
