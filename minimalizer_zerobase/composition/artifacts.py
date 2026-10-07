from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import cv2
import numpy as np

from minimalizer_zerobase.image_io import read_cv_image

from .semantic import SemanticCompositionResult, UNBOUND_PART


BACKGROUND_COLOR = (238, 238, 236)
PART_COLORS: dict[str, tuple[int, int, int]] = {
    UNBOUND_PART: (128, 128, 128),
    "head": (255, 170, 40),
    "hair": (90, 70, 180),
    "face": (240, 110, 140),
    "neck": (210, 140, 90),
    "torso": (45, 145, 210),
    "left_arm": (40, 190, 170),
    "right_arm": (20, 130, 110),
    "lower_body": (70, 95, 170),
    "major_clothing": (180, 80, 200),
    "accessory_or_held_object": (80, 190, 70),
}


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


def render_composed_minimal(result: SemanticCompositionResult) -> np.ndarray:
    canvas = np.full((result.height, result.width, 3), BACKGROUND_COLOR, dtype=np.uint8)
    for item in result.primitives:
        mask = result.primitive_masks[item["primitive_id"]]
        canvas[mask] = np.asarray(item["palette_color_rgb"], dtype=np.uint8)
    return canvas


def render_zorder_overlay(result: SemanticCompositionResult) -> np.ndarray:
    canvas = render_composed_minimal(result)
    part_masks: dict[str, np.ndarray] = {}
    for item in result.primitives:
        part = item["composition_part"]
        part_masks.setdefault(part, np.zeros((result.height, result.width), dtype=bool))
        part_masks[part] |= result.primitive_masks[item["primitive_id"]]
    for order, part in enumerate(result.part_raster_order):
        mask = part_masks[part]
        color = np.asarray(PART_COLORS.get(part, (30, 30, 30)), dtype=np.uint8)
        canvas[_outline(mask)] = color
        ys, xs = np.where(mask)
        if len(xs):
            x = max(2, min(result.width - 42, int(round(float(xs.mean()))) - 10))
            y = max(12, min(result.height - 3, int(round(float(ys.mean())))))
            cv2.putText(
                canvas,
                f"{order}:{part[:4]}",
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.30,
                tuple(int(value) for value in color),
                1,
                cv2.LINE_8,
            )
    return canvas


def phase11_metrics(result: SemanticCompositionResult) -> dict:
    return dict(result.validation)


def _verified_declared_outputs(
    phase_dir: Path, stage: dict, *, consumer: str
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


def write_phase11_artifacts(
    source_path: str | Path,
    phase5_dir: str | Path,
    phase10_dir: str | Path,
    result: SemanticCompositionResult,
    output_dir: str | Path,
    *,
    config: dict,
    phase5_stage: dict,
    phase10_stage: dict,
) -> dict:
    source_path = Path(source_path)
    phase5_dir = Path(phase5_dir)
    phase10_dir = Path(phase10_dir)
    output_dir = Path(output_dir)
    source_contract = phase10_stage.get("source")
    if not isinstance(source_contract, dict):
        raise ValueError("Phase 11 requires the Phase 10 source contract")
    source_sha = _sha256_file(source_path)
    for phase, stage in ((5, phase5_stage), (10, phase10_stage)):
        if stage.get("source", {}).get("sha256") != source_sha:
            raise ValueError(f"Phase 11 source SHA must match Phase {phase}")
        if stage.get("metrics", {}).get("pass") is not True:
            raise ValueError(f"Phase 11 requires a passing Phase {phase} stage")
    if (
        int(source_contract.get("width", 0)) != result.width
        or int(source_contract.get("height", 0)) != result.height
    ):
        raise ValueError("Phase 11 source dimensions must match Phase 10")
    phase5_inputs = _verified_declared_outputs(
        phase5_dir, phase5_stage, consumer="Phase 5"
    )
    phase10_inputs = _verified_declared_outputs(
        phase10_dir, phase10_stage, consumer="Phase 10"
    )
    source_image = read_cv_image(source_path, cv2.IMREAD_UNCHANGED)
    if source_image is None or source_image.shape[:2] != (result.height, result.width):
        raise ValueError("Phase 11 canonical source image is missing or dimensionally invalid")

    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / "11_composition.json"
    composed_path = output_dir / "11_composed_minimal.png"
    overlay_path = output_dir / "11_zorder_overlay.png"
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
    _write_rgb_png(composed_path, render_composed_minimal(result))
    _write_rgb_png(overlay_path, render_zorder_overlay(result))
    shutil.copyfile(composed_path, preview_path)
    metrics = phase11_metrics(result)
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    outputs = {
        path.name: _sha256_file(path)
        for path in (data_path, composed_path, overlay_path, preview_path, metrics_path)
    }
    stage = {
        "phase": 11,
        "stage": "semantic_composition",
        "producer": "minimalizer-zerobase2-phase11",
        "producer_version": "1.1",
        "source": source_contract,
        "inputs": {
            "phase5": phase5_inputs,
            "phase10": phase10_inputs,
            "source": {"path": source_path.name, "sha256": source_sha},
        },
        "config": config,
        "config_sha256": _canonical_json_sha256(config),
        "coordinate_space": result.to_dict()["coordinate_space"],
        "determinism_policy": "explicit-depth-graph-then-per-pixel-visual-raster-tiebreak-v2",
        "composition_policy": {
            "z_order_authority": "phase5-semantic-graph",
            "explicit_occlusion_relations": ["in_front_of", "behind"],
            "non_depth_relations_as_z_order": "forbidden",
            "unresolved_depth": "preserved-with-non-semantic-raster-tie-break",
            "raster_tie_break": "per-pixel-phase10-mask-and-phase9-color-raster-v2",
            "semantic_identifier_visual_authority": "forbidden",
            "identifier_serialization_tie": "exactly-identical-per-pixel-raster-only",
            "region_id_only_order": "forbidden",
            "mass_id_only_order": "forbidden",
        },
        "upstream_immutability": {
            "phase10_selected_geometry": "read-only",
            "phase10_semantic_owner": "read-only",
            "phase8_prune": "transitively-read-only-via-phase10",
            "phase9_palette": "transitively-read-only-via-phase10",
        },
        "render_authority": "deterministic-phase10-selected-geometry-and-palette-only",
        "provenance_policy": {
            "generation": "forbidden",
            "inpainting": "forbidden",
            "hidden_completion": "forbidden",
        },
        "composition_data": {
            "path": data_path.name,
            "sha256": outputs[data_path.name],
            "selected_primitive_count": len(result.primitives),
            "applied_graph_edge_count": len(result.applied_graph_edges),
        },
        "metrics": metrics,
        "outputs": outputs,
    }
    stage_path.write_text(
        json.dumps(stage, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return stage
