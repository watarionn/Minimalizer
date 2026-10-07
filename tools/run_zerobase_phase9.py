from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

from minimalizer_zerobase.image_io import read_cv_image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.artifact_contract import bridge_stage_contracts
from minimalizer_zerobase.palette import (
    PaletteConsolidationPolicy,
    consolidate_palette,
    write_phase9_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 9 palette consolidation."
    )
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    phase7_dir = args.case_dir / "phase_07"
    phase8_dir = args.case_dir / "phase_08"
    phase7_payload = json.loads(
        (phase7_dir / "07_masses.json").read_text(encoding="utf-8")
    )
    phase8_payload = json.loads(
        (phase8_dir / "08_importance.json").read_text(encoding="utf-8")
    )
    phase7_stage = json.loads(
        (phase7_dir / "stage.json").read_text(encoding="utf-8")
    )
    phase8_stage = json.loads(
        (phase8_dir / "stage.json").read_text(encoding="utf-8")
    )
    mass_labels = cv2.imread(
        str(phase7_dir / "07_mass_labels.png"),
        cv2.IMREAD_UNCHANGED,
    )
    source_bgr = read_cv_image(args.source, cv2.IMREAD_COLOR)
    if mass_labels is None or source_bgr is None:
        raise ValueError("Phase 9 could not read source or Phase 7 labels")
    source_rgb = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2RGB)

    policy = PaletteConsolidationPolicy()
    result = consolidate_palette(
        source_rgb,
        phase7_payload,
        phase8_payload,
        mass_labels,
        policy=policy,
    )
    output_dir = args.output_dir or args.case_dir / "phase_09"
    stage = write_phase9_artifacts(
        args.source,
        phase7_dir,
        phase8_dir,
        result,
        output_dir,
        config=policy.to_dict(),
        phase7_stage=phase7_stage,
        phase8_stage=phase8_stage,
    )
    bridge = bridge_stage_contracts(
        args.case_dir,
        args.source,
        max_phase=9,
    )
    summary = {
        "case": args.case_dir.name,
        "phase9_mass_count": len(result.assignments),
        "phase9_palette_entry_count": len(result.palette),
        "phase9_same_part_merge_count": result.validation[
            "same_part_merge_count"
        ],
        "phase9_reduction_ratio": result.validation[
            "palette_reduction_ratio"
        ],
        "phase9_pass": result.validation["pass"],
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
