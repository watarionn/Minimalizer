from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.artifact_contract import bridge_stage_contracts
from minimalizer_zerobase.composition import (
    CompositionPolicy,
    compose_semantic_scene,
    write_phase11_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 11 semantic composition."
    )
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    phase5_dir = args.case_dir / "phase_05"
    phase10_dir = args.case_dir / "phase_10"
    graph_payload = _load_json(phase5_dir / "05_structure_graph.json")
    geometry_payload = _load_json(phase10_dir / "10_geometry.json")
    phase5_stage = _load_json(phase5_dir / "stage.json")
    phase10_stage = _load_json(phase10_dir / "stage.json")
    policy = CompositionPolicy()
    result = compose_semantic_scene(graph_payload, geometry_payload, policy=policy)
    output_dir = args.output_dir or args.case_dir / "phase_11"
    stage = write_phase11_artifacts(
        args.source,
        phase5_dir,
        phase10_dir,
        result,
        output_dir,
        config=policy.to_dict(),
        phase5_stage=phase5_stage,
        phase10_stage=phase10_stage,
    )
    bridge = None
    if output_dir.resolve() == (args.case_dir / "phase_11").resolve():
        bridge = bridge_stage_contracts(args.case_dir, args.source, max_phase=11)
    summary = {
        "case": args.case_dir.name,
        "phase11_selected_primitive_count": len(result.primitives),
        "phase11_part_raster_order": list(result.part_raster_order),
        "phase11_applied_graph_edge_count": len(result.applied_graph_edges),
        "phase11_unresolved_depth_pair_count": len(result.unresolved_depth_pairs),
        "phase11_pass": result.validation["pass"],
        "stage_config_sha256": stage["config_sha256"],
        "provenance_gate_passed": bridge.gate_result.passed if bridge else None,
        "provenance_run_id": bridge.run_manifest.run_id if bridge else None,
        "provenance_artifact_count": len(bridge.artifacts) if bridge else None,
        "provenance_artifacts_sha256": (
            bridge.bundle.artifact_manifest_sha256 if bridge else None
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
