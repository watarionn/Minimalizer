from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import cv2
import numpy as np

from minimalizer_zerobase.image_io import read_cv_image

from .consolidation import PaletteConsolidationResult


BACKGROUND_COLOR = (238, 238, 236)


def _sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json_sha256(payload: dict) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _write_rgb_png(path: Path, rgb: np.ndarray) -> None:
    if not cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)):
        raise OSError(f"failed to write PNG artifact: {path}")


def render_palette_preview(result: PaletteConsolidationResult) -> np.ndarray:
    canvas = np.full(
        (result.height, result.width, 3),
        BACKGROUND_COLOR,
        dtype=np.uint8,
    )
    by_id = {entry.palette_id: entry for entry in result.palette}
    for index, assignment in enumerate(result.assignments):
        if assignment.palette_id is None:
            continue
        canvas[result.mass_labels == index] = np.asarray(
            by_id[assignment.palette_id].color_rgb,
            dtype=np.uint8,
        )
    return canvas


def render_palette_strip(result: PaletteConsolidationResult) -> np.ndarray:
    cell_width = 40
    label_height = 12
    height = 52
    width = max(cell_width, cell_width * len(result.palette))
    strip = np.full((height, width, 3), BACKGROUND_COLOR, dtype=np.uint8)
    for index, entry in enumerate(result.palette):
        x0 = index * cell_width
        x1 = x0 + cell_width
        strip[: height - label_height, x0:x1] = np.asarray(
            entry.color_rgb, dtype=np.uint8
        )
        marker = (255, 255, 255) if sum(entry.color_rgb) < 384 else (30, 30, 30)
        if entry.protected_anchor:
            strip[1:4, x0 + 1 : x1 - 1] = marker
        cv2.putText(
            strip,
            str(index),
            (x0 + 3, height - 3),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.3,
            (45, 45, 45),
            1,
            cv2.LINE_8,
        )
    return strip


def phase9_metrics(result: PaletteConsolidationResult) -> dict:
    return dict(result.validation)


def _verified_declared_outputs(
    phase_dir: Path,
    stage: dict,
    *,
    consumer: str,
) -> dict[str, str]:
    outputs = stage.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        raise ValueError(f"{consumer} requires declared upstream outputs")
    verified: dict[str, str] = {}
    for name, expected_sha in sorted(outputs.items()):
        path = phase_dir / name
        if not path.is_file() or _sha256_file(path) != expected_sha:
            raise ValueError(f"{consumer} input SHA mismatch: {name}")
        verified[name] = expected_sha
    verified["stage.json"] = _sha256_file(phase_dir / "stage.json")
    return verified


def write_phase9_artifacts(
    source_path: str | Path,
    phase7_dir: str | Path,
    phase8_dir: str | Path,
    result: PaletteConsolidationResult,
    output_dir: str | Path,
    *,
    config: dict,
    phase7_stage: dict,
    phase8_stage: dict,
) -> dict:
    source_path = Path(source_path)
    phase7_dir = Path(phase7_dir)
    phase8_dir = Path(phase8_dir)
    output_dir = Path(output_dir)

    source_contract = phase8_stage.get("source")
    if not isinstance(source_contract, dict):
        raise ValueError("Phase 9 requires the Phase 8 source contract")
    source_sha = _sha256_file(source_path)
    if source_contract.get("sha256") != source_sha:
        raise ValueError("Phase 9 source SHA must match the Phase 8 source")
    if phase7_stage.get("source", {}).get("sha256") != source_sha:
        raise ValueError("Phase 9 source SHA must match the Phase 7 source")
    if (
        int(source_contract.get("width", 0)) != result.width
        or int(source_contract.get("height", 0)) != result.height
    ):
        raise ValueError("Phase 9 source dimensions must match Phase 8")
    if phase7_stage.get("metrics", {}).get("pass") is not True:
        raise ValueError("Phase 9 requires a passing Phase 7 stage")
    if phase8_stage.get("metrics", {}).get("pass") is not True:
        raise ValueError("Phase 9 requires a passing Phase 8 stage")
    phase7_inputs = _verified_declared_outputs(
        phase7_dir, phase7_stage, consumer="Phase 7"
    )
    phase8_inputs = _verified_declared_outputs(
        phase8_dir, phase8_stage, consumer="Phase 8"
    )

    source_bgr = read_cv_image(source_path, cv2.IMREAD_COLOR)
    if source_bgr is None:
        raise ValueError("Phase 9 could not read the canonical source image")
    if source_bgr.shape[:2] != (result.height, result.width):
        raise ValueError("Phase 9 source image dimensions do not match result")

    output_dir.mkdir(parents=True, exist_ok=True)

    data_path = output_dir / "09_palette.json"
    palette_preview_path = output_dir / "09_palette_preview.png"
    palette_strip_path = output_dir / "09_palette_strip.png"
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
    _write_rgb_png(palette_preview_path, render_palette_preview(result))
    _write_rgb_png(palette_strip_path, render_palette_strip(result))
    shutil.copyfile(palette_preview_path, preview_path)
    metrics = phase9_metrics(result)
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    outputs = {
        path.name: _sha256_file(path)
        for path in (
            data_path,
            palette_preview_path,
            palette_strip_path,
            preview_path,
            metrics_path,
        )
    }
    stage = {
        "phase": 9,
        "stage": "palette_consolidation",
        "producer": "minimalizer-zerobase2-phase9",
        "producer_version": "1.0",
        "source": source_contract,
        "inputs": {
            "phase7": phase7_inputs,
            "phase8": phase8_inputs,
            "source": {"path": source_path.name, "sha256": source_sha},
        },
        "config": config,
        "config_sha256": _canonical_json_sha256(config),
        "coordinate_space": result.to_dict()["coordinate_space"],
        "determinism_policy": "semantic-part-palette-consolidation-v1",
        "merge_policy": {
            "cross_part_merge": "forbidden",
            "protected_mass": "anchor-priority-with-critical-contrast-guard",
            "unbound": "isolated-no-merge-no-reinterpretation",
            "prune": "excluded-no-resurrection",
        },
        "render_authority": "deterministic-source-derived-palette-only",
        "representative_color_policy": {
            "strategy": "source-pixel-nearest-mass-mean",
            "synthetic_average_color": "forbidden",
            "observed_source_coordinate_required": True,
        },
        "provenance_policy": {
            "visible_output": "observed-source-colors-and-fixed-background-only",
            "synthetic_color": "forbidden",
            "generation": "forbidden",
            "inpainting": "forbidden",
            "hidden_completion": "forbidden",
            "phase7_geometry": "read-only",
            "phase7_semantic_ownership": "read-only",
            "phase8_action_metadata": "read-only",
            "cross_part_merge": "forbidden",
            "unbound_reinterpretation": "forbidden",
            "prune_resurrection": "forbidden",
        },
        "palette_data": {
            "path": data_path.name,
            "sha256": outputs[data_path.name],
            "palette_color_count": len(result.palette),
        },
        "metrics": metrics,
        "outputs": outputs,
    }
    stage_path.write_text(
        json.dumps(stage, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return stage
