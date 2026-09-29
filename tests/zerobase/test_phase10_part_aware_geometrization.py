from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from minimalizer_zerobase.geometrization import (
    PART_FAMILIES,
    PartAwareGeometrizationPolicy,
    geometrize_parts,
    write_phase10_artifacts,
)


def _sha256(path: Path) -> str:
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


def _fixture() -> tuple[dict, dict, dict, np.ndarray]:
    height = width = 32
    labels = np.full((height, width), 65535, dtype=np.uint16)
    specs = (
        ("hair", "bound", "protect", (slice(1, 11), slice(1, 13)), (45, 35, 30)),
        ("face", "bound", "protect", (slice(4, 10), slice(15, 21)), (224, 178, 146)),
        ("torso", "bound", "protect", (slice(13, 24), slice(9, 20)), (70, 95, 150)),
        ("left_arm", "bound", "keep", (slice(13, 25), slice(3, 6)), (218, 170, 140)),
        ("accessory_or_held_object", "bound", "protect", (slice(12, 28), slice(24, 26)), (45, 170, 70)),
        (None, "unbound", "protect", (slice(27, 30), slice(11, 14)), (130, 80, 160)),
        ("hair", "bound", "prune", (slice(1, 3), slice(28, 30)), (55, 40, 35)),
    )
    masses: list[dict] = []
    decisions: list[dict] = []
    assignments: list[dict] = []
    palette: list[dict] = []
    for index, (part, status, action, selection, color) in enumerate(specs):
        labels[selection] = index
        mask = labels == index
        ys, xs = np.where(mask)
        mass_id = f"mass-{index:04d}"
        masses.append(
            {
                "mass_id": mass_id,
                "semantic_part_id": part,
                "binding_status": status,
                "region_ids": [f"region-{index:04d}"],
                "pixel_count": int(xs.size),
                "bbox_xywh": [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
                "centroid_xy": [float(xs.mean()), float(ys.mean())],
                "mean_rgb": [float(value) for value in color],
                "pixel_runs": _runs(mask),
                "evidence_refs": ["phase06:test"],
            }
        )
        decisions.append(
            {
                "mass_id": mass_id,
                "semantic_part_id": part,
                "binding_status": status,
                "pixel_count": int(xs.size),
                "action": action,
            }
        )
        palette_id = None if action == "prune" else f"palette-{index:04d}"
        assignments.append(
            {
                "mass_id": mass_id,
                "semantic_part_id": part,
                "binding_status": status,
                "action": action,
                "pixel_count": int(xs.size),
                "palette_id": palette_id,
                "palette_color_rgb": None if action == "prune" else list(color),
            }
        )
        if palette_id is not None:
            palette.append(
                {
                    "palette_id": palette_id,
                    "semantic_part_id": part,
                    "color_rgb": list(color),
                    "source_mass_id": mass_id,
                    "assigned_mass_ids": [mass_id],
                }
            )
    coordinate = {
        "pixel_width": width,
        "pixel_height": height,
        "normalized_origin": "top-left",
        "normalized_range": [0.0, 1.0],
    }
    phase7 = {
        "schema_version": "1.0",
        "coordinate_space": coordinate,
        "masses": masses,
        "validation": {"pass": True, "subject_pixel_count": int(np.count_nonzero(labels != 65535))},
    }
    phase8 = {
        "schema_version": "1.0",
        "coordinate_space": coordinate,
        "decisions": decisions,
        "validation": {"pass": True},
    }
    phase9 = {
        "schema_version": "1.0",
        "coordinate_space": coordinate,
        "assignments": assignments,
        "palette": palette,
        "validation": {"pass": True},
    }
    return phase7, phase8, phase9, labels


def test_phase10_is_deterministic_and_part_aware() -> None:
    phase7, phase8, phase9, labels = _fixture()
    before = copy.deepcopy((phase7, phase8, phase9))
    first = geometrize_parts(phase7, phase8, phase9, labels)
    second = geometrize_parts(phase7, phase8, phase9, labels)

    assert first.to_dict() == second.to_dict()
    assert (phase7, phase8, phase9) == before
    assert first.validation["pass"] is True
    assert first.validation["candidate_family_count"] >= 5
    assert first.validation["mean_candidates_per_active_mass"] >= 2
    assert PART_FAMILIES["face"] != PART_FAMILIES["hair"]
    assert PART_FAMILIES["hair"] != PART_FAMILIES["left_arm"]
    assert "rounded_polygon" in PART_FAMILIES["left_arm"]
    assert "rounded_polygon" in PART_FAMILIES["right_arm"]
    assert "rounded_polygon" in PART_FAMILIES["neck"]


def _single_arm_fixture(mask: np.ndarray, *, part_id: str = "left_arm") -> tuple[dict, dict, dict, np.ndarray]:
    height, width = mask.shape
    labels = np.full(mask.shape, 65535, dtype=np.uint16)
    labels[mask] = 0
    ys, xs = np.where(mask)
    mass_id = "mass-0000"
    coordinate = {
        "pixel_width": width,
        "pixel_height": height,
        "normalized_origin": "top-left",
        "normalized_range": [0.0, 1.0],
    }
    common = {
        "mass_id": mass_id,
        "semantic_part_id": part_id,
        "binding_status": "bound",
        "pixel_count": int(xs.size),
    }
    phase7 = {
        "schema_version": "1.0",
        "coordinate_space": coordinate,
        "masses": [
            {
                **common,
                "region_ids": ["region-0000"],
                "bbox_xywh": [
                    int(xs.min()),
                    int(ys.min()),
                    int(xs.max() - xs.min() + 1),
                    int(ys.max() - ys.min() + 1),
                ],
                "centroid_xy": [float(xs.mean()), float(ys.mean())],
                "mean_rgb": [80.0, 120.0, 180.0],
                "pixel_runs": _runs(mask),
                "evidence_refs": ["phase06:test"],
            }
        ],
        "validation": {
            "pass": True,
            "subject_pixel_count": int(xs.size),
        },
    }
    phase8 = {
        "schema_version": "1.0",
        "coordinate_space": coordinate,
        "decisions": [{**common, "action": "keep"}],
        "validation": {"pass": True},
    }
    phase9 = {
        "schema_version": "1.0",
        "coordinate_space": coordinate,
        "assignments": [
            {
                **common,
                "action": "keep",
                "palette_id": "palette-0000",
                "palette_color_rgb": [80, 120, 180],
            }
        ],
        "palette": [
            {
                "palette_id": "palette-0000",
                "semantic_part_id": part_id,
                "color_rgb": [80, 120, 180],
                "source_mass_id": mass_id,
                "assigned_mass_ids": [mass_id],
            }
        ],
        "validation": {"pass": True},
    }
    return phase7, phase8, phase9, labels


@pytest.mark.parametrize("part_id", ("left_arm", "right_arm"))
def test_phase10_broad_arm_mass_uses_area_families_and_guard(part_id: str) -> None:
    mask = np.zeros((48, 48), dtype=bool)
    mask[10:34, 8:30] = True
    mask[6:18, 18:38] = True
    phase7, phase8, phase9, labels = _single_arm_fixture(mask, part_id=part_id)

    result = geometrize_parts(phase7, phase8, phase9, labels)
    families = {item.primitive_type for item in result.candidates}
    selected = result.selected[0]

    assert {"polygon", "rounded_polygon"} <= families
    assert "capsule" not in families
    assert "oriented_rectangle" not in families
    assert selected.primitive_type not in {"capsule", "oriented_rectangle"}
    assert selected.selection_rationale == "minimum-aspect-aware-arm-cost-with-broad-mass-guard"
    assert result.candidates[0].parameters["source_mass_shape"]["elongation"] <= 2.25


def test_phase10_slender_arm_keeps_linear_families() -> None:
    mask = np.zeros((64, 32), dtype=bool)
    mask[5:59, 13:18] = True
    phase7, phase8, phase9, labels = _single_arm_fixture(mask)

    result = geometrize_parts(phase7, phase8, phase9, labels)
    families = {item.primitive_type for item in result.candidates}

    assert {"capsule", "tapered_strip", "polyline_ribbon"} <= families
    assert "polygon" not in families
    assert result.candidates[0].parameters["source_mass_shape"]["elongation"] > 2.25


def test_phase10_binds_every_candidate_and_selection_to_mass_and_owner() -> None:
    phase7, phase8, phase9, labels = _fixture()
    result = geometrize_parts(phase7, phase8, phase9, labels)
    owners = {item["mass_id"]: item["semantic_part_id"] for item in phase7["masses"]}
    selected_ids = {item.candidate_id for item in result.selected}

    for candidate in result.candidates:
        assert candidate.semantic_part_id == owners[candidate.mass_id]
        assert candidate.evidence_refs[0] == f"phase07:{candidate.mass_id}"
    assert selected_ids <= {item.candidate_id for item in result.candidates}
    assert result.validation["semantic_owner_change_count"] == 0
    assert result.validation["cross_mass_candidate_count"] == 0


def test_phase10_never_resurrects_pruned_or_reinterprets_unbound() -> None:
    phase7, phase8, phase9, labels = _fixture()
    result = geometrize_parts(phase7, phase8, phase9, labels)

    assert result.omitted_mass_ids == ("mass-0006",)
    assert all(item.mass_id != "mass-0006" for item in result.candidates)
    unbound = [item for item in result.selected if item.mass_id == "mass-0005"]
    assert len(unbound) == 1
    assert unbound[0].semantic_part_id is None
    assert unbound[0].binding_status == "unbound"
    assert result.validation["prune_resurrections"] == []


def test_phase10_policy_rejects_forbidden_generic_authority() -> None:
    with pytest.raises(ValueError, match="axis-aligned rectangles"):
        PartAwareGeometrizationPolicy(allow_axis_aligned_rectangle=True)
    with pytest.raises(ValueError, match="cross-mass"):
        PartAwareGeometrizationPolicy(allow_cross_mass_candidate=True)
    with pytest.raises(ValueError, match="prune resurrection"):
        PartAwareGeometrizationPolicy(allow_prune_resurrection=True)


@pytest.mark.parametrize(
    ("phase", "mutation", "message"),
    (
        (8, lambda payload: payload["decisions"][0].update(semantic_part_id="torso"), "Phase 8 semantic owner drift"),
        (9, lambda payload: payload["assignments"][0].update(action="prune"), "Phase 9 action drift"),
        (9, lambda payload: payload["assignments"][6].update(palette_id="palette-0000"), "prune resurrection"),
    ),
)
def test_phase10_fails_closed_on_upstream_drift(phase: int, mutation, message: str) -> None:
    phase7, phase8, phase9, labels = _fixture()
    target = {8: phase8, 9: phase9}[phase]
    mutation(target)
    with pytest.raises(ValueError, match=message):
        geometrize_parts(phase7, phase8, phase9, labels)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _write_upstream(root: Path, phase7: dict, phase8: dict, phase9: dict, labels: np.ndarray) -> tuple[Path, list[Path], list[dict]]:
    source_path = root / "source.png"
    source = np.full((32, 32, 3), 180, dtype=np.uint8)
    assert cv2.imwrite(str(source_path), source)
    source_contract = {"path": source_path.name, "sha256": _sha256(source_path), "width": 32, "height": 32}
    directories: list[Path] = []
    stages: list[dict] = []
    payload_names = {7: ("07_masses.json", phase7), 8: ("08_importance.json", phase8), 9: ("09_palette.json", phase9)}
    for phase in (7, 8, 9):
        directory = root / f"phase_{phase:02d}"
        directory.mkdir()
        name, payload = payload_names[phase]
        _write_json(directory / name, payload)
        if phase == 7:
            assert cv2.imwrite(str(directory / "07_mass_labels.png"), labels)
        _write_json(directory / "metrics.json", {"pass": True})
        outputs = {path.name: _sha256(path) for path in directory.iterdir()}
        stage = {
            "phase": phase,
            "stage": f"phase_{phase:02d}",
            "producer": f"test-phase-{phase}",
            "producer_version": "1.0",
            "source": source_contract,
            "config": {},
            "config_sha256": hashlib.sha256(b"{}").hexdigest(),
            "metrics": {"pass": True},
            "outputs": outputs,
        }
        _write_json(directory / "stage.json", stage)
        directories.append(directory)
        stages.append(stage)
    return source_path, directories, stages


def test_phase10_writer_emits_required_sha_bound_artifacts(tmp_path: Path) -> None:
    phase7, phase8, phase9, labels = _fixture()
    source_path, directories, stages = _write_upstream(tmp_path, phase7, phase8, phase9, labels)
    policy = PartAwareGeometrizationPolicy()
    result = geometrize_parts(phase7, phase8, phase9, labels, policy=policy)
    output = tmp_path / "phase_10"
    stage = write_phase10_artifacts(
        source_path,
        *directories,
        result,
        output,
        config=policy.to_dict(),
        phase7_stage=stages[0],
        phase8_stage=stages[1],
        phase9_stage=stages[2],
    )

    assert {path.name for path in output.iterdir()} == {
        "10_geometry.json",
        "10_candidate_grid.png",
        "10_selected_primitives.png",
        "preview.png",
        "metrics.json",
        "stage.json",
    }
    assert stage["phase"] == 10
    assert stage["metrics"]["pass"] is True
    assert set(stage["inputs"]["phase9"]) == {*stages[2]["outputs"], "stage.json"}
    payload = json.loads((output / "10_geometry.json").read_text(encoding="utf-8"))
    assert payload["primitive_candidates"]
    assert payload["candidate_costs"]
    assert payload["selected_primitives"]
    assert _sha256(output / "preview.png") == _sha256(output / "10_selected_primitives.png")


def test_phase10_writer_rejects_phase9_tamper_before_output(tmp_path: Path) -> None:
    phase7, phase8, phase9, labels = _fixture()
    source_path, directories, stages = _write_upstream(tmp_path, phase7, phase8, phase9, labels)
    result = geometrize_parts(phase7, phase8, phase9, labels)
    (directories[2] / "metrics.json").write_text('{"pass":false}', encoding="utf-8")

    with pytest.raises(ValueError, match="Phase 9 input SHA mismatch: metrics.json"):
        write_phase10_artifacts(
            source_path,
            *directories,
            result,
            tmp_path / "phase_10",
            config=PartAwareGeometrizationPolicy().to_dict(),
            phase7_stage=stages[0],
            phase8_stage=stages[1],
            phase9_stage=stages[2],
        )
    assert not (tmp_path / "phase_10").exists()
