from __future__ import annotations

import json
from pathlib import Path

from minimalizer_zerobase.golden_comparison.semantic_manifest import validate_semantic_manifest

ROOT=Path(__file__).resolve().parents[2]
TEMPLATE=ROOT/"benchmarks"/"golden"/"blind"/"GBLIND_GENERIC_V1.semantic.json"


def test_prefrozen_generic_blind_template_is_valid():
    payload=json.loads(TEMPLATE.read_text(encoding="utf-8"))
    validate_semantic_manifest(payload)


def test_template_only_uses_frozen_observer_roles():
    payload=json.loads(TEMPLATE.read_text(encoding="utf-8"))
    assert {x["semantic_role"] for x in payload["features"]}=={"hair","face-skin","limb","accessory"}


def test_template_has_no_case_specific_or_coordinate_authority():
    payload=json.loads(TEMPLATE.read_text(encoding="utf-8"))
    raw=json.dumps(payload,sort_keys=True)
    assert payload["case_id"]=="GBLIND_GENERIC_V1"
    assert [x["id"] for x in payload["features"] if x["disposition"]=="required"]==["hair"]
    for key in ('"bbox"','"polygon"','"points"','"golden"','"character_name"','"source_path"'):
        assert key not in raw
