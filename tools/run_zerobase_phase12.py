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
from minimalizer_zerobase.simplification import (
    StyleSimplificationPolicy,
    simplify_composed_scene,
    write_phase12_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 12 style simplification."
    )
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    phase11_dir = args.case_dir / "phase_11"
    composition_payload = _load_json(phase11_dir / "11_composition.json")
    phase11_stage = _load_json(phase11_dir / "stage.json")
    policy = StyleSimplificationPolicy()
    source_raw = cv2.imread(str(args.source), cv2.IMREAD_UNCHANGED)
    if source_raw is None:
        raise ValueError(f"unable to read Phase 12 source evidence: {args.source}")
    if source_raw.ndim == 2:
        source_rgba = cv2.cvtColor(source_raw, cv2.COLOR_GRAY2RGB)
    elif source_raw.shape[2] == 4:
        source_rgba = cv2.cvtColor(source_raw, cv2.COLOR_BGRA2RGBA)
    else:
        source_rgba = cv2.cvtColor(source_raw, cv2.COLOR_BGR2RGB)
    result = simplify_composed_scene(
        composition_payload, policy=policy, source_rgba=source_rgba
    )
    output_dir = args.output_dir or args.case_dir / "phase_12"
    stage = write_phase12_artifacts(
        args.source,
        phase11_dir,
        result,
        output_dir,
        config=policy.to_dict(),
        phase11_stage=phase11_stage,
    )
    bridge = None
    if output_dir.resolve() == (args.case_dir / "phase_12").resolve():
        bridge = bridge_stage_contracts(args.case_dir, args.source, max_phase=12)
    summary = {
        "case": args.case_dir.name,
        "phase12_pass": result.validation["pass"],
        "phase11_primitive_count": result.validation["phase11_primitive_count"],
        "selected_profile": result.validation["selected_profile"],
        "selected_primitive_count": result.validation["selected_primitive_count"],
        "candidate_metrics": {
            item.name: item.metrics for item in result.candidates
        },
        "stage_config_sha256": stage["config_sha256"],
        "provenance_gate_passed": bridge.gate_result.passed if bridge else None,
        "provenance_artifact_count": len(bridge.artifacts) if bridge else None,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if result.validation["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
