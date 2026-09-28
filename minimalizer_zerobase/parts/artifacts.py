from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from minimalizer_zerobase.subject.artifacts import canonical_json_sha256, sha256_file
from .decomposition import PART_NAMES, PartDecomposition, exclusive_part_labels

PART_COLORS = {
    "head": (205, 110, 110),
    "hair": (225, 105, 55),
    "face": (255, 202, 170),
    "neck": (235, 170, 145),
    "torso": (70, 120, 220),
    "left_arm": (70, 195, 115),
    "right_arm": (235, 198, 70),
    "lower_body": (125, 95, 195),
    "major_clothing": (105, 80, 160),
    "accessory_or_held_object": (235, 65, 185),
    "unknown": (95, 95, 95),
}


def render_part_map(result: PartDecomposition) -> Image.Image:
    labels = exclusive_part_labels(result)
    canvas = np.zeros((*labels.shape, 3), dtype=np.uint8)
    for index, name in enumerate(PART_NAMES):
        canvas[labels == index] = PART_COLORS[name]
    return Image.fromarray(canvas, mode="RGB")


def render_part_overlay(source: Image.Image, result: PartDecomposition) -> Image.Image:
    rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
    labels = exclusive_part_labels(result)
    out = (rgb.astype(np.float32) * 0.38).astype(np.uint8)
    for index, name in enumerate(PART_NAMES):
        mask = labels == index
        if not np.any(mask):
            continue
        color = np.asarray(PART_COLORS[name], dtype=np.float32)
        out[mask] = np.clip(
            rgb[mask].astype(np.float32) * 0.46 + color * 0.54,
            0,
            255,
        ).astype(np.uint8)
    return Image.fromarray(out, mode="RGB")


def write_phase4_artifacts(
    source_path: str | Path,
    phase3_dir: str | Path,
    result: PartDecomposition,
    output_dir: str | Path,
    *,
    config: dict,
    structural: dict,
) -> dict:
    source_path = Path(source_path)
    phase3_dir = Path(phase3_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    masks_dir = output_dir / "part_masks"
    masks_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as source:
        source_copy = source.copy()

    part_map_path = output_dir / "04_part_map.png"
    overlay_path = output_dir / "04_part_overlay.png"
    preview_path = output_dir / "preview.png"
    metrics_path = output_dir / "metrics.json"
    stage_path = output_dir / "stage.json"

    render_part_map(result).save(part_map_path, format="PNG")
    render_part_overlay(source_copy, result).save(overlay_path, format="PNG")
    render_part_overlay(source_copy, result).save(preview_path, format="PNG")

    for name, mask in result.part_masks.items():
        Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(
            masks_dir / f"{name}.png",
            format="PNG",
        )

    coverage = result.coverage()
    metrics = {
        "part_coverage": coverage,
        "unknown_ratio": coverage["unknown"],
        "parts_detected": [
            name
            for name in PART_NAMES
            if name != "unknown" and int(np.count_nonzero(result.part_masks[name])) > 0
        ],
        "face_bbox_xywh": list(result.face_bbox_xywh) if result.face_bbox_xywh else None,
        "face_score": result.face_score,
        "face_source": result.face_source,
        "face_landmark_confidence": result.face_landmark_confidence,
        "structural_quality": result.structural_quality,
        "accessory_kind": result.accessory_kind,
        "accessory_score": result.accessory_score,
        "hair_prototype_count": result.hair_prototype_count,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    output_hashes = {
        "04_part_map.png": sha256_file(part_map_path),
        "04_part_overlay.png": sha256_file(overlay_path),
        "preview.png": sha256_file(preview_path),
        "metrics.json": sha256_file(metrics_path),
    }
    for name in PART_NAMES:
        mask_path = masks_dir / f"{name}.png"
        output_hashes[f"part_masks/{name}.png"] = sha256_file(mask_path)

    phase3_inputs = {}
    for name in ("03_subject_mask.png", "03_subject_overlay.png", "stage.json"):
        path = phase3_dir / name
        if path.exists():
            phase3_inputs[name] = sha256_file(path)

    stage = {
        "phase": 4,
        "stage": "semantic_part_decomposition",
        "producer": "minimalizer-zerobase2-phase4",
        "producer_version": "1.0",
        "source": {
            "path": source_path.name,
            "sha256": sha256_file(source_path),
            "width": int(result.subject_mask.shape[1]),
            "height": int(result.subject_mask.shape[0]),
        },
        "inputs": {
            "phase3": phase3_inputs,
        },
        "config": config,
        "config_sha256": canonical_json_sha256(config),
        "structural": structural,
        "metrics": metrics,
        "outputs": output_hashes,
    }
    stage_path.write_text(
        json.dumps(stage, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return stage
