from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from minimalize_engine.v2 import AnalysisGuidance
from minimalize_engine.v2.rembg_guidance import subject_confidence_from_probability
from minimalize_engine.v2.pipeline import PipelineConfig, minimalize_v2
from minimalize_engine.v2.regression import algorithm_digest, validate_invariants


def _load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def _load_probability(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("L"), dtype=np.float32) / 255.0


def _barriers(result) -> dict[str, int]:
    return dict(result.region_merge.metrics.barrier_counts)


def compare_case(image_path: Path, mask_path: Path, model: str, config: PipelineConfig, confidence_power: float) -> dict:
    source = _load_rgb(image_path)
    probability = _load_probability(mask_path)
    baseline = minimalize_v2(source, presets=("minimal",), config=config)
    guided = minimalize_v2(
        source,
        presets=("minimal",),
        config=config,
        guidance=AnalysisGuidance(
            subject_prob=probability,
            subject_confidence=subject_confidence_from_probability(probability, power=confidence_power),
            subject_provider="rembg",
            subject_model=model,
        ),
    )
    baseline_barriers = _barriers(baseline)
    guided_barriers = _barriers(guided)
    checks = validate_invariants(guided, preset="minimal", config=config)
    failed = [check.name for check in checks if not check.passed]
    return {
        "name": image_path.stem,
        "baseline_digest": algorithm_digest(baseline, "minimal"),
        "guided_digest": algorithm_digest(guided, "minimal"),
        "digest_changed": algorithm_digest(baseline, "minimal") != algorithm_digest(guided, "minimal"),
        "baseline_final_roots": baseline.region_merge.metrics.final_root_count,
        "guided_final_roots": guided.region_merge.metrics.final_root_count,
        "baseline_selected_regions": len(baseline.presets["minimal"].selection.region_ids),
        "guided_selected_regions": len(guided.presets["minimal"].selection.region_ids),
        "baseline_visual_groups": baseline.presets["minimal"].detail_budget.metrics.visual_group_count,
        "guided_visual_groups": guided.presets["minimal"].detail_budget.metrics.visual_group_count,
        "baseline_palette_count": baseline.presets["minimal"].palette.metrics.palette_count,
        "guided_palette_count": guided.presets["minimal"].palette.metrics.palette_count,
        "baseline_vertices": baseline.presets["minimal"].contour.metrics.simplified_vertex_count,
        "guided_vertices": guided.presets["minimal"].contour.metrics.simplified_vertex_count,
        "baseline_subject_background_barriers": baseline_barriers.get("subject_background", 0),
        "guided_subject_background_barriers": guided_barriers.get("subject_background", 0),
        "guided_safe_merges": guided.region_merge.safe_merge_count,
        "guided_hierarchy_merges": guided.region_merge.hierarchy_merge_count,
        "failed_invariants": failed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare baseline V2 with rembg subject guidance.")
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("mask_dir", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--analysis-max-side", type=int, default=400)
    parser.add_argument("--confidence-power", type=float, default=2.0)
    args = parser.parse_args()
    config = PipelineConfig(analysis_max_side=args.analysis_max_side)
    cases = []
    for image_path in sorted(args.input_dir.glob("*.png")):
        mask_path = args.mask_dir / f"{image_path.stem}_mask.png"
        if not mask_path.exists():
            raise SystemExit(f"missing mask: {mask_path}")
        print(f"[v2] {args.model}: {image_path.stem}", flush=True)
        cases.append(compare_case(image_path, mask_path, args.model, config, args.confidence_power))

    report = {
        "model": args.model,
        "analysis_max_side": args.analysis_max_side,
        "confidence_power": args.confidence_power,
        "case_count": len(cases),
        "changed_count": sum(bool(case["digest_changed"]) for case in cases),
        "invariant_failure_count": sum(bool(case["failed_invariants"]) for case in cases),
        "mean_root_delta": float(np.mean([
            case["guided_final_roots"] - case["baseline_final_roots"] for case in cases
        ])),
        "mean_visual_group_delta": float(np.mean([
            case["guided_visual_groups"] - case["baseline_visual_groups"] for case in cases
        ])),
        "mean_subject_background_barrier_delta": float(np.mean([
            case["guided_subject_background_barriers"] - case["baseline_subject_background_barriers"]
            for case in cases
        ])),
        "cases": cases,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
