from __future__ import annotations

from typing import Any

from .semantic_manifest import validate_semantic_manifest


class SemanticBudgetError(RuntimeError):
    pass


IMPORTANCE_ORDER = {
    "identity_critical": 0,
    "important": 1,
    "supporting": 2,
    "compressible": 3,
}

POLICY_MINIMUM = {
    "preserve": 1,
    "symbolic": 1,
    "omit": 0,
}


def _priority(feature: dict[str, Any]) -> tuple[int, int, str]:
    disposition_rank = 0 if feature["disposition"] == "required" else 1
    return (
        disposition_rank,
        IMPORTANCE_ORDER[feature["importance"]],
        feature["id"],
    )


def allocate_semantic_budget(
    manifest: dict[str, Any],
    primitive_budget: int,
) -> dict[str, Any]:
    validate_semantic_manifest(manifest)
    if not isinstance(primitive_budget, int) or isinstance(primitive_budget, bool):
        raise SemanticBudgetError("primitive_budget must be an integer")
    if primitive_budget < 0:
        raise SemanticBudgetError("primitive_budget must be non-negative")

    eligible = [
        feature
        for feature in manifest["features"]
        if feature["disposition"] != "forbidden"
        and feature.get("compression_policy", "preserve") != "omit"
    ]
    required = [feature for feature in eligible if feature["disposition"] == "required"]
    required_minimum = sum(
        POLICY_MINIMUM[feature.get("compression_policy", "preserve")]
        for feature in required
    )
    if primitive_budget < required_minimum:
        raise SemanticBudgetError(
            f"budget {primitive_budget} cannot satisfy required minimum {required_minimum}"
        )

    allocation = {feature["id"]: 0 for feature in manifest["features"]}
    remaining = primitive_budget

    for feature in sorted(required, key=_priority):
        minimum = POLICY_MINIMUM[feature.get("compression_policy", "preserve")]
        allocation[feature["id"]] += minimum
        remaining -= minimum

    optional = [
        feature for feature in eligible
        if feature["disposition"] == "optional"
    ]
    for feature in sorted(optional, key=_priority):
        if remaining <= 0:
            break
        minimum = POLICY_MINIMUM[feature.get("compression_policy", "preserve")]
        if minimum <= remaining:
            allocation[feature["id"]] += minimum
            remaining -= minimum

    ranked = sorted(eligible, key=_priority)
    index = 0
    while remaining > 0 and ranked:
        feature = ranked[index % len(ranked)]
        allocation[feature["id"]] += 1
        remaining -= 1
        index += 1

    rows = [
        {
            "feature_id": feature["id"],
            "disposition": feature["disposition"],
            "importance": feature["importance"],
            "compression_policy": feature.get("compression_policy", "preserve"),
            "allocated_primitives": allocation[feature["id"]],
        }
        for feature in sorted(manifest["features"], key=lambda item: item["id"])
    ]
    return {
        "schema_version": "1.0",
        "case_id": manifest["case_id"],
        "primitive_budget": primitive_budget,
        "required_minimum": required_minimum,
        "unallocated_primitives": remaining,
        "allocations": rows,
    }
