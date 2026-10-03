from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.artifact_contract import bridge_stage_contracts
from minimalizer_zerobase.evaluation import (
    HUMAN_CRITERIA,
    Phase14EvaluationPolicy,
    write_phase14_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 14 evaluation redesign/calibration."
    )
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--human-status",
        choices=("pending", "pass", "fail"),
        default="pending",
    )
    parser.add_argument(
        "--failed-criterion",
        action="append",
        choices=HUMAN_CRITERIA,
        default=[],
    )
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--review-note", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    upstream_bridge = bridge_stage_contracts(
        args.case_dir,
        args.source,
        max_phase=13,
    )
    if not upstream_bridge.gate_result.passed:
        raise ValueError(
            "Phase 14 requires a passing Phase 3-13 artifact provenance gate"
        )

    output_dir = args.output_dir or args.case_dir / "phase_14"
    stage = write_phase14_artifacts(
        args.source,
        args.case_dir,
        output_dir,
        policy=Phase14EvaluationPolicy(),
        human_status=args.human_status,
        failed_criteria=args.failed_criterion,
        reviewer=args.reviewer,
        human_note=args.review_note,
    )

    final_bridge = upstream_bridge
    if output_dir.resolve() == (args.case_dir / "phase_14").resolve():
        final_bridge = bridge_stage_contracts(
            args.case_dir,
            args.source,
            max_phase=14,
        )

    metrics = stage["metrics"]
    summary = {
        "case": args.case_dir.name,
        "phase14_pass": bool(metrics["pass"]),
        "machine_pass": bool(metrics["machine_pass"]),
        "human_visual_pass": bool(metrics["human_visual_pass"]),
        "determinism_pass": bool(metrics["determinism_pass"]),
        "silhouette_preservation": metrics["silhouette_preservation"],
        "part_layout_consistency_mean": metrics[
            "part_layout_consistency_mean"
        ],
        "part_layout_consistency_min": metrics[
            "part_layout_consistency_min"
        ],
        "major_color_mass_consistency": metrics[
            "major_color_mass_consistency"
        ],
        "identity_feature_retention": metrics[
            "identity_feature_retention"
        ],
        "primitive_economy": metrics["primitive_economy"],
        "stage_config_sha256": stage["config_sha256"],
        "provenance_gate_passed": final_bridge.gate_result.passed,
        "provenance_artifact_count": len(final_bridge.artifacts),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if metrics["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
