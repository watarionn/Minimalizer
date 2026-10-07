from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from minimalizer_zerobase.composition.artifacts import BACKGROUND_COLOR

from .style import SimplificationCandidate, StyleSimplificationResult


def _sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json_sha256(payload: dict[str, Any]) -> str:
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


def _render(
    *,
    width: int,
    height: int,
    primitives: tuple[dict[str, Any], ...],
    masks: dict[str, np.ndarray],
) -> np.ndarray:
    canvas = np.full((height, width, 3), BACKGROUND_COLOR, dtype=np.uint8)
    for item in primitives:
        primitive_id = str(item["primitive_id"])
        canvas[masks[primitive_id]] = np.asarray(
            item["palette_color_rgb"], dtype=np.uint8
        )
    return canvas


def _baseline_render(result: StyleSimplificationResult) -> np.ndarray:
    return _render(
        width=result.width,
        height=result.height,
        primitives=result.baseline_primitives,
        masks=result.baseline_masks,
    )


def _candidate_render(
    result: StyleSimplificationResult, candidate: SimplificationCandidate
) -> np.ndarray:
    return _render(
        width=result.width,
        height=result.height,
        primitives=candidate.primitives,
        masks=candidate.primitive_masks,
    )


def _silhouette(masks: dict[str, np.ndarray], shape: tuple[int, int]) -> np.ndarray:
    out = np.zeros(shape, dtype=bool)
    for mask in masks.values():
        out |= mask
    return out


def _removed_overlay(
    result: StyleSimplificationResult, candidate: SimplificationCandidate | None
) -> np.ndarray:
    canvas = _baseline_render(result)
    if candidate is None:
        return canvas
    baseline = _silhouette(result.baseline_masks, (result.height, result.width))
    final = _silhouette(candidate.primitive_masks, (result.height, result.width))
    removed = baseline & ~final
    added = final & ~baseline
    canvas[removed] = np.asarray((255, 40, 40), dtype=np.uint8)
    canvas[added] = np.asarray((40, 120, 255), dtype=np.uint8)
    return canvas


def _verified_phase4_inputs(
    phase4_dir: Path, phase4_stage: dict[str, Any]
) -> dict[str, str]:
    outputs = phase4_stage.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        raise ValueError("Phase 12 structural repair requires declared Phase 4 outputs")
    verified: dict[str, str] = {}
    for name, expected_sha in sorted(outputs.items()):
        if not name.startswith("part_masks/"):
            continue
        path = phase4_dir / name
        if not path.is_file() or _sha256_file(path) != expected_sha:
            raise ValueError(f"Phase 12 Phase 4 input SHA mismatch: {name}")
        verified[name] = expected_sha
    if not verified:
        raise ValueError("Phase 12 structural repair requires Phase 4 part masks")
    verified["stage.json"] = _sha256_file(phase4_dir / "stage.json")
    return verified


def _verified_phase11_inputs(
    phase11_dir: Path, phase11_stage: dict[str, Any]
) -> dict[str, str]:
    outputs = phase11_stage.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        raise ValueError("Phase 12 requires declared Phase 11 outputs")
    verified: dict[str, str] = {}
    for name, expected_sha in sorted(outputs.items()):
        path = phase11_dir / name
        if not path.is_file() or _sha256_file(path) != expected_sha:
            raise ValueError(f"Phase 12 Phase 11 input SHA mismatch: {name}")
        verified[name] = expected_sha
    verified["stage.json"] = _sha256_file(phase11_dir / "stage.json")
    return verified


