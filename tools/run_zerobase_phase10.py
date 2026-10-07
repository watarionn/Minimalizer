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
from minimalizer_zerobase.geometrization import write_phase10_artifacts
from minimalizer_zerobase.production.profile import reviewed_sa10_enabled

if reviewed_sa10_enabled():
    from minimalizer_zerobase.reviewed_sa10.geometrization_part_aware import (
        PartAwareGeometrizationPolicy,
        geometrize_parts,
    )
else:
    from minimalizer_zerobase.geometrization import (
        PartAwareGeometrizationPolicy,
        geometrize_parts,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 10 part-aware geometrization."
    )
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    phase7_dir = args.case_dir / "phase_07"
    phase8_dir = args.case_dir / "phase_08"
    phase9_dir = args.case_dir / "phase_09"
    phase7_payload = _load_json(phase7_dir / "07_masses.json")
    phase8_payload = _load_json(phase8_dir / "08_importance.json")
    phase9_payload = _load_json(phase9_dir / "09_palette.json")
    phase7_stage = _load_json(phase7_dir / "stage.json")
    phase8_stage = _load_json(phase8_dir / "stage.json")
    phase9_stage = _load_json(phase9_dir / "stage.json")
    mass_labels = cv2.imread(
        str(phase7_dir / "07_mass_labels.png"), cv2.IMREAD_UNCHANGED
    )
    if mass_labels is None:
        raise ValueError("Phase 10 could not read Phase 7 mass labels")

    policy = PartAwareGeometrizationPolicy()
    result = geometrize_parts(
        phase7_payload,
        phase8_payload,
        phase9_payload,
        mass_labels,
        policy=policy,
    )
    output_dir = args.output_dir or args.case_dir / "phase_10"
    stage = write_phase10_artifacts(
        args.source,
        phase7_dir,
        phase8_dir,
        phase9_dir,
        result,
        output_dir,
        config=policy.to_dict(),
        phase7_stage=phase7_stage,
        phase8_stage=phase8_stage,
        phase9_stage=phase9_stage,
    )
    bridge = bridge_stage_contracts(args.case_dir, args.source, max_phase=10)
    summary = {
        "case": args.case_dir.name,
        "phase10_candidate_count": len(result.candidates),
        "phase10_selected_primitive_count": len(result.selected),
        "phase10_selected_family_counts": result.validation["selected_family_counts"],
        "phase10_mean_selected_iou": result.validation["mean_selected_iou"],
        "phase10_pass": result.validation["pass"],
        "stage_config_sha256": stage["config_sha256"],
        "provenance_gate_passed": bridge.gate_result.passed,
        "provenance_run_id": bridge.run_manifest.run_id,
        "provenance_artifact_count": len(bridge.artifacts),
        "provenance_artifacts_sha256": bridge.bundle.artifact_manifest_sha256,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
