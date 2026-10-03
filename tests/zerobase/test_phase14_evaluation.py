from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

from minimalizer_zerobase.evaluation import (
    build_phase14_corpus_summary,
    evaluate_phase14_case,
    write_phase14_artifacts,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _polygon(
    primitive_id: str,
    part: str,
    color: tuple[int, int, int],
    points: list[list[float]],
    order: int,
) -> dict:
    return {
        "primitive_id": primitive_id,
        "primitive_type": "polygon",
        "parameters": {
            "components": [points],
            "corner_radius_px": 0,
        },
        "composition_part": part,
        "semantic_part_id": part,
        "binding_status": "bound",
        "palette_color_rgb": list(color),
        "raster_index": order,
    }


def _mask_from_points(
    shape: tuple[int, int],
    points: list[list[float]],
) -> np.ndarray:
    image = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(image).polygon(
        [(int(x), int(y)) for x, y in points],
        fill=255,
    )
    return np.asarray(image) > 0


def _make_case(tmp_path: Path) -> tuple[Path, Path]:
    case = tmp_path / "case"
    phase3 = case / "phase_03"
    phase4 = case / "phase_04" / "part_masks"
    phase12 = case / "phase_12"
    phase13 = case / "phase_13"
    for directory in (phase3, phase4, phase12, phase13):
        directory.mkdir(parents=True, exist_ok=True)

    shape = (100, 100)
    primitives = [
        _polygon(
            "hair",
            "hair",
            (70, 60, 65),
            [[25, 8], [65, 8], [72, 36], [22, 38]],
            0,
        ),
        _polygon(
            "face",
            "face",
            (235, 215, 210),
            [[36, 20], [58, 20], [63, 40], [54, 51], [38, 48], [32, 35]],
            1,
        ),
        _polygon(
            "torso",
            "torso",
            (60, 62, 68),
            [[30, 50], [66, 50], [72, 88], [24, 88]],
            2,
        ),
        _polygon(
            "accessory",
            "accessory_or_held_object",
            (175, 90, 70),
            [[45, 52], [51, 52], [53, 77], [47, 83], [43, 74]],
            3,
        ),
    ]

    colors = {
        "hair": (70, 60, 65),
        "face": (235, 215, 210),
        "torso": (60, 62, 68),
        "accessory_or_held_object": (175, 90, 70),
    }
    source = np.zeros((*shape, 3), dtype=np.uint8)
    source[:] = (245, 245, 245)
    subject = np.zeros(shape, dtype=bool)
    part_pixels: dict[str, int] = {}
    for primitive in primitives:
        points = primitive["parameters"]["components"][0]
        mask = _mask_from_points(shape, points)
        part = primitive["composition_part"]
        subject |= mask
        source[mask] = colors[part]
        part_pixels[part] = int(mask.sum())
        Image.fromarray((mask.astype(np.uint8) * 255)).save(
            phase4 / f"{part}.png"
        )

    source_path = tmp_path / "source.png"
    Image.fromarray(source).save(source_path)
    Image.fromarray((subject.astype(np.uint8) * 255)).save(
        phase3 / "03_subject_mask.png"
    )

    part_metrics = {
        part: {
            "baseline_pixels": pixels,
            "candidate_pixels": pixels,
            "intersection_pixels": pixels,
            "union_pixels": pixels,
            "iou": 1.0,
            "recall": 1.0,
        }
        for part, pixels in part_pixels.items()
    }
    selected = {
        "name": "conservative",
        "primitives": primitives,
        "metrics": {
            "pass": True,
            "profile": "conservative",
            "baseline_primitive_count": 8,
            "primitive_count": 4,
            "primitive_reduction": 4,
            "silhouette_iou": 0.99,
            "baseline_vertex_count": 64,
            "vertex_count": 20,
            "vertex_reduction": 44,
            "part_metrics": part_metrics,
            "critical_part_failures": [],
            "critical_part_iou_failures": [],
            "missing_visible_parts": [],
            "removed_micro_component_count": 0,
        },
    }
    phase12_payload = {
        "schema_version": "1.0",
        "coordinate_space": {
            "pixel_width": 100,
            "pixel_height": 100,
            "normalized_origin": "top-left",
            "normalized_range": [0.0, 1.0],
        },
        "selected_name": "conservative",
        "candidates": [selected],
        "validation": {
            "pass": True,
            "selection_rule": (
                "fewest-primitives-then-highest-silhouette-"
                "then-fewest-vertices"
            ),
        },
    }
    (phase12 / "12_simplification.json").write_text(
        json.dumps(phase12_payload),
        encoding="utf-8",
    )
    Image.fromarray(source).save(phase12 / "12_final.png")

    phase13_index = {
        "schema_version": "1.0",
        "phase": 13,
        "case_id": "case",
        "first_machine_bad_stage_id": None,
        "human_review": {
            "status": "pass",
            "first_bad_stage_id": None,
            "note": "fixture visual pass",
        },
    }
    (phase13 / "13_stage_index.json").write_text(
        json.dumps(phase13_index),
        encoding="utf-8",
    )
    Image.fromarray(source).save(phase13 / "13_debug_board.png")

    source_contract = {
        "path": source_path.name,
        "sha256": _sha(source_path),
        "width": 100,
        "height": 100,
    }
    coordinate_space = phase12_payload["coordinate_space"]
    phase4_outputs = {
        f"part_masks/{path.name}": _sha(path)
        for path in phase4.glob("*.png")
    }
    phase4_stage = {
        "phase": 4,
        "source": source_contract,
        "outputs": phase4_outputs,
    }
    (case / "phase_04" / "stage.json").write_text(
        json.dumps(phase4_stage),
        encoding="utf-8",
    )

    phase12_stage = {
        "phase": 12,
        "source": source_contract,
        "coordinate_space": coordinate_space,
        "outputs": {
            "12_simplification.json": _sha(
                phase12 / "12_simplification.json"
            ),
            "12_final.png": _sha(phase12 / "12_final.png"),
        },
    }
    (phase12 / "stage.json").write_text(
        json.dumps(phase12_stage),
        encoding="utf-8",
    )
    phase13_stage = {
        "phase": 13,
        "source": source_contract,
        "coordinate_space": coordinate_space,
        "metrics": {"pass": True},
        "outputs": {
            "13_stage_index.json": _sha(
                phase13 / "13_stage_index.json"
            ),
            "13_debug_board.png": _sha(
                phase13 / "13_debug_board.png"
            ),
        },
    }
    (phase13 / "stage.json").write_text(
        json.dumps(phase13_stage),
        encoding="utf-8",
    )
    return case, source_path


def test_phase14_machine_human_and_determinism_pass(tmp_path: Path) -> None:
    case, source = _make_case(tmp_path)

    result = evaluate_phase14_case(
        case,
        source,
        human_status="pass",
        reviewer="fixture",
        human_note="visual pass",
    )

    assert result["pass"] is True
    assert result["machine_pass"] is True
    assert result["human_visual_qa"]["passed"] is True
    assert result["determinism"]["passed"] is True
    assert result["scores"]["silhouette_preservation"] == 0.99
    assert result["scores"]["part_layout_consistency_mean"] > 0.99
    assert result["scores"]["identity_feature_retention"] == 1.0


def test_phase14_human_fail_overrides_numeric_pass(tmp_path: Path) -> None:
    case, source = _make_case(tmp_path)

    result = evaluate_phase14_case(
        case,
        source,
        human_status="fail",
        failed_criteria=("same_subject_recognizability",),
        reviewer="fixture",
    )

    assert result["machine_pass"] is True
    assert result["human_visual_qa"]["passed"] is False
    assert result["pass"] is False
    assert (
        result["human_visual_qa"]["criteria"][
            "same_subject_recognizability"
        ]
        is False
    )


def test_phase14_writer_creates_case_contract_and_sheet(tmp_path: Path) -> None:
    case, source = _make_case(tmp_path)
    out = case / "phase_14"

    stage = write_phase14_artifacts(
        source,
        case,
        out,
        human_status="pass",
        reviewer="fixture",
    )

    assert stage["metrics"]["pass"] is True
    assert stage["metrics"]["determinism_pass"] is True
    for name in (
        "14_case_evaluation.json",
        "14_eval_sheet.png",
        "preview.png",
        "metrics.json",
        "stage.json",
    ):
        assert (out / name).is_file()
    evaluation = json.loads(
        (out / "14_case_evaluation.json").read_text(encoding="utf-8")
    )
    assert evaluation["human_visual_qa"]["passed"] is True
    assert evaluation["determinism"]["passed"] is True


def test_phase14_corpus_summary_is_fail_closed() -> None:
    base = {
        "case_id": "a",
        "pass": True,
        "scores": {
            "silhouette_preservation": 0.98,
            "part_layout_consistency_mean": 0.90,
            "part_layout_consistency_min": 0.70,
            "major_color_mass_consistency": 0.75,
            "identity_feature_retention": 0.95,
            "oversized_block_penalty": 0.0,
            "fragmentation_penalty": 0.02,
            "primitive_economy": 0.40,
        },
        "human_visual_qa": {"passed": True},
        "determinism": {"passed": True},
    }
    failed = json.loads(json.dumps(base))
    failed["case_id"] = "b"
    failed["pass"] = False
    failed["human_visual_qa"]["passed"] = False

    summary = build_phase14_corpus_summary(
        (base, failed),
        corpus_name="fixture",
        required_case_count=2,
    )

    assert summary["pass"] is False
    assert summary["pass_count"] == 1
    assert summary["failing_cases"] == ["b"]
    with pytest.raises(ValueError, match="requires 3 cases"):
        build_phase14_corpus_summary(
            (base, failed),
            corpus_name="fixture",
            required_case_count=3,
        )


def test_phase14_corpus_rejects_duplicate_case_ids() -> None:
    case = {
        "case_id": "same",
        "pass": True,
        "scores": {
            "silhouette_preservation": 0.98,
            "part_layout_consistency_mean": 0.90,
            "part_layout_consistency_min": 0.70,
            "major_color_mass_consistency": 0.75,
            "identity_feature_retention": 0.95,
            "oversized_block_penalty": 0.0,
            "fragmentation_penalty": 0.02,
            "primitive_economy": 0.40,
        },
        "human_visual_qa": {"passed": True},
        "determinism": {"passed": True},
    }
    with pytest.raises(ValueError, match="duplicate"):
        build_phase14_corpus_summary(
            (case, case),
            corpus_name="fixture",
        )