def write_phase12_artifacts(
    source_path: str | Path,
    phase11_dir: str | Path,
    result: StyleSimplificationResult,
    output_dir: str | Path,
    *,
    config: dict[str, Any],
    phase11_stage: dict[str, Any],
    phase4_dir: str | Path | None = None,
    phase4_stage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_path = Path(source_path)
    phase11_dir = Path(phase11_dir)
    phase4_dir = Path(phase4_dir) if phase4_dir is not None else None
    output_dir = Path(output_dir)
    source_contract = phase11_stage.get("source")
    if not isinstance(source_contract, dict):
        raise ValueError("Phase 12 requires the Phase 11 source contract")
    source_sha = _sha256_file(source_path)
    if source_contract.get("sha256") != source_sha:
        raise ValueError("Phase 12 source SHA must match Phase 11")
    if phase11_stage.get("metrics", {}).get("pass") is not True:
        raise ValueError("Phase 12 requires a passing Phase 11 stage")
    if (
        int(source_contract.get("width", 0)) != result.width
        or int(source_contract.get("height", 0)) != result.height
    ):
        raise ValueError("Phase 12 source dimensions must match Phase 11")
    source_image = cv2.imread(str(source_path), cv2.IMREAD_UNCHANGED)
    if source_image is None or source_image.shape[:2] != (result.height, result.width):
        raise ValueError("Phase 12 canonical source is missing or dimensionally invalid")
    phase11_inputs = _verified_phase11_inputs(phase11_dir, phase11_stage)
    phase4_inputs = None
    if phase4_dir is not None or phase4_stage is not None:
        if phase4_dir is None or phase4_stage is None:
            raise ValueError("Phase 12 Phase 4 structural input requires dir and stage")
        if phase4_stage.get("source", {}).get("sha256") != source_sha:
            raise ValueError("Phase 12 source SHA must match Phase 4")
        phase4_inputs = _verified_phase4_inputs(phase4_dir, phase4_stage)

    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / "12_simplification.json"
    before_path = output_dir / "12_before.png"
    conservative_path = output_dir / "12_candidate_conservative.png"
    aggressive_path = output_dir / "12_candidate_aggressive.png"
    final_path = output_dir / "12_final.png"
    removed_path = output_dir / "12_removed_shapes_overlay.png"
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
    _write_rgb_png(before_path, _baseline_render(result))
    by_name = {item.name: item for item in result.candidates}
    _write_rgb_png(
        conservative_path,
        _candidate_render(result, by_name["conservative"]),
    )
    _write_rgb_png(
        aggressive_path,
        _candidate_render(result, by_name["aggressive"]),
    )
    selected = result.selected
    final_rgb = (
        _candidate_render(result, selected)
        if selected is not None
        else _baseline_render(result)
    )
    _write_rgb_png(final_path, final_rgb)
    _write_rgb_png(removed_path, _removed_overlay(result, selected))
    shutil.copyfile(final_path, preview_path)
    metrics_path.write_text(
        json.dumps(result.validation, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    outputs = {
        path.name: _sha256_file(path)
        for path in (
            data_path,
            before_path,
            conservative_path,
            aggressive_path,
            final_path,
            removed_path,
            preview_path,
            metrics_path,
        )
    }
    stage = {
        "phase": 12,
        "stage": "style_constraint_simplification",
        "producer": "minimalizer-zerobase2-phase12",
        "producer_version": "0.1",
        "source": source_contract,
        "inputs": {
            **({"phase4": phase4_inputs} if phase4_inputs is not None else {}),
            "phase11": phase11_inputs,
        },
        "config": config,
        "config_sha256": _canonical_json_sha256(config),
        "coordinate_space": result.to_dict()["coordinate_space"],
        "determinism_policy": "part-plus-rgb-grouping-connected-components-fixed-profile-selection",
        "upstream_immutability": {
            "phase11_semantic_owner": "read-only",
            "phase11_palette_color": "read-only-per-group",
            "phase11_part_order": "read-only",
        },
        "simplification_policy": {
            "candidate_profiles": ["conservative", "aggressive"],
            "human_visual_gate_required": True,
            "silent_fallback_to_production": False,
        },
        "provenance_policy": {
            "generation": "forbidden",
            "inpainting": "forbidden",
            "hidden_completion": "forbidden",
            "structural_source_repair": "phase04-part-masks-only-when-bound",
        },
        "metrics": result.validation,
        "outputs": outputs,
    }
    stage_path.write_text(
        json.dumps(stage, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return stage
