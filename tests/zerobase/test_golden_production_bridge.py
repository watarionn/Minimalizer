from __future__ import annotations

from minimalizer_zerobase.production.golden_bridge import (
    GoldenProductionBridgePolicy,
    prepare_golden_candidate,
)


def _manifest() -> dict:
    return {
        "schema_version": "1.0",
        "case_id": "blind_synthetic",
        "features": [
            {"id":"hair","semantic_role":"hair","disposition":"required","importance":"identity_critical","palette_role":"primary","compression_policy":"preserve"},
            {"id":"tie","semantic_role":"necktie","disposition":"required","importance":"important","palette_role":"accent","compression_policy":"preserve"},
            {"id":"face_detail","semantic_role":"face_detail","disposition":"forbidden","importance":"compressible","palette_role":"not_applicable","compression_policy":"omit"},
        ],
        "relations": [{"subject":"tie","predicate":"attached_to","object":"hair"}],
        "evaluation_regions": [{"id":"identity","feature_ids":["hair","tie"]}],
    }


def _evidence() -> dict:
    return {
        "hair":{"state":"present","source":"synthetic"},
        "tie":{"state":"present","source":"synthetic"},
        "face_detail":{"state":"absent","source":"synthetic"},
    }


def test_bridge_is_default_off() -> None:
    report=prepare_golden_candidate(manifest=_manifest(),feature_evidence=_evidence())
    assert report["status"]=="SKIPPED"
    assert report["production_candidate_authorized"] is False


def test_hard_gate_failure_blocks_candidate_before_budget_or_geometry() -> None:
    evidence=_evidence(); evidence["tie"]={"state":"absent","source":"synthetic"}
    report=prepare_golden_candidate(
        manifest=_manifest(), feature_evidence=evidence,
        policy=GoldenProductionBridgePolicy(enabled=True),
    )
    assert report["status"]=="BLOCKED"
    assert "semantic_budget" not in report
    assert report["production_candidate_authorized"] is False


def test_ready_bridge_connects_g3_g4_g5_and_g7_without_golden_raster() -> None:
    report=prepare_golden_candidate(
        manifest=_manifest(), feature_evidence=_evidence(),
        policy=GoldenProductionBridgePolicy(enabled=True, primitive_budget=5),
    )
    assert report["status"]=="READY"
    assert report["feature_survival"]["gate"]=="PASS"
    assert report["semantic_budget"]["primitive_budget"]==5
    assert report["geometry_plan"]["primitives"]
    assert report["diffmin"]["status"]=="SKIPPED"
    assert report["golden_raster_is_production_input"] is False


def test_diffmin_remains_explicit_opt_in_inside_bridge() -> None:
    report=prepare_golden_candidate(
        manifest=_manifest(), feature_evidence=_evidence(),
        policy=GoldenProductionBridgePolicy(enabled=True, primitive_budget=5, diffmin_enabled=True),
    )
    assert report["diffmin"]["status"]=="READY"
    assert report["diffmin"]["optimization_scope"]=="parameters_of_existing_authored_geometry_only"


def test_manifest_feature_names_are_not_gc001_specific() -> None:
    report=prepare_golden_candidate(
        manifest=_manifest(), feature_evidence=_evidence(),
        policy=GoldenProductionBridgePolicy(enabled=True, primitive_budget=4),
    )
    assert report["case_id"]=="blind_synthetic"
    assert {x["feature_id"] for x in report["geometry_plan"]["primitives"]} <= {"hair","tie"}
