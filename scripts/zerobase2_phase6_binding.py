from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import skimage
from PIL import Image

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.binding import (
    BindingPolicy,
    build_region_bindings,
    write_phase6_artifacts,
)
from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.subject.artifacts import sha256_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 6 region-to-part binding.",
    )
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts/zerobase2"),
    )
    parser.add_argument("--n-segments", type=int, default=180)
    parser.add_argument("--compactness", type=float, default=12.0)
    return parser.parse_args()


def case_id(path: Path) -> str:
    return path.stem.replace("_list_thumb", "").replace("(4)", "").strip("_-")


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"required upstream artifact is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _require_hash(path: Path, expected: str | None, label: str) -> str:
    actual = sha256_file(path)
    if not expected or expected != actual:
        raise ValueError(
            f"{label} binding mismatch: expected={expected!r}, actual={actual!r}"
        )
    return actual


def _load_phase4_masks(
    phase4_dir: Path,
    phase4_stage: dict,
) -> dict[str, np.ndarray]:
    masks: dict[str, np.ndarray] = {}
    outputs = phase4_stage.get("outputs", {})
    for name in PART_NAMES:
        relative = f"part_masks/{name}.png"
        path = phase4_dir / relative
        if not path.is_file():
            raise FileNotFoundError(f"Phase 4 part mask is missing: {path}")
        _require_hash(path, outputs.get(relative), f"Phase 4 {relative}")
        with Image.open(path) as image:
            masks[name] = np.asarray(image.convert("L"), dtype=np.uint8) > 0
    return masks


def _verify_phase5(
    phase4_dir: Path,
    phase5_dir: Path,
    phase5_stage: dict,
) -> dict:
    outputs = phase5_stage.get("outputs", {})
    graph_path = phase5_dir / "05_structure_graph.json"
    _require_hash(
        graph_path,
        outputs.get("05_structure_graph.json"),
        "Phase 5 structural graph",
    )
    recorded_phase4 = phase5_stage.get("inputs", {}).get("phase4", {})
    for relative, expected in sorted(recorded_phase4.items()):
        _require_hash(phase4_dir / relative, expected, f"Phase 5 input Phase 4 {relative}")
    graph = _read_json(graph_path)
    if not graph.get("validation", {}).get("pass"):
        raise ValueError("Phase 5 structural graph did not pass its own validation")
    return graph


def main() -> int:
    args = parse_args()
    policy = BindingPolicy(
        n_segments=args.n_segments,
        compactness=args.compactness,
    )
    config = {
        **policy.to_dict(),
        "input_contract": "phase04-masks-plus-phase05-graph-read-only",
        "region_provider": "skimage.segmentation.slic",
        "region_provider_version": skimage.__version__,
        "region_provider_role": "evidence-only",
        "binding_authority": "multi-evidence-with-parent-ambiguity-inheritance",
        "semantic_boundary_policy": "split-with-parent-ambiguity-inheritance-v2",
        "graph_context_policy": "decision-support-with-spatial-corroboration",
        "boundary_geometry_policy": "independent-spatial-decision-support",
        "color_policy": "score-support-never-sole-binding-authority",
        "low_confidence_policy": "unbound",
        "upstream_mutation": "forbidden",
    }
    summaries = []
    for source_path in args.inputs:
        cid = case_id(source_path)
        phase4_dir = args.output_root / cid / "phase_04"
        phase5_dir = args.output_root / cid / "phase_05"
        phase4_stage = _read_json(phase4_dir / "stage.json")
        phase5_stage = _read_json(phase5_dir / "stage.json")
        if not source_path.is_file():
            raise FileNotFoundError(
                f"canonical source is required for Phase 6 color evidence: {source_path}"
            )
        expected_source_sha = phase4_stage.get("source", {}).get("sha256")
        actual_source_sha = _require_hash(
            source_path,
            expected_source_sha,
            f"canonical source for {cid}",
        )
        masks = _load_phase4_masks(phase4_dir, phase4_stage)
        graph = _verify_phase5(phase4_dir, phase5_dir, phase5_stage)
        with Image.open(source_path) as source:
            rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
        result = build_region_bindings(rgb, masks, graph, policy=policy)
        output_dir = args.output_root / cid / "phase_06"
        stage = write_phase6_artifacts(
            source_path,
            phase4_dir,
            phase5_dir,
            result,
            output_dir,
            config=config,
            phase4_stage=phase4_stage,
            phase5_stage=phase5_stage,
        )
        summaries.append(
            {
                "case_id": cid,
                "output_dir": str(output_dir),
                "source_sha256": actual_source_sha,
                "binding_sha256": stage["outputs"]["06_region_bindings.json"],
                "preview_sha256": stage["outputs"]["preview.png"],
                "metrics": stage["metrics"],
            }
        )
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
