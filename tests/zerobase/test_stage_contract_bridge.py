from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

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
    Image.new("RGB", (8, 6), (120, 80, 40)).save(source_path)
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
    Image.new("RGB", (8, 6), (0, 0, 0)).save(source_path)
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
