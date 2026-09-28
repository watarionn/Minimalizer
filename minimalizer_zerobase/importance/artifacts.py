from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import cv2
import numpy as np

from .omission import ImportanceOmissionResult


BACKGROUND_COLOR = (238, 238, 236)
PRUNE_COLOR = (224, 62, 62)
UNBOUND_COLOR = (255, 35, 225)


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


def _decision_mask(result: ImportanceOmissionResult, index: int) -> np.ndarray:
    return result.mass_labels == index


def _score_color(score: float) -> tuple[int, int, int]:
    value = min(1.0, max(0.0, float(score)))
    if value <= 0.5:
        blend = value / 0.5
        left = np.asarray((215, 64, 57), dtype=np.float64)
        right = np.asarray((238, 190, 67), dtype=np.float64)
    else:
        blend = (value - 0.5) / 0.5
        left = np.asarray((238, 190, 67), dtype=np.float64)
        right = np.asarray((55, 178, 121), dtype=np.float64)
    return tuple(
        int(round(channel))
        for channel in left * (1.0 - blend) + right * blend
    )


def render_importance_heatmap(result: ImportanceOmissionResult) -> np.ndarray:
    canvas = np.full(
        (result.height, result.width, 3),
        BACKGROUND_COLOR,
        dtype=np.uint8,
    )
    for index, decision in enumerate(result.decisions):
        color = (
            UNBOUND_COLOR
            if decision.binding_status == "unbound"
            else _score_color(decision.score)
        )
        canvas[_decision_mask(result, index)] = np.asarray(color, dtype=np.uint8)
    return canvas


def render_pruned_masses(result: ImportanceOmissionResult) -> np.ndarray:
    canvas = np.full(
        (result.height, result.width, 3),
        BACKGROUND_COLOR,
        dtype=np.uint8,
    )
    for index, decision in enumerate(result.decisions):
        if decision.action == "prune":
            continue
        color = (
            UNBOUND_COLOR
            if decision.binding_status == "unbound"
            else tuple(
                int(round(value)) for value in result.mean_rgb_by_mass[index]
            )
        )
        canvas[_decision_mask(result, index)] = np.asarray(color, dtype=np.uint8)
    return canvas


def render_removed_overlay(
    source_rgb: np.ndarray,
    result: ImportanceOmissionResult,
) -> np.ndarray:
    rgb = np.asarray(source_rgb, dtype=np.uint8)
    if rgb.shape[:2] != (result.height, result.width):
        raise ValueError("source dimensions must match Phase 8 decisions")
    canvas = np.clip(rgb.astype(np.float32) * 0.7, 0, 255).astype(np.uint8)
    removed = np.zeros((result.height, result.width), dtype=bool)
    for index, decision in enumerate(result.decisions):
        if decision.action == "prune":
            removed |= _decision_mask(result, index)
    if np.any(removed):
        red = np.asarray(PRUNE_COLOR, dtype=np.float32)
        canvas[removed] = np.clip(
            canvas[removed].astype(np.float32) * 0.35 + red * 0.65,
            0,
            255,
        ).astype(np.uint8)
        bgr = cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR)
        contours, _ = cv2.findContours(
            removed.astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        cv2.drawContours(bgr, contours, -1, PRUNE_COLOR[::-1], 1, cv2.LINE_8)
        canvas = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return canvas


def phase8_metrics(result: ImportanceOmissionResult) -> dict:
    return dict(result.validation)


def write_phase8_artifacts(
    source_path: str | Path,
    phase7_dir: str | Path,
    result: ImportanceOmissionResult,
    output_dir: str | Path,
    *,
    config: dict,
    phase7_stage: dict,
) -> dict:
    source_path = Path(source_path)
    phase7_dir = Path(phase7_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_contract = phase7_stage.get("source")
    if not isinstance(source_contract, dict):
        raise ValueError("Phase 8 requires the Phase 7 source contract")
    if source_contract.get("sha256") != _sha256_file(source_path):
        raise ValueError("Phase 8 source SHA must match the Phase 7 source")
    if (
        int(source_contract.get("width", 0)) != result.width
        or int(source_contract.get("height", 0)) != result.height
    ):
        raise ValueError("Phase 8 source dimensions must match Phase 7")
    if phase7_stage.get("metrics", {}).get("pass") is not True:
        raise ValueError("Phase 8 requires a passing Phase 7 stage")

    declared_outputs = phase7_stage.get("outputs")
    if not isinstance(declared_outputs, dict) or not declared_outputs:
        raise ValueError("Phase 8 requires declared Phase 7 outputs")
    phase7_inputs: dict[str, str] = {}
    for name, expected_sha in sorted(declared_outputs.items()):
        path = phase7_dir / name
        if not path.is_file() or _sha256_file(path) != expected_sha:
            raise ValueError(f"Phase 8 Phase 7 input SHA mismatch: {name}")
        phase7_inputs[name] = expected_sha
    phase7_inputs["stage.json"] = _sha256_file(phase7_dir / "stage.json")

    source_bgr = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if source_bgr is None:
        raise ValueError("Phase 8 could not read the canonical source image")
    source_rgb = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2RGB)
    if source_rgb.shape[:2] != (result.height, result.width):
        raise ValueError("Phase 8 source image dimensions do not match decisions")

    data_path = output_dir / "08_importance.json"
    heatmap_path = output_dir / "08_importance_heatmap.png"
    pruned_path = output_dir / "08_pruned_masses.png"
    removed_path = output_dir / "08_removed_overlay.png"
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
    _write_rgb_png(heatmap_path, render_importance_heatmap(result))
    _write_rgb_png(pruned_path, render_pruned_masses(result))
    _write_rgb_png(removed_path, render_removed_overlay(source_rgb, result))
    shutil.copyfile(pruned_path, preview_path)

    metrics = phase8_metrics(result)
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    outputs = {
        path.name: _sha256_file(path)
        for path in (
            data_path,
            heatmap_path,
            pruned_path,
            removed_path,
            preview_path,
            metrics_path,
        )
    }
    stage = {
        "phase": 8,
        "stage": "importance_omission_policy",
        "producer": "minimalizer-zerobase2-phase8",
        "producer_version": "1.0",
        "source": source_contract,
        "inputs": {
            "phase7": phase7_inputs,
            "source": {
                "path": source_path.name,
                "sha256": _sha256_file(source_path),
            },
        },
        "config": config,
        "config_sha256": _canonical_json_sha256(config),
        "coordinate_space": result.to_dict()["coordinate_space"],
        "determinism_policy": "semantic-mass-importance-omission-v1",
        "action_semantics": {
            "protect": "must-survive-downstream-omission",
            "keep": "retained-by-current-policy",
            "prune": "omission-candidate-with-explicit-redundancy-evidence",
        },
        "render_authority": "analytical-diagnostic-only",
        "provenance_policy": {
            "visible_output": "observed-source-pixels-and-fixed-diagnostic-colors-only",
            "generation": "forbidden",
            "inpainting": "forbidden",
            "hidden_completion": "forbidden",
            "phase7_semantic_ownership": "read-only",
            "unbound_reinterpretation": "forbidden",
        },
        "decision_data": {
            "path": data_path.name,
            "sha256": outputs[data_path.name],
            "mass_count": len(result.decisions),
        },
        "metrics": metrics,
        "outputs": outputs,
    }
    stage_path.write_text(
        json.dumps(stage, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return stage
