from __future__ import annotations

import json
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from minimalizer_zerobase.binding.artifacts import UNBOUND_COLOR
from minimalizer_zerobase.parts.artifacts import PART_COLORS
from minimalizer_zerobase.subject.artifacts import (
    canonical_json_sha256,
    sha256_file,
)

from .reconstruction import MajorMassResult


def _mass_mask(result: MajorMassResult, index: int) -> np.ndarray:
    return result.mass_labels == index


def render_mass_blocks(result: MajorMassResult) -> Image.Image:
    canvas = np.full(
        (result.height, result.width, 3),
        (238, 238, 236),
        dtype=np.uint8,
    )
    for index, mass in enumerate(result.masses):
        mask = _mass_mask(result, index)
        if mass.binding_status == "unbound":
            color = np.asarray(UNBOUND_COLOR, dtype=np.uint8)
        else:
            color = np.asarray(
                [int(round(value)) for value in mass.mean_rgb],
                dtype=np.uint8,
            )
        canvas[mask] = color
    return Image.fromarray(canvas, mode="RGB")


def render_mass_silhouette(result: MajorMassResult) -> Image.Image:
    mask = (result.mass_labels >= 0).astype(np.uint8) * 255
    return Image.fromarray(mask, mode="L")


def render_mass_outline_overlay(
    source: Image.Image,
    result: MajorMassResult,
) -> Image.Image:
    rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
    if rgb.shape[:2] != (result.height, result.width):
        raise ValueError("source dimensions must match Phase 7 masses")
    canvas = np.clip(rgb.astype(np.float32) * 0.62, 0, 255).astype(np.uint8)
    bgr = cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR)
    for index, mass in enumerate(result.masses):
        mask = _mass_mask(result, index).astype(np.uint8)
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        color = (
            UNBOUND_COLOR
            if mass.semantic_part_id is None
            else PART_COLORS.get(mass.semantic_part_id, UNBOUND_COLOR)
        )
        cv2.drawContours(bgr, contours, -1, color[::-1], 1, cv2.LINE_8)
    return Image.fromarray(
        cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB),
        mode="RGB",
    )


def phase7_metrics(result: MajorMassResult) -> dict:
    return dict(result.validation)


def write_phase7_artifacts(
    source_path: str | Path,
    phase6_dir: str | Path,
    result: MajorMassResult,
    output_dir: str | Path,
    *,
    config: dict,
    phase6_stage: dict,
) -> dict:
    source_path = Path(source_path)
    phase6_dir = Path(phase6_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_contract = phase6_stage.get("source")
    if not isinstance(source_contract, dict):
        raise ValueError("Phase 7 requires the Phase 6 source contract")
    if source_contract.get("sha256") != sha256_file(source_path):
        raise ValueError("Phase 7 source SHA must match the Phase 6 source")
    if (
        int(source_contract.get("width", 0)) != result.width
        or int(source_contract.get("height", 0)) != result.height
    ):
        raise ValueError("Phase 7 source dimensions must match Phase 6")

    with Image.open(source_path) as source:
        source_copy = source.copy()
        if source_copy.size != (result.width, result.height):
            raise ValueError("Phase 7 source image dimensions do not match masses")

    data_path = output_dir / "07_masses.json"
    labels_path = output_dir / "07_mass_labels.png"
    silhouette_path = output_dir / "07_mass_silhouette.png"
    blocks_path = output_dir / "07_mass_blocks.png"
    outline_path = output_dir / "07_mass_outline_overlay.png"
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

    label_canvas = np.where(
        result.mass_labels >= 0,
        result.mass_labels,
        65535,
    ).astype(np.uint16)
    Image.fromarray(label_canvas).save(labels_path, format="PNG")
    render_mass_silhouette(result).save(silhouette_path, format="PNG")
    render_mass_blocks(result).save(blocks_path, format="PNG")
    render_mass_outline_overlay(source_copy, result).save(
        outline_path,
        format="PNG",
    )
    shutil.copyfile(blocks_path, preview_path)

    metrics = phase7_metrics(result)
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    phase6_inputs = {
        name: sha256_file(phase6_dir / name)
        for name in (
            "stage.json",
            "metrics.json",
            "06_region_bindings.json",
            "06_region_labels.png",
        )
    }
    outputs = {
        path.name: sha256_file(path)
        for path in (
            data_path,
            labels_path,
            silhouette_path,
            blocks_path,
            outline_path,
            preview_path,
            metrics_path,
        )
    }
    stage = {
        "phase": 7,
        "stage": "major_mass_reconstruction",
        "producer": "minimalizer-zerobase2-phase7",
        "producer_version": "1.0",
        "source": phase6_stage.get("source"),
        "inputs": {
            "phase6": phase6_inputs,
            "source": {
                "path": source_path.name,
                "sha256": sha256_file(source_path),
            },
        },
        "config": config,
        "config_sha256": canonical_json_sha256(config),
        "coordinate_space": result.to_dict()["coordinate_space"],
        "determinism_policy": "same-part-adjacency-components-v1",
        "merge_policy": {
            "cross_part_merge": "forbidden-v1",
            "unbound_absorption": "forbidden-v1",
            "semantic_owner": "phase06-read-only",
        },
        "mass_data": {
            "path": data_path.name,
            "sha256": outputs[data_path.name],
            "mass_count": len(result.masses),
        },
        "metrics": metrics,
        "outputs": outputs,
    }
    stage_path.write_text(
        json.dumps(stage, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return stage
