from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from minimalizer_zerobase.golden_comparison.semantic_manifest import (
    SemanticManifestError,
    canonical_semantic_manifest_json,
    load_semantic_manifest,
    validate_semantic_manifest,
)

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "benchmarks" / "golden" / "cases" / "GC001_IMG_1205.semantic.json"


def _case() -> dict:
    return json.loads(CASE.read_text(encoding="utf-8"))


def test_gc001_semantic_manifest_is_valid_and_deterministic() -> None:
    first = canonical_semantic_manifest_json(load_semantic_manifest(CASE))
    second = canonical_semantic_manifest_json(load_semantic_manifest(CASE))
    assert first == second


def test_gc001_required_identity_features_are_authority() -> None:
    features = {item["id"]: item for item in _case()["features"]}
    required = {"orange_hair", "goggles", "green_necktie", "navy_white_uniform"}
    assert {key for key, item in features.items() if item["disposition"] == "required"} == required
    assert all(features[key]["importance"] == "identity_critical" for key in required)
    assert all(features[key]["compression_policy"] == "preserve" for key in required)


def test_gc001_facial_details_are_forbidden_and_omitted() -> None:
    features = {item["id"]: item for item in _case()["features"]}
    assert features["facial_details"]["disposition"] == "forbidden"
    assert features["facial_details"]["compression_policy"] == "omit"


def test_forbidden_feature_cannot_request_preservation() -> None:
    payload = _case()
    feature = next(item for item in payload["features"] if item["id"] == "facial_details")
    feature["compression_policy"] = "preserve"
    with pytest.raises(SemanticManifestError, match="forbidden features must be omitted"):
        validate_semantic_manifest(payload)


def test_required_feature_cannot_be_omitted() -> None:
    payload = _case()
    feature = next(item for item in payload["features"] if item["id"] == "goggles")
    feature["compression_policy"] = "omit"
    with pytest.raises(SemanticManifestError, match="required features cannot be omitted"):
        validate_semantic_manifest(payload)


def test_relations_fail_closed_on_unknown_feature() -> None:
    payload = _case()
    payload["relations"].append({"subject": "unknown", "predicate": "attached_to", "object": "orange_hair"})
    with pytest.raises(SemanticManifestError, match="unknown feature"):
        validate_semantic_manifest(payload)


def test_evaluation_regions_are_semantic_not_coordinate_targets() -> None:
    payload = _case()
    raw = json.dumps(payload, sort_keys=True)
    forbidden_coordinate_keys = {"x", "y", "x1", "y1", "x2", "y2", "bbox", "polygon", "points"}
    assert not any(f'"{key}"' in raw for key in forbidden_coordinate_keys)
    assert all(set(region) == {"id", "feature_ids"} for region in payload["evaluation_regions"])


def test_gc001_semantic_manifest_matches_golden_case_identity() -> None:
    golden_case = json.loads(
        (ROOT / "benchmarks" / "golden" / "cases" / "GC001_IMG_1205.json").read_text(encoding="utf-8")
    )
    semantic_case = _case()
    assert semantic_case["case_id"] == golden_case["case_id"]
