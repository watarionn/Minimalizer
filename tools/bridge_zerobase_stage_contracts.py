from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.artifact_contract import bridge_stage_contracts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bridge ZeroBase Phase 3-9 stage contracts into the common artifact graph."
    )
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--max-phase", type=int, choices=(6, 7, 8, 9), default=6)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = bridge_stage_contracts(
        args.case_dir,
        args.source,
        output_dir=args.output_dir,
        max_phase=args.max_phase,
    )
    payload = {
        "run_id": result.run_manifest.run_id,
        "artifact_count": len(result.artifacts),
        "gate_passed": result.gate_result.passed,
        "run_manifest": result.bundle.run_manifest_path,
        "run_manifest_sha256": result.bundle.run_manifest_sha256,
        "artifact_manifest": result.bundle.artifact_manifest_path,
        "artifact_manifest_sha256": result.bundle.artifact_manifest_sha256,
        "gate_report": result.gate_report_path,
        "gate_report_sha256": result.gate_report_sha256,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
