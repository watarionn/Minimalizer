from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from minimalize_engine.v2 import AnalysisGuidance, SemanticGuide
from minimalize_engine.v2.pipeline import PipelineConfig, minimalize_v2
from minimalize_engine.v2.regression import algorithm_digest, validate_invariants
from minimalize_engine.v2.rembg_guidance import subject_confidence_from_probability

MODEL_NAME = "selfie_multiclass_256x256"


def _load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def _load_probability(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("L"), dtype=np.float32) / 255.0


def _load_semantics(path: Path, subject_prob: np.ndarray) -> SemanticGuide:
    payload = np.load(path)
    labels = tuple(str(value) for value in payload["labels"].tolist())
    confidence = np.asarray(payload["confidence"], dtype=np.float32)
    if labels != ("background", "hair", "body-skin", "face-skin", "clothes", "others"):
        raise ValueError(f"unexpected MediaPipe labels: {labels}")
    if confidence.shape[0] != len(labels) or confidence.shape[1:] != subject_prob.shape:
        raise ValueError("MediaPipe confidence tensor must match source resolution")
    foreground = confidence[1:] * subject_prob[None, ...]
    return SemanticGuide(
        labels=labels[1:],
        confidence_maps=foreground.astype(np.float32),
        provider="mediapipe",
        model=MODEL_NAME,
    )


def _high_conf_semantics(result, threshold: float = 0.80) -> tuple[int, dict[str, int]]:
    count = 0
    labels: dict[str, int] = {}
    initial = result.region_merge.initial_region_count
    for region_id in range(initial):
        stats = result.region_merge.tree.nodes[region_id].stats
        if stats.semantic_tag is None or stats.semantic_confidence < threshold:
            continue
        count += 1
        labels[stats.semantic_tag] = labels.get(stats.semantic_tag, 0) + 1
    return count, labels


def _barriers(result) -> dict[str, int]:
    return dict(result.region_merge.metrics.barrier_counts)


def compare_case(image_path: Path, rembg_mask: Path, semantic_npz: Path, config: PipelineConfig) -> dict:
    source = _load_rgb(image_path)
    subject_prob = _load_probability(rembg_mask)
    subject_conf = subject_confidence_from_probability(subject_prob, power=2.0)
    base_guidance = AnalysisGuidance(
        subject_prob=subject_prob,
        subject_confidence=subject_conf,
        subject_provider="rembg",
        subject_model="isnet-anime",
    )
    semantic = _load_semantics(semantic_npz, subject_prob)
    combined_guidance = AnalysisGuidance(
        subject_prob=subject_prob,
        subject_confidence=subject_conf,
        semantic=semantic,
        subject_provider="rembg",
        subject_model="isnet-anime",
    )
    baseline = minimalize_v2(source, presets=("minimal",), config=config, guidance=base_guidance)
    combined = minimalize_v2(source, presets=("minimal",), config=config, guidance=combined_guidance)
    checks = validate_invariants(combined, preset="minimal", config=config)
    high_count, high_labels = _high_conf_semantics(combined)
    base = baseline.presets["minimal"]
    guided = combined.presets["minimal"]
    return {
        "name": image_path.stem,
        "digest_changed": algorithm_digest(baseline, "minimal") != algorithm_digest(combined, "minimal"),
        "baseline_final_roots": baseline.region_merge.metrics.final_root_count,
        "guided_final_roots": combined.region_merge.metrics.final_root_count,
        "baseline_visual_groups": base.detail_budget.metrics.visual_group_count,
        "guided_visual_groups": guided.detail_budget.metrics.visual_group_count,
        "baseline_palette_count": base.palette.metrics.palette_count,
        "guided_palette_count": guided.palette.metrics.palette_count,
        "baseline_vertices": base.contour.metrics.simplified_vertex_count,
        "guided_vertices": guided.contour.metrics.simplified_vertex_count,
        "semantic_barriers": _barriers(combined).get("semantic", 0),
        "high_conf_semantic_regions": high_count,
        "high_conf_semantic_labels": high_labels,
        "failed_invariants": [check.name for check in checks if not check.passed],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare rembg-only V2 with rembg + MediaPipe semantic hints.")
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("rembg_mask_dir", type=Path)
    parser.add_argument("semantic_dir", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--analysis-max-side", type=int, default=400)
    args = parser.parse_args()
    config = PipelineConfig(analysis_max_side=args.analysis_max_side)
    cases = []
    for image_path in sorted(args.input_dir.glob("*.png")):
        rembg_mask = args.rembg_mask_dir / f"{image_path.stem}_mask.png"
        semantic_npz = args.semantic_dir / f"{image_path.stem}_confidence.npz"
        if not rembg_mask.exists() or not semantic_npz.exists():
            raise SystemExit(f"missing guidance asset for {image_path.stem}")
        print(f"[semantic-v2] {image_path.stem}", flush=True)
        cases.append(compare_case(image_path, rembg_mask, semantic_npz, config))

    report = {
        "model": MODEL_NAME,
        "analysis_max_side": args.analysis_max_side,
        "case_count": len(cases),
        "digest_changed_count": sum(bool(case["digest_changed"]) for case in cases),
        "invariant_failure_count": sum(bool(case["failed_invariants"]) for case in cases),
        "mean_root_delta": float(np.mean([
            case["guided_final_roots"] - case["baseline_final_roots"] for case in cases
        ])),
        "mean_visual_group_delta": float(np.mean([
            case["guided_visual_groups"] - case["baseline_visual_groups"] for case in cases
        ])),
        "mean_high_conf_semantic_regions": float(np.mean([
            case["high_conf_semantic_regions"] for case in cases
        ])),
        "total_semantic_barriers": int(sum(case["semantic_barriers"] for case in cases)),
        "cases": cases,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
