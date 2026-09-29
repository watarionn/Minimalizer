from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import cv2
import numpy as np

from .part_aware import FAMILY_ORDER, PartAwareGeometrizationResult


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


def _outline(mask: np.ndarray) -> np.ndarray:
    binary = mask.astype(np.uint8)
    eroded = cv2.erode(binary, np.ones((3, 3), dtype=np.uint8), iterations=1)
    return (binary > 0) & (eroded == 0)


def render_selected_primitives(result: PartAwareGeometrizationResult) -> np.ndarray:
    canvas = np.full((result.height, result.width, 3), BACKGROUND_COLOR, dtype=np.uint8)
    for item in sorted(result.selected, key=lambda primitive: primitive.mass_id):
        mask = result.candidate_masks[item.candidate_id]
        canvas[mask] = np.asarray(item.palette_color_rgb, dtype=np.uint8)
        canvas[_outline(mask)] = np.asarray((45, 45, 45), dtype=np.uint8)
    return canvas


def render_candidate_grid(result: PartAwareGeometrizationResult) -> np.ndarray:
    present = [
        family
        for family in FAMILY_ORDER
        if any(item.primitive_type == family for item in result.candidates)
    ]
    columns = 4
    rows = max(1, (len(present) + columns - 1) // columns)
    grid = np.full(
        (rows * result.height, columns * result.width, 3),
        BACKGROUND_COLOR,
        dtype=np.uint8,
    )
    color_by_mass = {item.mass_id: item.palette_color_rgb for item in result.selected}
    for panel_index, family in enumerate(present):
        y0 = (panel_index // columns) * result.height
        x0 = (panel_index % columns) * result.width
        panel = np.full((result.height, result.width, 3), BACKGROUND_COLOR, dtype=np.uint8)
        for candidate in sorted(result.candidates, key=lambda item: item.mass_id):
            if candidate.primitive_type != family:
                continue
            mask = result.candidate_masks[candidate.candidate_id]
            panel[mask] = np.asarray(color_by_mass[candidate.mass_id], dtype=np.uint8)
            panel[_outline(mask)] = np.asarray((45, 45, 45), dtype=np.uint8)
        cv2.putText(
            panel,
            family,
            (6, 16),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (20, 20, 20),
            1,
            cv2.LINE_8,
        )
        grid[y0 : y0 + result.height, x0 : x0 + result.width] = panel
    return grid


def phase10_metrics(result: PartAwareGeometrizationResult) -> dict:
    return dict(result.validation)


def _verified_declared_outputs(phase_dir: Path, stage: dict, *, consumer: str) -> dict[str, str]:
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


def write_phase10_artifacts(
    source_path: str | Path,
    phase7_dir: str | Path,
    phase8_dir: str | Path,
    phase9_dir: str | Path,
    result: PartAwareGeometrizationResult,
    output_dir: str | Path,
    *,
    config: dict,
    phase7_stage: dict,
    phase8_stage: dict,
    phase9_stage: dict,
) -> dict:
    source_path = Path(source_path)
    phase7_dir = Path(phase7_dir)
    phase8_dir = Path(phase8_dir)
    phase9_dir = Path(phase9_dir)
    output_dir = Path(output_dir)
    source_contract = phase9_stage.get("source")
    if not isinstance(source_contract, dict):
        raise ValueError("Phase 10 requires the Phase 9 source contract")
    source_sha = _sha256_file(source_path)
    for phase, stage in ((7, phase7_stage), (8, phase8_stage), (9, phase9_stage)):
        if stage.get("source", {}).get("sha256") != source_sha:
            raise ValueError(f"Phase 10 source SHA must match Phase {phase}")
        if stage.get("metrics", {}).get("pass") is not True:
            raise ValueError(f"Phase 10 requires a passing Phase {phase} stage")
    if int(source_contract.get("width", 0)) != result.width or int(source_contract.get("height", 0)) != result.height:
        raise ValueError("Phase 10 source dimensions must match Phase 9")
    phase7_inputs = _verified_declared_outputs(phase7_dir, phase7_stage, consumer="Phase 7")
    phase8_inputs = _verified_declared_outputs(phase8_dir, phase8_stage, consumer="Phase 8")
    phase9_inputs = _verified_declared_outputs(phase9_dir, phase9_stage, consumer="Phase 9")
    source_image = cv2.imread(str(source_path), cv2.IMREAD_UNCHANGED)
    if source_image is None or source_image.shape[:2] != (result.height, result.width):
        raise ValueError("Phase 10 canonical source image is missing or dimensionally invalid")

    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / "10_geometry.json"
    candidate_grid_path = output_dir / "10_candidate_grid.png"
    selected_path = output_dir / "10_selected_primitives.png"
    preview_path = output_dir / "preview.png"
    metrics_path = output_dir / "metrics.json"
    stage_path = output_dir / "stage.json"
    data_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    _write_rgb_png(candidate_grid_path, render_candidate_grid(result))
    _write_rgb_png(selected_path, render_selected_primitives(result))
    shutil.copyfile(selected_path, preview_path)
    metrics = phase10_metrics(result)
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    outputs = {
        path.name: _sha256_file(path)
        for path in (data_path, candidate_grid_path, selected_path, preview_path, metrics_path)
    }
    stage = {
        "phase": 10,
        "stage": "part_aware_geometrization",
        "producer": "minimalizer-zerobase2-phase10",
        "producer_version": "1.0",
        "source": source_contract,
        "inputs": {
            "phase7": phase7_inputs,
            "phase8": phase8_inputs,
            "phase9": phase9_inputs,
            "source": {"path": source_path.name, "sha256": source_sha},
        },
        "config": config,
        "config_sha256": _canonical_json_sha256(config),
        "coordinate_space": result.to_dict()["coordinate_space"],
        "determinism_policy": "part-aware-observed-mass-geometry-v1",
        "candidate_policy": {
            "generic_region_rectangle_or_capsule": "forbidden",
            "multiple_candidates_per_active_mass": "required",
            "semantic_part_family_and_budget": "required",
            "cross_mass_candidate": "forbidden",
        },
        "selection_policy": "minimum-total-cost-then-canonical-family-order",
        "render_authority": "deterministic-source-mass-geometry-and-phase9-palette-only",
        "composition_boundary": "diagnostic-mass-id-order-only; semantic-z-order-is-phase11-authority",
        "provenance_policy": {
            "generation": "forbidden",
            "inpainting": "forbidden",
            "hidden_completion": "forbidden",
            "phase7_geometry_and_owner": "read-only",
            "phase8_actions": "read-only-no-prune-resurrection",
            "phase9_palette": "read-only",
            "candidate_geometry": "deterministic-transform-of-observed-phase7-mass",
        },
        "geometry_data": {
            "path": data_path.name,
            "sha256": outputs[data_path.name],
            "candidate_count": len(result.candidates),
            "selected_primitive_count": len(result.selected),
        },
        "metrics": metrics,
        "outputs": outputs,
    }
    stage_path.write_text(
        json.dumps(stage, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return stage
