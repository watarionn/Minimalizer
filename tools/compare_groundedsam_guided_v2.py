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

MEDIAPIPE_LABELS = (
    "background", "hair", "body-skin", "face-skin", "clothes", "others",
)
GROUNDED_SAM_LABELS = ("hair", "face-skin", "limb", "accessory")
FUSED_LABELS = (
    "hair", "body-skin", "face-skin", "clothes", "others", "limb", "accessory",
)


def _load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def _load_probability(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("L"), dtype=np.float32) / 255.0


def _load_npz(path: Path) -> tuple[tuple[str, ...], np.ndarray]:
    payload = np.load(path)
    labels = tuple(str(value) for value in payload["labels"].tolist())
    confidence = np.asarray(payload["confidence"], dtype=np.float32)
    if confidence.ndim != 3 or confidence.shape[0] != len(labels):
        raise ValueError(f"invalid semantic tensor: {path}")
    return labels, confidence


def _mediapipe_guide(path: Path, subject_prob: np.ndarray) -> SemanticGuide:
    labels, confidence = _load_npz(path)
    if labels != MEDIAPIPE_LABELS:
        raise ValueError(f"unexpected MediaPipe labels: {labels}")
    if confidence.shape[1:] != subject_prob.shape:
        raise ValueError("MediaPipe confidence tensor must match source resolution")
    foreground = confidence[1:] * subject_prob[None, ...]
    return SemanticGuide(
        labels=labels[1:],
        confidence_maps=foreground.astype(np.float32),
        provider="mediapipe",
        model="selfie_multiclass_256x256",
    )


def _fused_guide(
    mediapipe_path: Path,
    groundedsam_path: Path,
    subject_prob: np.ndarray,
) -> SemanticGuide:
    mp_guide = _mediapipe_guide(mediapipe_path, subject_prob)
    gs_labels, gs_confidence = _load_npz(groundedsam_path)
    if gs_labels != GROUNDED_SAM_LABELS:
        raise ValueError(f"unexpected Grounded-SAM labels: {gs_labels}")
    if gs_confidence.shape[1:] != subject_prob.shape:
        raise ValueError("Grounded-SAM confidence tensor must match source resolution")

    fused = np.zeros((len(FUSED_LABELS), *subject_prob.shape), dtype=np.float32)
    for label, confidence in zip(mp_guide.labels, mp_guide.confidence_maps):
        fused[FUSED_LABELS.index(label)] = confidence
    for label, confidence in zip(gs_labels, gs_confidence):
        index = FUSED_LABELS.index(label)
        fused[index] = np.maximum(fused[index], confidence)
    return SemanticGuide(
        labels=FUSED_LABELS,
        confidence_maps=fused,
        provider="mediapipe+grounded-sam",
        model="selfie_multiclass_256x256+grounding-dino-tiny+sam-vit-base",
    )


def _semantic_counts(result, threshold: float) -> tuple[int, dict[str, int]]:
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


def _semantic_changed_regions(baseline, guided) -> int:
    changed = 0
    initial = baseline.region_merge.initial_region_count
    if guided.region_merge.initial_region_count != initial:
        raise ValueError("initial region count changed between semantic variants")
    for region_id in range(initial):
        left = baseline.region_merge.tree.nodes[region_id].stats
        right = guided.region_merge.tree.nodes[region_id].stats
        if (
            left.semantic_tag != right.semantic_tag
            or abs(left.semantic_confidence - right.semantic_confidence) > 1e-9
        ):
            changed += 1
    return changed
def _barriers(result) -> dict[str, int]:
    return dict(result.region_merge.metrics.barrier_counts)


