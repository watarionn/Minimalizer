from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DISPOSITIONS = {"required", "optional", "forbidden"}
IMPORTANCE = {"identity_critical", "important", "supporting", "compressible"}
PALETTE_ROLES = {"primary", "secondary", "accent", "contrast", "neutral", "not_applicable"}
COMPRESSION_POLICIES = {"preserve", "symbolic", "omit"}
RELATION_PREDICATES = {"part_of", "attached_to", "overlaps", "paired_with", "contrasts_with"}


class SemanticManifestError(RuntimeError):
    pass


def load_semantic_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_semantic_manifest(payload)
    return payload


def validate_semantic_manifest(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "1.0":
        raise SemanticManifestError("unsupported semantic manifest schema_version")
    if not isinstance(payload.get("case_id"), str) or not payload["case_id"]:
        raise SemanticManifestError("semantic manifest requires case_id")

    features = payload.get("features")
    if not isinstance(features, list) or not features:
        raise SemanticManifestError("semantic manifest requires features")

    ids: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            raise SemanticManifestError("feature must be an object")
        feature_id = feature.get("id")
        if not isinstance(feature_id, str) or not feature_id:
            raise SemanticManifestError("feature.id is required")
        if feature_id in ids:
            raise SemanticManifestError(f"duplicate feature id: {feature_id}")
        ids.add(feature_id)
        if not isinstance(feature.get("semantic_role"), str) or not feature["semantic_role"]:
            raise SemanticManifestError(f"{feature_id}.semantic_role is required")
        if feature.get("disposition") not in DISPOSITIONS:
            raise SemanticManifestError(f"{feature_id}.disposition is invalid")
        if feature.get("importance") not in IMPORTANCE:
            raise SemanticManifestError(f"{feature_id}.importance is invalid")
        if feature.get("palette_role") not in PALETTE_ROLES:
            raise SemanticManifestError(f"{feature_id}.palette_role is invalid")
        policy = feature.get("compression_policy")
        if policy is not None and policy not in COMPRESSION_POLICIES:
            raise SemanticManifestError(f"{feature_id}.compression_policy is invalid")
        if feature["disposition"] == "forbidden" and policy not in (None, "omit"):
            raise SemanticManifestError(f"{feature_id}: forbidden features must be omitted")
        if feature["disposition"] == "required" and policy == "omit":
            raise SemanticManifestError(f"{feature_id}: required features cannot be omitted")

    relations = payload.get("relations")
    if not isinstance(relations, list):
        raise SemanticManifestError("relations must be a list")
    for relation in relations:
        if not isinstance(relation, dict):
            raise SemanticManifestError("relation must be an object")
        subject = relation.get("subject")
        obj = relation.get("object")
        if subject not in ids or obj not in ids:
            raise SemanticManifestError("relation references unknown feature")
        if relation.get("predicate") not in RELATION_PREDICATES:
            raise SemanticManifestError("relation predicate is invalid")

    regions = payload.get("evaluation_regions")
    if not isinstance(regions, list) or not regions:
        raise SemanticManifestError("semantic manifest requires evaluation_regions")
    region_ids: set[str] = set()
    for region in regions:
        if not isinstance(region, dict):
            raise SemanticManifestError("evaluation region must be an object")
        region_id = region.get("id")
        if not isinstance(region_id, str) or not region_id:
            raise SemanticManifestError("evaluation region id is required")
        if region_id in region_ids:
            raise SemanticManifestError(f"duplicate evaluation region id: {region_id}")
        region_ids.add(region_id)
        feature_ids = region.get("feature_ids")
        if not isinstance(feature_ids, list) or not feature_ids:
            raise SemanticManifestError(f"{region_id}.feature_ids is required")
        if len(feature_ids) != len(set(feature_ids)):
            raise SemanticManifestError(f"{region_id}.feature_ids contains duplicates")
        unknown = set(feature_ids) - ids
        if unknown:
            raise SemanticManifestError(f"{region_id} references unknown feature")


def canonical_semantic_manifest_json(payload: dict[str, Any]) -> str:
    validate_semantic_manifest(payload)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
