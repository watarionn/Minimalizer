from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
import cv2
import numpy as np

from minimalizer_zerobase.artifact_contract import (
    ArtifactOrigin,
    StageContractBridgeError,
    bridge_stage_contracts,
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _config_sha(config: dict) -> str:
    raw = json.dumps(
        config,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _write_stage(path: Path, payload: dict) -> str:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return _sha256_file(path)


def _write_output(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return _sha256_file(path)


def _base_stage(
    *,
    phase: int,
    stage_name: str,
    source: dict,
    config: dict,
    outputs: dict[str, str],
    inputs: dict | None = None,
) -> dict:
    stage = {
        "phase": phase,
        "stage": stage_name,
        "producer": f"test-phase{phase}",
        "producer_version": "1.0",
        "source": source,
        "config": config,
        "config_sha256": _config_sha(config),
        "outputs": outputs,
    }
    if inputs is not None:
        stage["inputs"] = inputs
    return stage


def _make_case(tmp_path: Path) -> tuple[Path, Path]:
    source_path = tmp_path / "source.png"
    assert cv2.imwrite(
        str(source_path),
        np.full((6, 8, 3), (40, 80, 120), dtype=np.uint8),
    )
    source = {
        "path": source_path.name,
        "sha256": _sha256_file(source_path),
        "width": 8,
        "height": 6,
    }

    case_dir = tmp_path / "case-a"
    phase3 = case_dir / "phase_03"
    phase4 = case_dir / "phase_04"
    phase5 = case_dir / "phase_05"
    phase6 = case_dir / "phase_06"
    for directory in (phase3, phase4, phase5, phase6):
        directory.mkdir(parents=True)

    phase3_mask_sha = _write_output(
        phase3 / "03_subject_mask.png",
        b"phase3-mask",
    )
    phase3_metrics_sha = _write_output(
        phase3 / "metrics.json",
        b'{"phase":3}\n',
    )
    stage3 = _base_stage(
        phase=3,
        stage_name="canonical_subject_extraction",
        source=source,
        config={"threshold": 0.5},
        outputs={
            "03_subject_mask.png": phase3_mask_sha,
            "metrics.json": phase3_metrics_sha,
        },
    )
    stage3_sha = _write_stage(phase3 / "stage.json", stage3)


    face_sha = _write_output(
        phase4 / "part_masks" / "face.png",
        b"phase4-face-mask",
    )
    phase4_metrics_sha = _write_output(
        phase4 / "metrics.json",
        b'{"phase":4}\n',
    )
    stage4 = _base_stage(
        phase=4,
        stage_name="semantic_part_decomposition",
        source=source,
        config={"parts": "test"},
        inputs={
            "phase3": {
                "03_subject_mask.png": phase3_mask_sha,
                "stage.json": stage3_sha,
            },
        },
        outputs={
            "part_masks/face.png": face_sha,
            "metrics.json": phase4_metrics_sha,
        },
    )
    stage4_sha = _write_stage(phase4 / "stage.json", stage4)

    graph_sha = _write_output(
        phase5 / "05_structure_graph.json",
        b'{"graph":"ok"}\n',
    )
    stage5 = _base_stage(
        phase=5,
        stage_name="structural_layout_graph",
        source=source,
        config={"graph": "test"},
        inputs={
            "phase4": {
                "part_masks/face.png": face_sha,
                "stage.json": stage4_sha,
            },
            "visual_source": {
                "path": source_path.name,
                "sha256": source["sha256"],
                "kind": "canonical-source",
            },
        },
        outputs={
            "05_structure_graph.json": graph_sha,
        },
    )
    stage5_sha = _write_stage(phase5 / "stage.json", stage5)


    binding_sha = _write_output(
        phase6 / "06_region_bindings.json",
        b'{"bindings":"ok"}\n',
    )
    stage6 = _base_stage(
        phase=6,
        stage_name="region_to_part_binding",
        source=source,
        config={"binding": "test"},
        inputs={
            "phase4": {
                "part_masks/face.png": face_sha,
                "stage.json": stage4_sha,
            },
            "phase5": {
                "05_structure_graph.json": graph_sha,
                "stage.json": stage5_sha,
            },
            "source": {
                "path": source_path.name,
                "sha256": source["sha256"],
            },
        },
        outputs={
            "06_region_bindings.json": binding_sha,
        },
    )
    _write_stage(phase6 / "stage.json", stage6)
    return case_dir, source_path


def _load_stage(case_dir: Path, phase: int) -> dict:
    return json.loads(
        (case_dir / f"phase_{phase:02d}" / "stage.json").read_text(
            encoding="utf-8"
        )
    )


def test_bridge_builds_verified_graph_and_deterministic_bundle(
    tmp_path: Path,
) -> None:
    case_dir, source_path = _make_case(tmp_path)
    first_dir = tmp_path / "bridge-a"
    second_dir = tmp_path / "bridge-b"

    first = bridge_stage_contracts(
        case_dir,
        source_path,
        output_dir=first_dir,
    )
    source_copy = tmp_path / "source-copy.png"
    shutil.copyfile(source_path, source_copy)
    second = bridge_stage_contracts(
        case_dir,
        source_copy,
        output_dir=second_dir,
    )

    assert first.gate_result.passed is True
    assert first.run_manifest.run_id == "case-a:phase03-06"
    assert len(first.run_manifest.stage_manifest_refs) == 4
    assert first.bundle.run_manifest_sha256 == second.bundle.run_manifest_sha256
    assert (
        first.bundle.artifact_manifest_sha256
        == second.bundle.artifact_manifest_sha256
    )
    assert (first_dir / "run.json").read_bytes() == (
        second_dir / "run.json"
    ).read_bytes()
    assert (first_dir / "artifacts.json").read_bytes() == (
        second_dir / "artifacts.json"
    ).read_bytes()


    by_id = {record.artifact_id: record for record in first.artifacts}
    assert by_id["source"].origin == ArtifactOrigin.SOURCE_PIXEL
    assert by_id["phase03:03_subject_mask.png"].origin == ArtifactOrigin.ANALYTICAL
    assert (
        by_id["phase05:05_structure_graph.json"].origin
        == ArtifactOrigin.SEMANTIC_METADATA
    )
    phase4_parents = {
        parent.artifact_id
        for parent in by_id["phase04:part_masks/face.png"].parents
    }
    assert phase4_parents == {
        "phase03:03_subject_mask.png",
        "phase03:stage.json",
    }


def test_bridge_rejects_modified_declared_output(tmp_path: Path) -> None:
    case_dir, source_path = _make_case(tmp_path)
    target = case_dir / "phase_06" / "06_region_bindings.json"
    target.write_bytes(b"tampered")
    with pytest.raises(
        StageContractBridgeError,
        match="Phase 6 output SHA mismatch",
    ):
        bridge_stage_contracts(case_dir, source_path)


def test_bridge_rejects_upstream_input_hash_mismatch(tmp_path: Path) -> None:
    case_dir, source_path = _make_case(tmp_path)
    stage_path = case_dir / "phase_06" / "stage.json"
    stage = _load_stage(case_dir, 6)
    stage["inputs"]["phase5"]["05_structure_graph.json"] = "f" * 64
    _write_stage(stage_path, stage)
    with pytest.raises(
        StageContractBridgeError,
        match="Phase 6 input SHA mismatch",
    ):
        bridge_stage_contracts(case_dir, source_path)


def test_bridge_rejects_source_replacement(tmp_path: Path) -> None:
    case_dir, source_path = _make_case(tmp_path)
    assert cv2.imwrite(
        str(source_path),
        np.zeros((6, 8, 3), dtype=np.uint8),
    )
    with pytest.raises(
        StageContractBridgeError,
        match="source file SHA does not match",
    ):
        bridge_stage_contracts(case_dir, source_path)


def test_bridge_rejects_config_hash_mismatch(tmp_path: Path) -> None:
    case_dir, source_path = _make_case(tmp_path)
    stage_path = case_dir / "phase_06" / "stage.json"
    stage = _load_stage(case_dir, 6)
    stage["config"]["binding"] = "tampered"
    _write_stage(stage_path, stage)
    with pytest.raises(
        StageContractBridgeError,
        match="Phase 6 config SHA mismatch",
    ):
        bridge_stage_contracts(case_dir, source_path)


@pytest.mark.parametrize(
    "unsafe_path",
    ("../escape.png", "/escape.png", "C:/escape.png"),
)
def test_bridge_rejects_unsafe_declared_output_path(
    tmp_path: Path,
    unsafe_path: str,
) -> None:
    case_dir, source_path = _make_case(tmp_path)
    stage_path = case_dir / "phase_03" / "stage.json"
    stage = _load_stage(case_dir, 3)
    stage["outputs"][unsafe_path] = "0" * 64
    _write_stage(stage_path, stage)
    with pytest.raises(
        StageContractBridgeError,
        match="unsafe stage artifact path",
    ):
        bridge_stage_contracts(case_dir, source_path)


def _add_phase7(case_dir: Path, source_path: Path) -> None:
    phase6 = case_dir / "phase_06"
    phase7 = case_dir / "phase_07"
    phase7.mkdir()
    source = _load_stage(case_dir, 6)["source"]
    binding_sha = _sha256_file(phase6 / "06_region_bindings.json")
    stage6_sha = _sha256_file(phase6 / "stage.json")
    masses_sha = _write_output(
        phase7 / "07_masses.json",
        b'{"masses":"ok"}\n',
    )
    labels_sha = _write_output(
        phase7 / "07_mass_labels.png",
        b"phase7-labels",
    )
    stage7 = _base_stage(
        phase=7,
        stage_name="major_mass_reconstruction",
        source=source,
        config={"minimum_shared_boundary_pixels": 1},
        inputs={
            "phase6": {
                "06_region_bindings.json": binding_sha,
                "stage.json": stage6_sha,
            },
            "source": {
                "path": source_path.name,
                "sha256": source["sha256"],
            },
        },
        outputs={
            "07_masses.json": masses_sha,
            "07_mass_labels.png": labels_sha,
        },
    )
    _write_stage(phase7 / "stage.json", stage7)


def test_bridge_can_extend_verified_chain_through_phase7(tmp_path: Path) -> None:
    case_dir, source_path = _make_case(tmp_path)
    _add_phase7(case_dir, source_path)

    result = bridge_stage_contracts(
        case_dir,
        source_path,
        output_dir=tmp_path / "bridge-phase7",
        max_phase=7,
    )

    assert result.gate_result.passed is True
    assert result.run_manifest.run_id == "case-a:phase03-07"
    assert len(result.run_manifest.stage_manifest_refs) == 5
    by_id = {record.artifact_id: record for record in result.artifacts}
    masses = by_id["phase07:07_masses.json"]
    assert masses.artifact_type == "semantic-mass-data"
    assert {parent.artifact_id for parent in masses.parents} == {
        "phase06:06_region_bindings.json",
        "phase06:stage.json",
        "source",
    }


def test_bridge_phase7_fails_closed_when_phase7_stage_is_missing(
    tmp_path: Path,
) -> None:
    case_dir, source_path = _make_case(tmp_path)
    with pytest.raises(StageContractBridgeError, match="missing Phase 7"):
        bridge_stage_contracts(
            case_dir,
            source_path,
            max_phase=7,
        )


def _add_phase8(case_dir: Path, source_path: Path) -> None:
    phase7 = case_dir / "phase_07"
    phase8 = case_dir / "phase_08"
    phase8.mkdir()
    source = _load_stage(case_dir, 7)["source"]
    stage7 = _load_stage(case_dir, 7)
    importance_sha = _write_output(
        phase8 / "08_importance.json",
        b'{"decisions":"ok"}\n',
    )
    heatmap_sha = _write_output(
        phase8 / "08_importance_heatmap.png",
        b"phase8-heatmap",
    )
    stage8 = _base_stage(
        phase=8,
        stage_name="importance_omission_policy",
        source=source,
        config={"policy": "test"},
        inputs={
            "phase7": {
                "07_masses.json": stage7["outputs"]["07_masses.json"],
                "07_mass_labels.png": stage7["outputs"]["07_mass_labels.png"],
                "stage.json": _sha256_file(phase7 / "stage.json"),
            },
            "source": {
                "path": source_path.name,
                "sha256": source["sha256"],
            },
        },
        outputs={
            "08_importance.json": importance_sha,
            "08_importance_heatmap.png": heatmap_sha,
        },
    )
    _write_stage(phase8 / "stage.json", stage8)


def test_bridge_can_extend_verified_chain_through_phase8(tmp_path: Path) -> None:
    case_dir, source_path = _make_case(tmp_path)
    _add_phase7(case_dir, source_path)
    _add_phase8(case_dir, source_path)

    result = bridge_stage_contracts(
        case_dir,
        source_path,
        output_dir=tmp_path / "bridge-phase8",
        max_phase=8,
    )

    assert result.gate_result.passed is True
    assert result.run_manifest.run_id == "case-a:phase03-08"
    assert len(result.run_manifest.stage_manifest_refs) == 6
    by_id = {record.artifact_id: record for record in result.artifacts}
    importance = by_id["phase08:08_importance.json"]
    assert importance.artifact_type == "importance-omission-data"
    assert {parent.artifact_id for parent in importance.parents} == {
        "phase07:07_masses.json",
        "phase07:07_mass_labels.png",
        "phase07:stage.json",
        "source",
    }


def _add_phase9(case_dir: Path, source_path: Path) -> None:
    phase7 = case_dir / "phase_07"
    phase8 = case_dir / "phase_08"
    phase9 = case_dir / "phase_09"
    phase9.mkdir()
    source = _load_stage(case_dir, 8)["source"]
    stage7 = _load_stage(case_dir, 7)
    stage8 = _load_stage(case_dir, 8)
    palette_sha = _write_output(
        phase9 / "09_palette.json",
        b'{"palette":"ok"}\n',
    )
    preview_sha = _write_output(
        phase9 / "09_palette_preview.png",
        b"phase9-preview",
    )
    strip_sha = _write_output(
        phase9 / "09_palette_strip.png",
        b"phase9-strip",
    )
    stage9 = _base_stage(
        phase=9,
        stage_name="palette_consolidation",
        source=source,
        config={"palette": "test"},
        inputs={
            "phase7": {
                "07_masses.json": stage7["outputs"]["07_masses.json"],
                "07_mass_labels.png": stage7["outputs"]["07_mass_labels.png"],
                "stage.json": _sha256_file(phase7 / "stage.json"),
            },
            "phase8": {
                "08_importance.json": stage8["outputs"]["08_importance.json"],
                "08_importance_heatmap.png": stage8["outputs"]["08_importance_heatmap.png"],
                "stage.json": _sha256_file(phase8 / "stage.json"),
            },
            "source": {
                "path": source_path.name,
                "sha256": source["sha256"],
            },
        },
        outputs={
            "09_palette.json": palette_sha,
            "09_palette_preview.png": preview_sha,
            "09_palette_strip.png": strip_sha,
        },
    )
    _write_stage(phase9 / "stage.json", stage9)


def test_bridge_can_extend_verified_chain_through_phase9(tmp_path: Path) -> None:
    case_dir, source_path = _make_case(tmp_path)
    _add_phase7(case_dir, source_path)
    _add_phase8(case_dir, source_path)
    _add_phase9(case_dir, source_path)

    result = bridge_stage_contracts(
        case_dir,
        source_path,
        output_dir=tmp_path / "bridge-phase9",
        max_phase=9,
    )

    assert result.gate_result.passed is True
    assert result.run_manifest.run_id == "case-a:phase03-09"
    assert len(result.run_manifest.stage_manifest_refs) == 7
    by_id = {record.artifact_id: record for record in result.artifacts}
    palette = by_id["phase09:09_palette.json"]
    assert palette.artifact_type == "palette-consolidation-data"
    assert by_id["phase09:09_palette_strip.png"].artifact_type == "palette-strip"
    assert {parent.artifact_id for parent in palette.parents} == {
        "phase07:07_masses.json",
        "phase07:07_mass_labels.png",
        "phase07:stage.json",
        "phase08:08_importance.json",
        "phase08:08_importance_heatmap.png",
        "phase08:stage.json",
        "source",
    }


def test_bridge_phase9_fails_closed_when_phase9_stage_is_missing(
    tmp_path: Path,
) -> None:
    case_dir, source_path = _make_case(tmp_path)
    _add_phase7(case_dir, source_path)
    _add_phase8(case_dir, source_path)
    with pytest.raises(StageContractBridgeError, match="missing Phase 9"):
        bridge_stage_contracts(case_dir, source_path, max_phase=9)


def _add_phase10(case_dir: Path, source_path: Path) -> None:
    phase9 = case_dir / "phase_09"
    phase10 = case_dir / "phase_10"
    phase10.mkdir()
    source = _load_stage(case_dir, 9)["source"]
    stage9 = _load_stage(case_dir, 9)
    geometry_sha = _write_output(
        phase10 / "10_geometry.json", b'{"geometry":"ok"}\n'
    )
    grid_sha = _write_output(
        phase10 / "10_candidate_grid.png", b"phase10-grid"
    )
    selected_sha = _write_output(
        phase10 / "10_selected_primitives.png", b"phase10-selected"
    )
    stage10 = _base_stage(
        phase=10,
        stage_name="part_aware_geometrization",
        source=source,
        config={"geometry": "test"},
        inputs={
            "phase9": {
                "09_palette.json": stage9["outputs"]["09_palette.json"],
                "09_palette_preview.png": stage9["outputs"]["09_palette_preview.png"],
                "09_palette_strip.png": stage9["outputs"]["09_palette_strip.png"],
                "stage.json": _sha256_file(phase9 / "stage.json"),
            },
            "source": {
                "path": source_path.name,
                "sha256": source["sha256"],
            },
        },
        outputs={
            "10_geometry.json": geometry_sha,
            "10_candidate_grid.png": grid_sha,
            "10_selected_primitives.png": selected_sha,
        },
    )
    _write_stage(phase10 / "stage.json", stage10)


def test_bridge_can_extend_verified_chain_through_phase10(tmp_path: Path) -> None:
    case_dir, source_path = _make_case(tmp_path)
    _add_phase7(case_dir, source_path)
    _add_phase8(case_dir, source_path)
    _add_phase9(case_dir, source_path)
    _add_phase10(case_dir, source_path)

    result = bridge_stage_contracts(
        case_dir,
        source_path,
        output_dir=tmp_path / "bridge-phase10",
        max_phase=10,
    )

    assert result.gate_result.passed is True
    assert result.run_manifest.run_id == "case-a:phase03-10"
    assert len(result.run_manifest.stage_manifest_refs) == 8
    by_id = {record.artifact_id: record for record in result.artifacts}
    geometry = by_id["phase10:10_geometry.json"]
    assert geometry.artifact_type == "part-aware-geometry-data"
    assert by_id["phase10:10_candidate_grid.png"].artifact_type == "primitive-candidate-grid"
    assert by_id["phase10:10_selected_primitives.png"].artifact_type == "selected-primitive-preview"
    assert {parent.artifact_id for parent in geometry.parents} == {
        "phase09:09_palette.json",
        "phase09:09_palette_preview.png",
        "phase09:09_palette_strip.png",
        "phase09:stage.json",
        "source",
    }


def test_bridge_phase10_fails_closed_when_phase10_stage_is_missing(tmp_path: Path) -> None:
    case_dir, source_path = _make_case(tmp_path)
    _add_phase7(case_dir, source_path)
    _add_phase8(case_dir, source_path)
    _add_phase9(case_dir, source_path)
    with pytest.raises(StageContractBridgeError, match="missing Phase 10"):
        bridge_stage_contracts(case_dir, source_path, max_phase=10)


def _add_phase11(case_dir: Path, source_path: Path) -> None:
    phase5 = case_dir / "phase_05"
    phase10 = case_dir / "phase_10"
    phase11 = case_dir / "phase_11"
    phase11.mkdir()
    source = _load_stage(case_dir, 10)["source"]
    stage5 = _load_stage(case_dir, 5)
    stage10 = _load_stage(case_dir, 10)
    composition_sha = _write_output(
        phase11 / "11_composition.json", b'{"composition":"ok"}\n'
    )
    composed_sha = _write_output(
        phase11 / "11_composed_minimal.png", b"phase11-composed"
    )
    overlay_sha = _write_output(
        phase11 / "11_zorder_overlay.png", b"phase11-overlay"
    )
    stage11 = _base_stage(
        phase=11,
        stage_name="semantic_composition",
        source=source,
        config={"depth_authority": ["in_front_of", "behind"]},
        inputs={
            "phase5": {
                **stage5["outputs"],
                "stage.json": _sha256_file(phase5 / "stage.json"),
            },
            "phase10": {
                **stage10["outputs"],
                "stage.json": _sha256_file(phase10 / "stage.json"),
            },
            "source": {
                "path": source_path.name,
                "sha256": source["sha256"],
            },
        },
        outputs={
            "11_composition.json": composition_sha,
            "11_composed_minimal.png": composed_sha,
            "11_zorder_overlay.png": overlay_sha,
        },
    )
    _write_stage(phase11 / "stage.json", stage11)


def test_bridge_can_extend_verified_chain_through_phase11(tmp_path: Path) -> None:
    case_dir, source_path = _make_case(tmp_path)
    _add_phase7(case_dir, source_path)
    _add_phase8(case_dir, source_path)
    _add_phase9(case_dir, source_path)
    _add_phase10(case_dir, source_path)
    _add_phase11(case_dir, source_path)

    result = bridge_stage_contracts(
        case_dir,
        source_path,
        output_dir=tmp_path / "bridge-phase11",
        max_phase=11,
    )

    assert result.gate_result.passed is True
    assert result.run_manifest.run_id == "case-a:phase03-11"
    assert len(result.run_manifest.stage_manifest_refs) == 9
    by_id = {record.artifact_id: record for record in result.artifacts}
    composition = by_id["phase11:11_composition.json"]
    assert composition.artifact_type == "semantic-composition-scene"
    assert (
        by_id["phase11:11_composed_minimal.png"].artifact_type
        == "semantic-composition-preview"
    )
    assert (
        by_id["phase11:11_zorder_overlay.png"].artifact_type
        == "semantic-zorder-overlay"
    )
    parent_ids = {parent.artifact_id for parent in composition.parents}
    assert "phase05:05_structure_graph.json" in parent_ids
    assert "phase05:stage.json" in parent_ids
    assert "phase10:10_geometry.json" in parent_ids
    assert "phase10:stage.json" in parent_ids
    assert "source" in parent_ids


def test_bridge_phase11_fails_closed_when_phase11_stage_is_missing(
    tmp_path: Path,
) -> None:
    case_dir, source_path = _make_case(tmp_path)
    _add_phase7(case_dir, source_path)
    _add_phase8(case_dir, source_path)
    _add_phase9(case_dir, source_path)
    _add_phase10(case_dir, source_path)
    with pytest.raises(StageContractBridgeError, match="missing Phase 11"):
        bridge_stage_contracts(case_dir, source_path, max_phase=11)


def _add_phase12(case_dir: Path, source_path: Path) -> None:
    phase11 = case_dir / "phase_11"
    phase12 = case_dir / "phase_12"
    phase12.mkdir()
    source = _load_stage(case_dir, 11)["source"]
    stage11 = _load_stage(case_dir, 11)
    data_sha = _write_output(
        phase12 / "12_simplification.json", b'{"simplification":"ok"}\n'
    )
    final_sha = _write_output(
        phase12 / "12_final.png", b"phase12-final"
    )
    stage12 = _base_stage(
        phase=12,
        stage_name="style_constraint_simplification",
        source=source,
        config={"style": "test"},
        inputs={
            "phase11": {
                **stage11["outputs"],
                "stage.json": _sha256_file(phase11 / "stage.json"),
            },
            "source": {
                "path": source_path.name,
                "sha256": source["sha256"],
            },
        },
        outputs={
            "12_simplification.json": data_sha,
            "12_final.png": final_sha,
        },
    )
    _write_stage(phase12 / "stage.json", stage12)


def _add_phase13(case_dir: Path, source_path: Path) -> None:
    phase12 = case_dir / "phase_12"
    phase13 = case_dir / "phase_13"
    phase13.mkdir()
    source = _load_stage(case_dir, 12)["source"]
    stage12 = _load_stage(case_dir, 12)
    board_sha = _write_output(
        phase13 / "13_debug_board.png", b"phase13-board"
    )
    index_sha = _write_output(
        phase13 / "13_stage_index.json", b'{"stages":[]}\n'
    )
    stage13 = _base_stage(
        phase=13,
        stage_name="stage_visualizer_debug_board",
        source=source,
        config={"stage_order": ["input", "03", "12"]},
        inputs={
            "phase12": {
                "12_final.png": stage12["outputs"]["12_final.png"],
                "stage.json": _sha256_file(phase12 / "stage.json"),
            },
            "source": {
                "path": source_path.name,
                "sha256": source["sha256"],
            },
        },
        outputs={
            "13_debug_board.png": board_sha,
            "13_stage_index.json": index_sha,
        },
    )
    _write_stage(phase13 / "stage.json", stage13)


def test_bridge_can_extend_verified_chain_through_phase13(tmp_path: Path) -> None:
    case_dir, source_path = _make_case(tmp_path)
    _add_phase7(case_dir, source_path)
    _add_phase8(case_dir, source_path)
    _add_phase9(case_dir, source_path)
    _add_phase10(case_dir, source_path)
    _add_phase11(case_dir, source_path)
    _add_phase12(case_dir, source_path)
    _add_phase13(case_dir, source_path)

    result = bridge_stage_contracts(
        case_dir,
        source_path,
        output_dir=tmp_path / "bridge-phase13",
        max_phase=13,
    )

    assert result.gate_result.passed is True
    assert result.run_manifest.run_id == "case-a:phase03-13"
    assert len(result.run_manifest.stage_manifest_refs) == 11
    by_id = {record.artifact_id: record for record in result.artifacts}
    assert by_id["phase13:13_debug_board.png"].artifact_type == "stage-debug-board"
    assert by_id["phase13:13_stage_index.json"].artifact_type == "stage-debug-index"
    parent_ids = {
        parent.artifact_id
        for parent in by_id["phase13:13_debug_board.png"].parents
    }
    assert "phase12:12_final.png" in parent_ids
    assert "phase12:stage.json" in parent_ids
    assert "source" in parent_ids


def _add_phase14(case_dir: Path, source_path: Path) -> None:
    phase4 = case_dir / "phase_04"
    phase12 = case_dir / "phase_12"
    phase13 = case_dir / "phase_13"
    phase14 = case_dir / "phase_14"
    phase14.mkdir()
    source = _load_stage(case_dir, 13)["source"]
    stage4 = _load_stage(case_dir, 4)
    stage12 = _load_stage(case_dir, 12)
    stage13 = _load_stage(case_dir, 13)

    eval_sha = _write_output(
        phase14 / "14_case_evaluation.json",
        b'{"phase":14,"pass":true}\n',
    )
    sheet_sha = _write_output(
        phase14 / "14_eval_sheet.png",
        b"phase14-eval-sheet",
    )
    preview_sha = _write_output(
        phase14 / "preview.png",
        b"phase14-preview",
    )
    metrics_sha = _write_output(
        phase14 / "metrics.json",
        b'{"pass":true}\n',
    )

    stage14 = _base_stage(
        phase=14,
        stage_name="evaluation_redesign_calibration",
        source=source,
        config={"evaluation_version": "phase14-test-v1"},
        inputs={
            "phase04": {
                "part_masks/face.png": stage4["outputs"][
                    "part_masks/face.png"
                ],
                "stage.json": _sha256_file(phase4 / "stage.json"),
            },
            "phase12": {
                "12_simplification.json": stage12["outputs"][
                    "12_simplification.json"
                ],
                "12_final.png": stage12["outputs"]["12_final.png"],
                "stage.json": _sha256_file(phase12 / "stage.json"),
            },
            "phase13": {
                "13_stage_index.json": stage13["outputs"][
                    "13_stage_index.json"
                ],
                "13_debug_board.png": stage13["outputs"][
                    "13_debug_board.png"
                ],
                "stage.json": _sha256_file(phase13 / "stage.json"),
            },
            "source": {
                "path": source_path.name,
                "sha256": source["sha256"],
            },
        },
        outputs={
            "14_case_evaluation.json": eval_sha,
            "14_eval_sheet.png": sheet_sha,
            "preview.png": preview_sha,
            "metrics.json": metrics_sha,
        },
    )
    _write_stage(phase14 / "stage.json", stage14)


def test_bridge_can_extend_verified_chain_through_phase14(tmp_path: Path) -> None:
    case_dir, source_path = _make_case(tmp_path)
    _add_phase7(case_dir, source_path)
    _add_phase8(case_dir, source_path)
    _add_phase9(case_dir, source_path)
    _add_phase10(case_dir, source_path)
    _add_phase11(case_dir, source_path)
    _add_phase12(case_dir, source_path)
    _add_phase13(case_dir, source_path)
    _add_phase14(case_dir, source_path)

    result = bridge_stage_contracts(
        case_dir,
        source_path,
        output_dir=tmp_path / "bridge-phase14",
        max_phase=14,
    )

    assert result.gate_result.passed is True
    assert result.run_manifest.run_id == "case-a:phase03-14"
    assert len(result.run_manifest.stage_manifest_refs) == 12
    by_id = {record.artifact_id: record for record in result.artifacts}
    assert (
        by_id["phase14:14_case_evaluation.json"].artifact_type
        == "evaluation-redesign-data"
    )
    assert (
        by_id["phase14:14_eval_sheet.png"].artifact_type
        == "evaluation-sheet"
    )
    parent_ids = {
        parent.artifact_id
        for parent in by_id["phase14:14_case_evaluation.json"].parents
    }
    assert "phase04:part_masks/face.png" in parent_ids
    assert "phase12:12_simplification.json" in parent_ids
    assert "phase12:12_final.png" in parent_ids
    assert "phase13:13_stage_index.json" in parent_ids
    assert "phase13:13_debug_board.png" in parent_ids
    assert "source" in parent_ids


def test_bridge_accepts_unicode_source_copy_path(tmp_path: Path) -> None:
    case_dir, source_path = _make_case(tmp_path)
    unicode_source = tmp_path / "日本語ソース.png"
    unicode_source.write_bytes(source_path.read_bytes())

    result = bridge_stage_contracts(
        case_dir,
        unicode_source,
        output_dir=tmp_path / "bridge-unicode-source",
    )

    assert result.gate_result.passed is True
    assert result.run_manifest.run_id == "case-a:phase03-06"
