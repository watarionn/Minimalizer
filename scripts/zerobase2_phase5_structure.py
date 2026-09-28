from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.structure.artifacts import write_phase5_artifacts
from minimalizer_zerobase.structure.graph import build_structural_layout_graph
from minimalizer_zerobase.subject.artifacts import sha256_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 5 structural layout graph.",
    )
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts/zerobase2"),
    )
    return parser.parse_args()


def case_id(path: Path) -> str:
    return path.stem.replace("_list_thumb", "").replace("(4)", "").strip("_-")


def _load_phase4_masks(phase4_dir: Path, phase4_stage: dict) -> dict[str, np.ndarray]:
    masks: dict[str, np.ndarray] = {}
    recorded_outputs = phase4_stage.get("outputs", {})
    for name in PART_NAMES:
        relative = f"part_masks/{name}.png"
        path = phase4_dir / "part_masks" / f"{name}.png"
        if not path.is_file():
            raise FileNotFoundError(f"Phase 4 part mask is missing: {path}")
        recorded_sha = recorded_outputs.get(relative)
        actual_sha = sha256_file(path)
        if recorded_sha != actual_sha:
            raise ValueError(
                f"Phase 4 part mask binding mismatch for {relative}: "
                f"recorded={recorded_sha!r}, actual={actual_sha!r}"
            )
        with Image.open(path) as image:
            masks[name] = np.asarray(image.convert("L"), dtype=np.uint8) > 0
    return masks


def main() -> int:
    args = parse_args()
    config = {
        "input_contract": "phase04-part-masks-read-only",
        "anchor_policy": "centroid-plus-nearest-boundary-v1",
        "attachment_policy": "adaptive-mask-distance-v1",
        "occlusion_policy": "phase04-display-priority-dag-v1",
        "mask_mutation": "forbidden",
        "visual_source_policy": "canonical-or-bound-phase03-overlay-when-absent",
    }
    summaries = []
    for source_path in args.inputs:
        cid = case_id(source_path)
        phase4_dir = args.output_root / cid / "phase_04"
        stage_path = phase4_dir / "stage.json"
        if not stage_path.is_file():
            raise FileNotFoundError(f"Phase 4 stage is missing: {stage_path}")
        phase4_stage = json.loads(stage_path.read_text(encoding="utf-8"))
        canonical_source = phase4_stage.get("source", {})
        expected_source_sha = canonical_source.get("sha256")
        if source_path.is_file():
            visual_source_path = source_path
            visual_source_kind = "canonical-source"
            actual_source_sha = sha256_file(source_path)
            if expected_source_sha != actual_source_sha:
                raise ValueError(
                    f"source binding mismatch for {cid}: "
                    f"recorded={expected_source_sha!r}, actual={actual_source_sha!r}"
                )
        else:
            phase3_dir = args.output_root / cid / "phase_03"
            phase3_stage_path = phase3_dir / "stage.json"
            visual_source_path = phase3_dir / "03_subject_overlay.png"
            if not phase3_stage_path.is_file() or not visual_source_path.is_file():
                raise FileNotFoundError(
                    f"canonical source and Phase 3 visual fallback are both missing for {cid}"
                )
            phase3_stage = json.loads(phase3_stage_path.read_text(encoding="utf-8"))
            if phase3_stage.get("source", {}).get("sha256") != expected_source_sha:
                raise ValueError(f"Phase 3 source binding mismatch for {cid}")
            recorded_overlay_sha = phase3_stage.get("outputs", {}).get(
                "03_subject_overlay.png"
            )
            actual_overlay_sha = sha256_file(visual_source_path)
            if recorded_overlay_sha != actual_overlay_sha:
                raise ValueError(f"Phase 3 visual fallback binding mismatch for {cid}")
            actual_source_sha = expected_source_sha
            visual_source_kind = "phase03-subject-overlay-bound-fallback"
        masks = _load_phase4_masks(phase4_dir, phase4_stage)
        phase4_metrics = phase4_stage.get("metrics", {})
        graph = build_structural_layout_graph(
            masks,
            accessory_kind=str(phase4_metrics.get("accessory_kind", "none")),
            accessory_confidence=float(phase4_metrics.get("accessory_score", 0.0)),
        )
        output_dir = args.output_root / cid / "phase_05"
        stage = write_phase5_artifacts(
            visual_source_path,
            phase4_dir,
            masks,
            graph,
            output_dir,
            config=config,
            phase4_stage=phase4_stage,
            canonical_source=canonical_source,
            visual_source_kind=visual_source_kind,
        )
        summaries.append(
            {
                "case_id": cid,
                "output_dir": str(output_dir),
                "source_sha256": actual_source_sha,
                "visual_source_kind": visual_source_kind,
                "graph_sha256": stage["outputs"]["05_structure_graph.json"],
                "overlay_sha256": stage["outputs"]["05_structure_graph_overlay.png"],
                "metrics": stage["metrics"],
            }
        )
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
