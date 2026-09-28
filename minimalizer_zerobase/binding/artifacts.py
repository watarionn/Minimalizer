from __future__ import annotations

import json
import shutil
from pathlib import Path

import cv2
import numpy as np
import skimage
from PIL import Image

from minimalizer_zerobase.parts.artifacts import PART_COLORS
from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.subject.artifacts import canonical_json_sha256, sha256_file

from .region_binding import RegionBindingResult

UNBOUND_COLOR = (255, 35, 225)


def _region_boundaries(labels: np.ndarray) -> np.ndarray:
    boundaries = np.zeros(labels.shape, dtype=bool)
    boundaries[:, 1:] |= labels[:, 1:] != labels[:, :-1]
    boundaries[:, :-1] |= labels[:, 1:] != labels[:, :-1]
    boundaries[1:, :] |= labels[1:, :] != labels[:-1, :]
    boundaries[:-1, :] |= labels[1:, :] != labels[:-1, :]
    return boundaries & (labels >= 0)


def render_region_binding(
    source: Image.Image,
    result: RegionBindingResult,
) -> Image.Image:
    rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
    if rgb.shape[:2] != (result.height, result.width):
        raise ValueError("source dimensions must match Phase 6 bindings")
    output = np.clip(rgb.astype(np.float32) * 0.42, 0, 255).astype(np.uint8)
    by_label = {region.source_region_label: region for region in result.regions}
    for label, region in sorted(by_label.items()):
        mask = result.region_labels == label
        color = np.asarray(
            PART_COLORS.get(region.semantic_part_id, UNBOUND_COLOR),
            dtype=np.float32,
        )
        output[mask] = np.clip(
            rgb[mask].astype(np.float32) * 0.42 + color * 0.58,
            0,
            255,
        ).astype(np.uint8)
    output[_region_boundaries(result.region_labels)] = (245, 245, 245)
    return Image.fromarray(output, mode="RGB")


def render_unbound_overlay(
    source: Image.Image,
    result: RegionBindingResult,
) -> Image.Image:
    rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
    output = np.clip(rgb.astype(np.float32) * 0.58, 0, 255).astype(np.uint8)
    unbound = np.zeros(result.region_labels.shape, dtype=bool)
    for region in result.regions:
        if region.binding_status == "unbound":
            unbound |= result.region_labels == region.source_region_label
    color = np.asarray(UNBOUND_COLOR, dtype=np.float32)
    output[unbound] = np.clip(
        rgb[unbound].astype(np.float32) * 0.28 + color * 0.72,
        0,
        255,
    ).astype(np.uint8)
    if np.any(unbound):
        contours, _ = cv2.findContours(
            unbound.astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        bgr = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
        cv2.drawContours(bgr, contours, -1, (0, 255, 255), 1, cv2.LINE_8)
        output = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(output, mode="RGB")


def phase6_metrics(result: RegionBindingResult) -> dict:
    part_region_counts = {name: 0 for name in PART_NAMES}
    part_pixel_counts = {name: 0 for name in PART_NAMES}
    unbound_count = 0
    unbound_pixels = 0
    confidences: list[float] = []
    for region in result.regions:
        if region.semantic_part_id is None:
            unbound_count += 1
            unbound_pixels += region.pixel_count
        else:
            part_region_counts[region.semantic_part_id] += 1
            part_pixel_counts[region.semantic_part_id] += region.pixel_count
            confidences.append(region.binding_confidence)
    return {
        "region_count": len(result.regions),
        "bound_region_count": len(result.regions) - unbound_count,
        "unbound_region_count": unbound_count,
        "unbound_pixel_count": unbound_pixels,
        "mean_bound_confidence": (
            round(float(np.mean(confidences)), 6) if confidences else 0.0
        ),
        "part_region_counts": part_region_counts,
        "part_pixel_counts": part_pixel_counts,
        **result.validation,
    }


def write_phase6_artifacts(
    source_path: str | Path,
    phase4_dir: str | Path,
    phase5_dir: str | Path,
    result: RegionBindingResult,
    output_dir: str | Path,
    *,
    config: dict,
    phase4_stage: dict,
    phase5_stage: dict,
) -> dict:
    source_path = Path(source_path)
    phase4_dir = Path(phase4_dir)
    phase5_dir = Path(phase5_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(source_path) as source:
        source_copy = source.copy()

    data_path = output_dir / "06_region_bindings.json"
    label_path = output_dir / "06_region_labels.png"
    binding_path = output_dir / "06_region_binding.png"
    unbound_path = output_dir / "06_unbound_overlay.png"
    preview_path = output_dir / "preview.png"
    metrics_path = output_dir / "metrics.json"
    stage_path = output_dir / "stage.json"

    data_path.write_text(
        json.dumps(
            result.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    label_canvas = np.where(result.region_labels >= 0, result.region_labels, 65535).astype(
        np.uint16
    )
    Image.fromarray(label_canvas).save(label_path, format="PNG")
    render_region_binding(source_copy, result).save(binding_path, format="PNG")
    render_unbound_overlay(source_copy, result).save(unbound_path, format="PNG")
    shutil.copyfile(binding_path, preview_path)

    metrics = phase6_metrics(result)
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    phase4_inputs = {
        "stage.json": sha256_file(phase4_dir / "stage.json"),
        "metrics.json": sha256_file(phase4_dir / "metrics.json"),
    }
    for name in PART_NAMES:
        relative = f"part_masks/{name}.png"
        phase4_inputs[relative] = sha256_file(phase4_dir / relative)
    phase5_inputs = {
        "stage.json": sha256_file(phase5_dir / "stage.json"),
        "metrics.json": sha256_file(phase5_dir / "metrics.json"),
        "05_structure_graph.json": sha256_file(
            phase5_dir / "05_structure_graph.json"
        ),
    }
    outputs = {
        path.name: sha256_file(path)
        for path in (
            data_path,
            label_path,
            binding_path,
            unbound_path,
            preview_path,
            metrics_path,
        )
    }
    stage = {
        "phase": 6,
        "stage": "region_to_part_binding",
        "producer": "minimalizer-zerobase2-phase6",
        "producer_version": "1.0",
        "source": phase4_stage.get("source"),
        "inputs": {
            "phase4": phase4_inputs,
            "phase5": phase5_inputs,
            "source": {
                "path": source_path.name,
                "sha256": sha256_file(source_path),
            },
        },
        "config": config,
        "config_sha256": canonical_json_sha256(config),
        "analyzer_provenance": {
            "region_provider": "skimage.segmentation.slic",
            "region_provider_version": skimage.__version__,
            "region_provider_role": "evidence-only",
            "phase4_config_sha256": phase4_stage.get("config_sha256"),
            "phase5_config_sha256": phase5_stage.get("config_sha256"),
        },
        "coordinate_space": result.to_dict()["coordinate_space"],
        "determinism_policy": "seedless-slic-plus-pure-mask-binding-v1",
        "binding_data": {
            "path": data_path.name,
            "sha256": outputs[data_path.name],
            "region_count": len(result.regions),
        },
        "metrics": metrics,
        "outputs": outputs,
    }
    stage_path.write_text(
        json.dumps(stage, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return stage
