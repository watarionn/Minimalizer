from __future__ import annotations

from typing import Any, Mapping


class GuardedDiffMinError(RuntimeError):
    pass


def prepare_diffmin_refinement(
    *,
    enabled: bool = False,
    feature_survival_report: Mapping[str, Any],
    geometry_plan: Mapping[str, Any],
    baseline_renderer: str,
    candidate_renderer: str,
    requested_primitives: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if not enabled:
        return {
            "schema_version": "1.0",
            "enabled": False,
            "status": "SKIPPED",
            "reason": "diffmin_default_off",
            "may_create_semantic_parts": False,
            "may_change_primitive_count": False,
        }

    if feature_survival_report.get("gate") != "PASS":
        raise GuardedDiffMinError("DiffMin requires a hard-gate-PASS authored candidate")
    if not baseline_renderer or baseline_renderer != candidate_renderer:
        raise GuardedDiffMinError("DiffMin requires the same renderer for baseline and candidate")

    planned = geometry_plan.get("primitives")
    if not isinstance(planned, list) or not planned:
        raise GuardedDiffMinError("DiffMin requires an existing authored geometry plan")

    authorized = {
        (row.get("feature_id"), row.get("primitive_kind"), row.get("ordinal"))
        for row in planned
    }
    if None in {value for item in authorized for value in item}:
        raise GuardedDiffMinError("geometry plan contains incomplete primitive identity")

    requested = requested_primitives if requested_primitives is not None else planned
    requested_ids = {
        (row.get("feature_id"), row.get("primitive_kind"), row.get("ordinal"))
        for row in requested
    }
    if requested_ids != authorized:
        added = requested_ids - authorized
        removed = authorized - requested_ids
        raise GuardedDiffMinError(
            f"DiffMin cannot change authored primitive identity/count; added={sorted(added)!r}, removed={sorted(removed)!r}"
        )

    return {
        "schema_version": "1.0",
        "enabled": True,
        "status": "READY",
        "renderer": baseline_renderer,
        "authorized_primitive_count": len(authorized),
        "authorized_primitives": [
            {"feature_id": feature_id, "primitive_kind": kind, "ordinal": ordinal}
            for feature_id, kind, ordinal in sorted(authorized)
        ],
        "may_create_semantic_parts": False,
        "may_change_primitive_count": False,
        "may_change_primitive_identity": False,
        "optimization_scope": "parameters_of_existing_authored_geometry_only",
    }


def validate_diffmin_result(
    contract: Mapping[str, Any],
    *,
    resulting_primitives: list[Mapping[str, Any]],
    post_feature_survival_report: Mapping[str, Any],
) -> dict[str, Any]:
    if contract.get("status") != "READY":
        raise GuardedDiffMinError("DiffMin result requires a READY refinement contract")
    if post_feature_survival_report.get("gate") != "PASS":
        raise GuardedDiffMinError("DiffMin result failed the post-refinement hard gate")

    expected = {
        (row["feature_id"], row["primitive_kind"], row["ordinal"])
        for row in contract.get("authorized_primitives", [])
    }
    actual = {
        (row.get("feature_id"), row.get("primitive_kind"), row.get("ordinal"))
        for row in resulting_primitives
    }
    if actual != expected:
        raise GuardedDiffMinError("DiffMin result changed authored primitive identity/count")

    return {
        "schema_version": "1.0",
        "status": "PASS",
        "hard_gate": "PASS",
        "primitive_identity_preserved": True,
        "semantic_parts_created": False,
    }
