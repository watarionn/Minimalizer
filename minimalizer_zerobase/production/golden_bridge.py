from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from minimalizer_zerobase.golden_comparison.feature_survival import evaluate_feature_survival
from minimalizer_zerobase.golden_comparison.semantic_budget import allocate_semantic_budget
from minimalizer_zerobase.golden_comparison.geometry_grammar import build_geometry_plan
from minimalizer_zerobase.golden_comparison.guarded_diffmin import prepare_diffmin_refinement


class GoldenProductionBridgeError(RuntimeError):
    pass


@dataclass(frozen=True)
class GoldenProductionBridgePolicy:
    enabled: bool = False
    primitive_budget: int = 12
    diffmin_enabled: bool = False
    renderer: str = "SvgRenderer"


def prepare_golden_candidate(
    *,
    manifest: dict[str, Any],
    feature_evidence: Mapping[str, Any],
    policy: GoldenProductionBridgePolicy | None = None,
) -> dict[str, Any]:
    policy = policy or GoldenProductionBridgePolicy()
    if not policy.enabled:
        return {
            "schema_version": "1.0",
            "status": "SKIPPED",
            "reason": "golden_production_bridge_default_off",
            "production_candidate_authorized": False,
        }

    survival = evaluate_feature_survival(manifest, feature_evidence)
    if survival["gate"] != "PASS":
        return {
            "schema_version": "1.0",
            "status": "BLOCKED",
            "reason": "feature_survival_hard_gate_failed",
            "feature_survival": survival,
            "production_candidate_authorized": False,
        }

    budget = allocate_semantic_budget(manifest, policy.primitive_budget)
    geometry = build_geometry_plan(manifest, budget)
    diffmin = prepare_diffmin_refinement(
        enabled=policy.diffmin_enabled,
        feature_survival_report=survival,
        geometry_plan=geometry,
        baseline_renderer=policy.renderer,
        candidate_renderer=policy.renderer,
    )
    return {
        "schema_version": "1.0",
        "status": "READY",
        "case_id": manifest["case_id"],
        "feature_survival": survival,
        "semantic_budget": budget,
        "geometry_plan": geometry,
        "diffmin": diffmin,
        "renderer": policy.renderer,
        "production_candidate_authorized": True,
        "golden_raster_is_production_input": False,
    }
