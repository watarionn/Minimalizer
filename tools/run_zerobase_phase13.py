from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.artifact_contract import bridge_stage_contracts
from minimalizer_zerobase.evaluation.debug_board import write_phase13_artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 13 stage visualizer/debug board."
    )
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--review-status",
        choices=("pending", "pass", "fail"),
        default="pending",
    )
    parser.add_argument("--first-bad-stage")
    parser.add_argument("--review-note", default="")
    parser.add_argument("--cell-size", type=int, default=300)
    parser.add_argument("--columns", type=int, default=4)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    upstream_bridge = bridge_stage_contracts(
        args.case_dir, args.source, max_phase=12
    )
    if not upstream_bridge.gate_result.passed:
        raise ValueError("Phase 13 requires a passing Phase 3-12 artifact provenance gate")

    output_dir = args.output_dir or args.case_dir / "phase_13"
    stage = write_phase13_artifacts(
        args.source,
        args.case_dir,
        output_dir,
        review_status=args.review_status,
        first_bad_stage_id=args.first_bad_stage,
        review_note=args.review_note,
        cell_size=args.cell_size,
        columns=args.columns,
    )
    final_bridge = upstream_bridge
    if output_dir.resolve() == (args.case_dir / "phase_13").resolve():
        final_bridge = bridge_stage_contracts(
            args.case_dir, args.source, max_phase=13
        )
    summary = {
        "case": args.case_dir.name,
        "phase13_pass": bool(stage["metrics"]["pass"]),
        "mandatory_stage_count": stage["metrics"]["mandatory_stage_count"],
        "upstream_all_machine_pass": stage["metrics"]["upstream_all_machine_pass"],
        "first_machine_bad_stage_id": stage["metrics"]["first_machine_bad_stage_id"],
        "human_review_status": stage["metrics"]["human_review_status"],
        "human_first_bad_stage_id": stage["metrics"]["human_first_bad_stage_id"],
        "stage_config_sha256": stage["config_sha256"],
        "provenance_gate_passed": final_bridge.gate_result.passed,
        "provenance_artifact_count": len(final_bridge.artifacts),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if stage["metrics"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