def compare_case(
    image_path: Path,
    rembg_mask: Path,
    mediapipe_npz: Path,
    groundedsam_npz: Path,
    config: PipelineConfig,
) -> dict:
    source = _load_rgb(image_path)
    subject_prob = _load_probability(rembg_mask)
    subject_conf = subject_confidence_from_probability(subject_prob, power=2.0)

    baseline_semantic = _mediapipe_guide(mediapipe_npz, subject_prob)
    fused_semantic = _fused_guide(mediapipe_npz, groundedsam_npz, subject_prob)
    baseline_guidance = AnalysisGuidance(
        subject_prob=subject_prob,
        subject_confidence=subject_conf,
        semantic=baseline_semantic,
        subject_provider="rembg",
        subject_model="isnet-anime",
    )
    guided_guidance = AnalysisGuidance(
        subject_prob=subject_prob,
        subject_confidence=subject_conf,
        semantic=fused_semantic,
        subject_provider="rembg",
        subject_model="isnet-anime",
    )

    baseline = minimalize_v2(
        source, presets=("minimal",), config=config, guidance=baseline_guidance
    )
    guided = minimalize_v2(
        source, presets=("minimal",), config=config, guidance=guided_guidance
    )
    checks = validate_invariants(guided, preset="minimal", config=config)
    baseline_50, baseline_labels_50 = _semantic_counts(baseline, 0.50)
    guided_50, guided_labels_50 = _semantic_counts(guided, 0.50)
    baseline_80, baseline_labels_80 = _semantic_counts(baseline, 0.80)
    guided_80, guided_labels_80 = _semantic_counts(guided, 0.80)

    base = baseline.presets["minimal"]
    final = guided.presets["minimal"]
    return {
        "name": image_path.stem,
        "digest_changed": (
            algorithm_digest(baseline, "minimal")
            != algorithm_digest(guided, "minimal")
        ),
        "baseline_final_roots": baseline.region_merge.metrics.final_root_count,
        "guided_final_roots": guided.region_merge.metrics.final_root_count,
        "baseline_visual_groups": base.detail_budget.metrics.visual_group_count,
        "guided_visual_groups": final.detail_budget.metrics.visual_group_count,
        "baseline_palette_count": base.palette.metrics.palette_count,
        "guided_palette_count": final.palette.metrics.palette_count,
        "baseline_vertices": base.contour.metrics.simplified_vertex_count,
        "guided_vertices": final.contour.metrics.simplified_vertex_count,
        "semantic_changed_initial_regions": _semantic_changed_regions(
            baseline, guided
        ),
        "baseline_semantic_regions_ge_050": baseline_50,
        "guided_semantic_regions_ge_050": guided_50,
        "baseline_semantic_labels_ge_050": baseline_labels_50,
        "guided_semantic_labels_ge_050": guided_labels_50,
        "baseline_semantic_regions_ge_080": baseline_80,
        "guided_semantic_regions_ge_080": guided_80,
        "baseline_semantic_labels_ge_080": baseline_labels_80,
        "guided_semantic_labels_ge_080": guided_labels_80,
        "semantic_barriers": _barriers(guided).get("semantic", 0),
        "failed_invariants": [
            check.name for check in checks if not check.passed
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare Phase D rembg+MediaPipe against the same pipeline "
            "with Grounded-SAM semantic-part evidence."
        )
    )
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("rembg_mask_dir", type=Path)
    parser.add_argument("mediapipe_dir", type=Path)
    parser.add_argument("groundedsam_dir", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--analysis-max-side", type=int, default=400)
    args = parser.parse_args()
    config = PipelineConfig(analysis_max_side=args.analysis_max_side)

    cases: list[dict] = []
    for image_path in sorted(args.input_dir.glob("*.png")):
        rembg_mask = args.rembg_mask_dir / f"{image_path.stem}_mask.png"
        mediapipe_npz = args.mediapipe_dir / f"{image_path.stem}_confidence.npz"
        groundedsam_npz = (
            args.groundedsam_dir / f"{image_path.stem}_confidence.npz"
        )
        for asset in (rembg_mask, mediapipe_npz, groundedsam_npz):
            if not asset.exists():
                raise SystemExit(f"missing guidance asset: {asset}")
        print(f"[groundedsam-v2] {image_path.stem}", flush=True)
        cases.append(
            compare_case(
                image_path,
                rembg_mask,
                mediapipe_npz,
                groundedsam_npz,
                config,
            )
        )

    report = {
        "analysis_max_side": args.analysis_max_side,
        "case_count": len(cases),
        "digest_changed_count": sum(
            bool(case["digest_changed"]) for case in cases
        ),
        "invariant_failure_count": sum(
            bool(case["failed_invariants"]) for case in cases
        ),
        "mean_root_delta": float(np.mean([
            case["guided_final_roots"] - case["baseline_final_roots"]
            for case in cases
        ])),
        "mean_visual_group_delta": float(np.mean([
            case["guided_visual_groups"] - case["baseline_visual_groups"]
            for case in cases
        ])),
        "mean_vertex_delta": float(np.mean([
            case["guided_vertices"] - case["baseline_vertices"]
            for case in cases
        ])),
        "mean_semantic_changed_initial_regions": float(np.mean([
            case["semantic_changed_initial_regions"] for case in cases
        ])),
        "mean_semantic_region_delta_ge_050": float(np.mean([
            case["guided_semantic_regions_ge_050"]
            - case["baseline_semantic_regions_ge_050"]
            for case in cases
        ])),
        "mean_semantic_region_delta_ge_080": float(np.mean([
            case["guided_semantic_regions_ge_080"]
            - case["baseline_semantic_regions_ge_080"]
            for case in cases
        ])),
        "total_semantic_barriers": int(
            sum(case["semantic_barriers"] for case in cases)
        ),
        "cases": cases,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "cases"},
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
