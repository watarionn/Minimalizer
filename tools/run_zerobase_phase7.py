from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.artifact_contract import bridge_stage_contracts
from minimalizer_zerobase.mass import (
    MajorMassPolicy,
    reconstruct_major_masses,
    write_phase7_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 7 major mass reconstruction."
    )
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--minimum-shared-boundary-pixels",
        type=int,
        default=1,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    phase6_dir = args.case_dir / "phase_06"
    phase6_data_path = phase6_dir / "06_region_bindings.json"
    phase6_stage_path = phase6_dir / "stage.json"
    phase6_payload = json.loads(
        phase6_data_path.read_text(encoding="utf-8")
    )
    phase6_stage = json.loads(
        phase6_stage_path.read_text(encoding="utf-8")
    )
    with Image.open(args.source) as source:
        source_rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)

    policy = MajorMassPolicy(
        minimum_shared_boundary_pixels=args.minimum_shared_boundary_pixels,
    )
    result = reconstruct_major_masses(
        source_rgb,
        phase6_payload,
        policy=policy,
    )
    output_dir = args.output_dir or args.case_dir / "phase_07"
    stage = write_phase7_artifacts(
        args.source,
        phase6_dir,
        result,
        output_dir,
        config=policy.to_dict(),
        phase6_stage=phase6_stage,
    )

    bridge = bridge_stage_contracts(
        args.case_dir,
        args.source,
        max_phase=7,
    )
    summary = {
        "case": args.case_dir.name,
        "phase7_mass_count": len(result.masses),
        "phase7_bound_mass_count": result.validation["bound_mass_count"],
        "phase7_unbound_mass_count": result.validation["unbound_mass_count"],
        "phase7_reduction_ratio": result.validation[
            "region_to_mass_reduction_ratio"
        ],
        "phase7_pass": result.validation["pass"],
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
