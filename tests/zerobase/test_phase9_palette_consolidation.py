from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from minimalizer_zerobase.palette import (
    PaletteConsolidationPolicy,
    consolidate_palette,
    write_phase9_artifacts,
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _runs(mask: np.ndarray) -> list[list[int]]:
    output: list[list[int]] = []
    for y in np.flatnonzero(np.any(mask, axis=1)):
        xs = np.flatnonzero(mask[y])
        start = previous = int(xs[0])
        for raw_x in xs[1:]:
            x = int(raw_x)
            if x != previous + 1:
                output.append([int(y), start, previous + 1])
                start = x
            previous = x
        output.append([int(y), start, previous + 1])
    return output


def _fixture() -> tuple[np.ndarray, dict, dict, np.ndarray]:
    height, width = 12, 16
    source = np.full((height, width, 3), (245, 245, 243), dtype=np.uint8)
    labels = np.full((height, width), 65535, dtype=np.uint16)
    specs = (
        ("hair", "bound", "protect", (30, 35, 40), (slice(1, 4), slice(1, 4))),
        ("hair", "bound", "keep", (36, 40, 45), (slice(1, 4), slice(4, 7))),
        (
            "major_clothing",
            "bound",
            "protect",
            (30, 35, 40),
            (slice(5, 9), slice(1, 5)),
        ),
        ("face", "bound", "protect", (224, 178, 146), (slice(1, 4), slice(8, 11))),
        (
            "accessory_or_held_object",
            "bound",
            "protect",
            (190, 35, 45),
            (slice(5, 7), slice(7, 9)),
        ),
        (
            "accessory_or_held_object",
            "bound",
            "protect",
            (35, 175, 70),
            (slice(7, 9), slice(7, 9)),
        ),
        (None, "unbound", "protect", (118, 70, 150), (slice(9, 11), slice(12, 15))),
        ("hair", "bound", "prune", (34, 39, 44), (slice(5, 6), slice(12, 13))),
    )
    masses = []
    decisions = []
    for index, (part, status, action, color, selection) in enumerate(specs):
        labels[selection] = index
        source[selection] = color
        mask = labels == index
        ys, xs = np.where(mask)
        masses.append(
            {
                "mass_id": f"mass-{index:04d}",
                "semantic_part_id": part,
                "binding_status": status,
                "region_ids": [f"region-{index:04d}"],
                "pixel_count": int(xs.size),
                "bbox_xywh": [
                    int(xs.min()),
                    int(ys.min()),
                    int(xs.max() - xs.min() + 1),
                    int(ys.max() - ys.min() + 1),
                ],
                "centroid_xy": [float(xs.mean()), float(ys.mean())],
                "mean_rgb": [float(value) for value in color],
                "pixel_runs": _runs(mask),
                "evidence_refs": ["phase06:test"],
            }
        )
        rationale = []
        if action == "protect" and part in {"face", "accessory_or_held_object"}:
            rationale.append(f"identity-role-protected:{part}")
        decisions.append(
            {
                "mass_id": f"mass-{index:04d}",
                "semantic_part_id": part,
                "binding_status": status,
                "pixel_count": int(xs.size),
                "action": action,
                "rationale": rationale,
            }
        )
    phase7 = {
        "schema_version": "1.0",
        "coordinate_space": {
            "pixel_width": width,
            "pixel_height": height,
            "normalized_origin": "top-left",
            "normalized_range": [0.0, 1.0],
        },
        "masses": masses,
        "validation": {"pass": True, "subject_pixel_count": int(np.count_nonzero(labels != 65535))},
    }
    phase8 = {
        "schema_version": "1.0",
        "coordinate_space": phase7["coordinate_space"],
        "decisions": decisions,
        "validation": {"pass": True},
    }
    return source, phase7, phase8, labels


def _by_mass(result) -> dict:
    return {item.mass_id: item for item in result.assignments}


def test_phase9_is_deterministic_and_uses_only_source_colors() -> None:
    source, phase7, phase8, labels = _fixture()
    before7, before8 = copy.deepcopy(phase7), copy.deepcopy(phase8)
    first = consolidate_palette(source, phase7, phase8, labels)
    second = consolidate_palette(source, phase7, phase8, labels)

    assert first.to_dict() == second.to_dict()
    assert phase7 == before7
    assert phase8 == before8
    for entry in first.palette:
        x, y = entry.source_pixel_xy
        assert tuple(int(value) for value in source[y, x]) == entry.color_rgb
    assert first.validation["source_derived_representative_violation_count"] == 0
    assert first.validation["pass"] is True


def test_phase9_default_merge_is_same_part_only() -> None:
    source, phase7, phase8, labels = _fixture()
    result = consolidate_palette(source, phase7, phase8, labels)
    by_mass = _by_mass(result)

    assert by_mass["mass-0000"].palette_id == by_mass["mass-0001"].palette_id
    assert by_mass["mass-0000"].palette_id != by_mass["mass-0002"].palette_id
    assert by_mass["mass-0000"].source_color_rgb == by_mass["mass-0002"].source_color_rgb
    assert result.validation["same_part_merge_count"] == 1
    assert result.validation["cross_part_merge_count"] == 0


def test_phase9_protects_face_accessory_and_critical_contrast_anchors() -> None:
    source, phase7, phase8, labels = _fixture()
    result = consolidate_palette(source, phase7, phase8, labels)
    by_mass = _by_mass(result)
    entries = {entry.palette_id: entry for entry in result.palette}

    for mass_id in ("mass-0003", "mass-0004", "mass-0005"):
        assignment = by_mass[mass_id]
        assert assignment.action == "protect"
        assert assignment.assignment_kind == "part-anchor"
        assert entries[assignment.palette_id].protected_anchor is True
        assert assignment.source_color_rgb == assignment.palette_color_rgb
    assert by_mass["mass-0004"].palette_id != by_mass["mass-0005"].palette_id
    assert result.validation["critical_contrast_violation_count"] == 0
    assert result.validation["critical_anchor_violation_count"] == 0


def test_phase9_does_not_merge_or_reinterpret_unbound() -> None:
    source, phase7, phase8, labels = _fixture()
    result = consolidate_palette(source, phase7, phase8, labels)
    unbound = _by_mass(result)["mass-0006"]

    assert unbound.semantic_part_id is None
    assert unbound.assignment_kind == "unbound-isolated"
    assert unbound.source_color_rgb == unbound.palette_color_rgb
    assert result.validation["unbound_merge_count"] == 0
    assert result.validation["unbound_reinterpretation_count"] == 0


def test_phase9_never_resurrects_phase8_prune() -> None:
    source, phase7, phase8, labels = _fixture()
    result = consolidate_palette(source, phase7, phase8, labels)
    pruned = _by_mass(result)["mass-0007"]

    assert pruned.action == "prune"
    assert pruned.palette_id is None
    assert pruned.palette_color_rgb is None
    assert pruned.assignment_kind == "pruned"
    assert result.validation["prune_resurrection_count"] == 0


def test_phase9_policy_rejects_forbidden_authority_and_contrast_collapse() -> None:
    with pytest.raises(ValueError, match="cross-part"):
        PaletteConsolidationPolicy(allow_cross_part_merge=True)
    with pytest.raises(ValueError, match="unbound reinterpretation"):
        PaletteConsolidationPolicy(reinterpret_unbound=True)
    with pytest.raises(ValueError, match="observed source pixels"):
        PaletteConsolidationPolicy(representative_strategy="average")
    with pytest.raises(ValueError, match="contrast guard"):
        PaletteConsolidationPolicy(
            critical_near_color_distance=30,
            critical_contrast_distance=28,
        )


def test_phase9_rejects_phase8_owner_or_protect_drift() -> None:
    source, phase7, phase8, labels = _fixture()
    phase8["decisions"][0]["semantic_part_id"] = "major_clothing"
    with pytest.raises(ValueError, match="semantic owner drift"):
        consolidate_palette(source, phase7, phase8, labels)

    source, phase7, phase8, labels = _fixture()
    phase8["decisions"][3]["action"] = "keep"
    with pytest.raises(ValueError, match="face/accessory anchors"):
        consolidate_palette(source, phase7, phase8, labels)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _write_upstream(
    root: Path,
    source: np.ndarray,
    phase7_payload: dict,
    phase8_payload: dict,
    labels: np.ndarray,
) -> tuple[Path, Path, Path, dict, dict]:
    source_path = root / "source.png"
    assert cv2.imwrite(str(source_path), cv2.cvtColor(source, cv2.COLOR_RGB2BGR))
    source_contract = {
        "path": source_path.name,
        "sha256": _sha256_file(source_path),
        "width": source.shape[1],
        "height": source.shape[0],
    }
    phase7_dir = root / "phase_07"
    phase8_dir = root / "phase_08"
    phase7_dir.mkdir()
    phase8_dir.mkdir()

    _write_json(phase7_dir / "07_masses.json", phase7_payload)
    assert cv2.imwrite(str(phase7_dir / "07_mass_labels.png"), labels)
    assert cv2.imwrite(
        str(phase7_dir / "07_mass_silhouette.png"),
        (labels != 65535).astype(np.uint8) * 255,
    )
    phase7_block = np.full_like(source, 100)
    for name in ("07_mass_blocks.png", "07_mass_outline_overlay.png", "preview.png"):
        assert cv2.imwrite(str(phase7_dir / name), cv2.cvtColor(phase7_block, cv2.COLOR_RGB2BGR))
    _write_json(phase7_dir / "metrics.json", {"pass": True})
    phase7_outputs = {
        path.name: _sha256_file(path)
        for path in phase7_dir.iterdir()
        if path.name != "stage.json"
    }
    phase7_stage = {
        "phase": 7,
        "source": source_contract,
        "metrics": {"pass": True},
        "outputs": phase7_outputs,
    }
    _write_json(phase7_dir / "stage.json", phase7_stage)

    _write_json(phase8_dir / "08_importance.json", phase8_payload)
    phase8_image = np.full_like(source, 110)
    for name in (
        "08_importance_heatmap.png",
        "08_pruned_masses.png",
        "08_removed_overlay.png",
        "preview.png",
    ):
        assert cv2.imwrite(str(phase8_dir / name), cv2.cvtColor(phase8_image, cv2.COLOR_RGB2BGR))
    _write_json(phase8_dir / "metrics.json", {"pass": True})
    phase8_outputs = {
        path.name: _sha256_file(path)
        for path in phase8_dir.iterdir()
        if path.name != "stage.json"
    }
    phase8_stage = {
        "phase": 8,
        "source": source_contract,
        "metrics": {"pass": True},
        "outputs": phase8_outputs,
    }
    _write_json(phase8_dir / "stage.json", phase8_stage)
    return source_path, phase7_dir, phase8_dir, phase7_stage, phase8_stage


def test_phase9_writes_required_outputs_and_binds_all_phase8_outputs(tmp_path: Path) -> None:
    source, phase7_payload, phase8_payload, labels = _fixture()
    source_path, phase7_dir, phase8_dir, phase7_stage, phase8_stage = _write_upstream(
        tmp_path, source, phase7_payload, phase8_payload, labels
    )
    policy = PaletteConsolidationPolicy()
    result = consolidate_palette(source, phase7_payload, phase8_payload, labels, policy=policy)
    output = tmp_path / "phase_09"
    stage = write_phase9_artifacts(
        source_path,
        phase7_dir,
        phase8_dir,
        result,
        output,
        config=policy.to_dict(),
        phase7_stage=phase7_stage,
        phase8_stage=phase8_stage,
    )

    required = {
        "09_palette.json",
        "09_palette_preview.png",
        "09_palette_strip.png",
        "preview.png",
        "metrics.json",
        "stage.json",
    }
    assert {path.name for path in output.iterdir()} == required
    assert stage["phase"] == 9
    assert stage["metrics"]["pass"] is True
    assert set(stage["inputs"]["phase8"]) == {
        *phase8_stage["outputs"],
        "stage.json",
    }
    assert stage["merge_policy"]["cross_part_merge"] == "forbidden"
    assert stage["representative_color_policy"]["synthetic_average_color"] == "forbidden"
    assert _sha256_file(output / "preview.png") == _sha256_file(
        output / "09_palette_preview.png"
    )
    preview = cv2.imread(str(output / "09_palette_preview.png"), cv2.IMREAD_COLOR)
    assert preview is not None
    assert tuple(int(value) for value in preview[5, 12]) == (236, 238, 238)


def test_phase9_writer_rejects_phase8_declared_output_tamper(tmp_path: Path) -> None:
    source, phase7_payload, phase8_payload, labels = _fixture()
    source_path, phase7_dir, phase8_dir, phase7_stage, phase8_stage = _write_upstream(
        tmp_path, source, phase7_payload, phase8_payload, labels
    )
    result = consolidate_palette(source, phase7_payload, phase8_payload, labels)
    (phase8_dir / "metrics.json").write_text('{"pass":false}', encoding="utf-8")

    with pytest.raises(ValueError, match="Phase 8 input SHA mismatch: metrics.json"):
        write_phase9_artifacts(
            source_path,
            phase7_dir,
            phase8_dir,
            result,
            tmp_path / "phase_09",
            config=PaletteConsolidationPolicy().to_dict(),
            phase7_stage=phase7_stage,
            phase8_stage=phase8_stage,
        )
    assert not (tmp_path / "phase_09").exists()
