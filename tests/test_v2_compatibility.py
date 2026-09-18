from __future__ import annotations

import inspect

from app.cli import build_parser
import web.app as web_app
from minimalize_engine.v2 import (
    PUBLIC_CONTRACT_SCHEMA_VERSION,
    build_public_contract_compatibility,
)


def test_public_contract_matrix_covers_exposed_legacy_web_controls_exactly():
    report = build_public_contract_compatibility()
    actual = set(inspect.signature(web_app.minimalize_image).parameters) - {"request"}
    matrix = {item.control for item in report.items if item.surface == "web"}
    assert matrix == actual


def test_public_contract_matrix_covers_legacy_cli_controls_exactly():
    report = build_public_contract_compatibility()
    excluded = {"help", "v2_shadow_png", "v2_preset", "v2_no_facets"}
    actual = {action.dest for action in build_parser()._actions if action.dest not in excluded}
    matrix = {item.control for item in report.items if item.surface == "cli"}
    assert matrix == actual


def test_public_contract_dispositions_are_conservative_and_machine_readable():
    report = build_public_contract_compatibility()
    payload = report.to_dict()
    assert payload["schema_version"] == PUBLIC_CONTRACT_SCHEMA_VERSION
    assert payload["scope"] == "legacy_standard_public_controls_to_v2"
    assert payload["disposition_counts"] == {
        "mapped": 2,
        "legacy_retained": 58,
        "versioned_deprecated": 0,
        "out_of_scope": 6,
    }
    by_key = {(item.surface, item.control): item for item in report.items}
    assert by_key[("web", "file")].disposition == "mapped"
    assert by_key[("cli", "input")].disposition == "mapped"
    assert by_key[("web", "level")].disposition == "legacy_retained"
    assert by_key[("web", "rinka_preset")].disposition == "out_of_scope"
    assert all(item.disposition != "versioned_deprecated" for item in report.items)
