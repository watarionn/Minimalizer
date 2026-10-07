from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from minimalizer_zerobase.evaluation.expanded_regression_gate import (
    build_expanded_regression_gate,
)

SA10_COMPLETE_GC001_VERSION = "sa10.7-v1"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_complete_gc001_regression_artifact(
    *,
    hard_gate: Mapping[str, Any],
    adaptive_budget: Mapping[str, Any],
    semantic_retention: Mapping[str, Any],
    teacher_evaluation: Mapping[str, Any],
    component_economy: Mapping[str, Any],
) -> dict[str, Any]:
    if semantic_retention.get("authoritative") is not False:
        raise ValueError("semantic retention must be non-authoritative")
    if semantic_retention.get("can_override_hard_fail") is not False:
        raise ValueError("semantic retention cannot override hard fail")

    teacher_authority = teacher_evaluation.get("authority", {})
    if teacher_authority.get("production_input_allowed") is not False:
        raise ValueError("teacher evaluation cannot be a production input")
    if teacher_authority.get("production_output_changed") is not False:
        raise ValueError("teacher evaluation cannot change production output")

    if component_economy.get("authoritative") is not False:
        raise ValueError("component/economy evidence must be non-authoritative")

    cap = int(adaptive_budget["global_cap"])
    allocated = int(adaptive_budget["allocated_total"])
    if cap < 0 or allocated < 0 or allocated > cap:
        raise ValueError("invalid adaptive budget")
    adaptive_ratio = None if cap == 0 else allocated / cap

    coverage = teacher_evaluation["coverage_diagnostic"]
    component_survival = component_economy.get("component_survival_ratio")
    primitive_economy = component_economy.get("primitive_economy_ratio")

    report = build_expanded_regression_gate(
        hard_gate=hard_gate,
        semantic_retention_score=semantic_retention.get("semantic_retention_score"),
        adaptive_complexity_ratio=adaptive_ratio,
        component_survival_ratio=component_survival,
        primitive_economy_ratio=primitive_economy,
        teacher_coverage_ratio=coverage["coverage_ratio"],
        teacher_primitive_disagreements=coverage["primitive_disagreements"],
    )

    return {
        "artifact_version": SA10_COMPLETE_GC001_VERSION,
        "case_id": "GC001_IMG_1205",
        "regression_gate": report.to_dict(),
        "component_economy_evidence": dict(component_economy),
        "provenance": {
            "hard_gate": "GC001_sa743_gate_report.json",
            "adaptive_complexity": "GC001_sa743_macro_budget.json",
            "semantic_retention": "GC001_sa745_semantic_retention.json",
            "teacher": "GC001_sa9_teacher_evaluation.json",
            "component_survival": "GC001_sa106_component_economy.json",
            "primitive_economy": "GC001_sa106_component_economy.json",
            "role_masks": "GC001_sa106_role_masks/manifest.json",
        },
        "boundary": {
            "hard_gate_is_authority": True,
            "diagnostics_can_override_hard_fail": False,
            "aggregate_quality_score": False,
            "new_quality_thresholds_added": False,
            "golden_production_input": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hard-gate", type=Path, required=True)
    parser.add_argument("--adaptive-budget", type=Path, required=True)
    parser.add_argument("--semantic-retention", type=Path, required=True)
    parser.add_argument("--teacher-evaluation", type=Path, required=True)
    parser.add_argument("--component-economy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = build_complete_gc001_regression_artifact(
        hard_gate=_load(args.hard_gate),
        adaptive_budget=_load(args.adaptive_budget),
        semantic_retention=_load(args.semantic_retention),
        teacher_evaluation=_load(args.teacher_evaluation),
        component_economy=_load(args.component_economy),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
