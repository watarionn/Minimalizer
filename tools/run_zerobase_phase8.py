from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.artifact_contract import bridge_stage_contracts
from minimalizer_zerobase.importance import (
    OmissionPolicy,
    evaluate_importance_omission,
    write_phase8_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 8 importance/omission policy."
    )
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    phase7_dir = args.case_dir / "phase_07"
    phase7_payload = json.loads(
        (phase7_dir / "07_masses.json").read_text(encoding="utf-8")
    )
    phase7_stage = json.loads(
        (phase7_dir / "stage.json").read_text(encoding="utf-8")
    )
    mass_labels = cv2.imread(
        str(phase7_dir / "07_mass_labels.png"),
        cv2.IMREAD_UNCHANGED,
    )
    silhouette = cv2.imread(
        str(phase7_dir / "07_mass_silhouette.png"),
        cv2.IMREAD_GRAYSCALE,
    )
    if mass_labels is None or silhouette is None:
        raise ValueError("Phase 8 could not read mandatory Phase 7 label inputs")

    policy = OmissionPolicy()
    result = evaluate_importance_omission(
        phase7_payload,
        mass_labels,
        silhouette,
        policy=policy,
    )
    output_dir = args.output_dir or args.case_dir / "phase_08"
    stage = write_phase8_artifacts(
        args.source,
        phase7_dir,
        result,
        output_dir,
        config=policy.to_dict(),
        phase7_stage=phase7_stage,
    )
    bridge = bridge_stage_contracts(
        args.case_dir,
        args.source,
        max_phase=8,
    )
    summary = {
        "case": args.case_dir.name,
        "phase8_mass_count": len(result.decisions),
        "phase8_action_counts": result.validation["action_counts"],
        "phase8_prune_pixel_ratio": result.validation["prune_pixel_ratio"],
        "phase8_silhouette_retention_ratio": result.validation[
            "silhouette_retention_ratio"
        ],
        "phase8_pass": result.validation["pass"],
        "stage_config_sha256": stage["config_sha256"],
        "provenance_gate_passed": bridge.gate_result.passed,
        "provenance_run_id": bridge.run_manifest.run_id,
        "provenance_artifact_count": len(bridge.artifacts),
        "provenance_artifacts_sha256": (
            bridge.bundle.artifact_manifest_sha256
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
