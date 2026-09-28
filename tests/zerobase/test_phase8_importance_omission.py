from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from minimalizer_zerobase.importance import (
    OmissionPolicy,
    evaluate_importance_omission,
    write_phase8_artifacts,
)

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _runs(mask: np.ndarray) -> list[list[int]]:
    encoded: list[list[int]] = []
    for y in np.flatnonzero(np.any(mask, axis=1)):
        xs = np.flatnonzero(mask[y])
        start = previous = int(xs[0])
        for raw_x in xs[1:]:
            x = int(raw_x)
            if x != previous + 1:
                encoded.append([int(y), start, previous + 1])
                start = x
            previous = x
        encoded.append([int(y), start, previous + 1])
    return encoded


def _fixture() -> tuple[dict, np.ndarray, np.ndarray]:
    height = width = 24
    labels = np.full((height, width), 65535, dtype=np.uint16)
    specs = (
        ("hair", "bound", (35, 42, 48), (slice(2, 11), slice(2, 11))),
        ("torso", "bound", (80, 90, 100), (slice(11, 22), slice(3, 20))),
        ("hair", "bound", (36, 43, 49), (slice(14, 15), slice(8, 9))),
        ("face", "bound", (224, 184, 158), (slice(5, 9), slice(12, 16))),
        (
            "accessory_or_held_object",
            "bound",
            (32, 180, 76),
            (slice(11, 14), slice(20, 22)),
        ),
        (None, "unbound", (190, 50, 190), (slice(18, 20), slice(20, 22))),
        ("neck", "bound", (210, 170, 145), (slice(9, 11), slice(13, 15))),
    )
    for index, (_, _, _, selection) in enumerate(specs):
        labels[selection] = index

    masses = []
    for index, (part, status, color, selection) in enumerate(specs):
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
                "mean_rgb": list(color),
                "pixel_runs": _runs(mask),
                "evidence_refs": ["phase06:test"],
            }
        )
    silhouette = (labels != 65535).astype(np.uint8) * 255
    payload = {
        "schema_version": "1.0",
        "coordinate_space": {
            "pixel_width": width,
            "pixel_height": height,
            "normalized_origin": "top-left",
            "normalized_range": [0.0, 1.0],
        },
        "masses": masses,
        "validation": {
            "subject_pixel_count": int(np.count_nonzero(silhouette)),
            "pass": True,
        },
    }
    return payload, labels, silhouette


def _by_id(result) -> dict:
    return {decision.mass_id: decision for decision in result.decisions}


def test_phase8_records_all_five_dimensions_and_is_deterministic() -> None:
    payload, labels, silhouette = _fixture()
    before = copy.deepcopy(payload)
    first = evaluate_importance_omission(payload, labels, silhouette)
    second = evaluate_importance_omission(payload, labels, silhouette)

    assert first.to_dict() == second.to_dict()
    assert payload == before
    record = first.to_dict()["decisions"][0]
    assert set(record["score_breakdown"]) == {
        "silhouette_contribution",
        "part_role",
        "identity_contribution",
        "visual_salience",
        "redundancy",
    }
    assert first.validation["observed_only"] is True
    assert first.validation["pass"] is True


def test_phase8_hard_guards_protect_identity_uncertainty_and_part_maxima() -> None:
    payload, labels, silhouette = _fixture()
    decisions = _by_id(evaluate_importance_omission(payload, labels, silhouette))

    assert decisions["mass-0000"].action == "protect"  # largest hair
    assert decisions["mass-0001"].action == "protect"  # largest torso
    assert decisions["mass-0003"].action == "protect"  # face
    assert decisions["mass-0004"].action == "protect"  # small identity cue
    assert decisions["mass-0005"].action == "protect"  # unbound uncertainty
    assert decisions["mass-0005"].semantic_part_id is None
    assert decisions["mass-0005"].review_status == "deferred-unbound"


def test_phase8_prunes_only_redundant_fragment_with_multiple_low_grounds() -> None:
    payload, labels, silhouette = _fixture()
    decisions = _by_id(evaluate_importance_omission(payload, labels, silhouette))
    fragment = decisions["mass-0002"]

    assert fragment.action == "prune"
    assert fragment.redundancy >= OmissionPolicy().redundancy_threshold
    assert fragment.redundancy_evidence["established"] is True
    assert fragment.redundancy_evidence["reference_mass_id"] == "mass-0000"
    assert len(fragment.low_importance_grounds) >= 2
    assert fragment.omission_reason == (
        "redundant-low-contribution-same-part-fragment"
    )


def test_phase8_does_not_prune_small_mass_without_redundancy() -> None:
    payload, labels, silhouette = _fixture()
    payload["masses"][2]["semantic_part_id"] = "novel_identity_part"
    result = evaluate_importance_omission(payload, labels, silhouette)
    fragment = _by_id(result)["mass-0002"]

    assert fragment.redundancy == 0.0
    assert fragment.action != "prune"


def test_phase8_protects_even_tiny_observed_outer_silhouette_mass() -> None:
    payload, labels, silhouette = _fixture()
    labels[14, 8] = 65535
    labels[0, 0] = 2
    silhouette = (labels != 65535).astype(np.uint8) * 255
    payload["masses"][2]["bbox_xywh"] = [0, 0, 1, 1]
    payload["masses"][2]["centroid_xy"] = [0.0, 0.0]
    payload["masses"][2]["pixel_runs"] = [[0, 0, 1]]
    payload["validation"]["subject_pixel_count"] = int(
        np.count_nonzero(silhouette)
    )

    fragment = _by_id(
        evaluate_importance_omission(payload, labels, silhouette)
    )["mass-0002"]

    assert fragment.action == "protect"
    assert "observed-outer-silhouette-contributor" in fragment.rationale


def test_phase8_rejects_silhouette_or_label_contract_drift() -> None:
    payload, labels, silhouette = _fixture()
    changed_silhouette = silhouette.copy()
    changed_silhouette[0, 0] = 255
    with pytest.raises(ValueError, match="silhouette and mass labels disagree"):
        evaluate_importance_omission(payload, labels, changed_silhouette)

    changed_labels = labels.copy()
    changed_labels[0, 0] = 99
    with pytest.raises(ValueError, match="missing mass"):
        evaluate_importance_omission(payload, changed_labels, changed_labels != 65535)


def _write_phase7_input(
    root: Path,
    payload: dict,
    labels: np.ndarray,
    silhouette: np.ndarray,
) -> tuple[Path, Path, dict]:
    source_path = root / "source.png"
    source = np.full((24, 24, 3), (120, 100, 80), dtype=np.uint8)
    assert cv2.imwrite(str(source_path), cv2.cvtColor(source, cv2.COLOR_RGB2BGR))
    phase7 = root / "phase_07"
    phase7.mkdir()
    (phase7 / "07_masses.json").write_text(
        json.dumps(payload, sort_keys=True), encoding="utf-8"
    )
    assert cv2.imwrite(str(phase7 / "07_mass_labels.png"), labels)
    assert cv2.imwrite(str(phase7 / "07_mass_silhouette.png"), silhouette)
    block = np.full((24, 24, 3), (70, 80, 90), dtype=np.uint8)
    assert cv2.imwrite(str(phase7 / "07_mass_blocks.png"), block)
    assert cv2.imwrite(str(phase7 / "preview.png"), block)
    (phase7 / "metrics.json").write_text('{"pass":true}', encoding="utf-8")
    outputs = {
        name: sha256_file(phase7 / name)
        for name in (
            "07_masses.json",
            "07_mass_labels.png",
            "07_mass_silhouette.png",
            "07_mass_blocks.png",
            "preview.png",
            "metrics.json",
        )
    }
    stage = {
        "phase": 7,
        "source": {
            "path": source_path.name,
            "sha256": sha256_file(source_path),
            "width": 24,
            "height": 24,
        },
        "metrics": {"pass": True},
        "outputs": outputs,
    }
    (phase7 / "stage.json").write_text(
        json.dumps(stage, sort_keys=True), encoding="utf-8"
    )
    return source_path, phase7, stage


def test_phase8_artifacts_bind_every_declared_phase7_output(tmp_path: Path) -> None:
    payload, labels, silhouette = _fixture()
    source_path, phase7, phase7_stage = _write_phase7_input(
        tmp_path, payload, labels, silhouette
    )
    policy = OmissionPolicy()
    result = evaluate_importance_omission(
        payload, labels, silhouette, policy=policy
    )
    output = tmp_path / "phase_08"
    stage = write_phase8_artifacts(
        source_path,
        phase7,
        result,
        output,
        config=policy.to_dict(),
        phase7_stage=phase7_stage,
    )

    mandatory = (
        "08_importance.json",
        "08_importance_heatmap.png",
        "08_pruned_masses.png",
        "08_removed_overlay.png",
        "preview.png",
        "metrics.json",
        "stage.json",
    )
    assert all((output / name).is_file() for name in mandatory)
    assert stage["phase"] == 8
    assert stage["stage"] == "importance_omission_policy"
    assert stage["metrics"]["pass"] is True
    assert stage["provenance_policy"]["generation"] == "forbidden"
    assert stage["provenance_policy"]["unbound_reinterpretation"] == "forbidden"
    assert set(stage["inputs"]["phase7"]) == {
        *phase7_stage["outputs"],
        "stage.json",
    }
    assert sha256_file(output / "preview.png") == sha256_file(
        output / "08_pruned_masses.png"
    )


def test_phase8_writer_rejects_phase7_input_tampering(tmp_path: Path) -> None:
    payload, labels, silhouette = _fixture()
    source_path, phase7, phase7_stage = _write_phase7_input(
        tmp_path, payload, labels, silhouette
    )
    result = evaluate_importance_omission(payload, labels, silhouette)
    (phase7 / "metrics.json").write_text('{"pass":false}', encoding="utf-8")

    with pytest.raises(ValueError, match="input SHA mismatch"):
        write_phase8_artifacts(
            source_path,
            phase7,
            result,
            tmp_path / "phase_08",
            config=OmissionPolicy().to_dict(),
            phase7_stage=phase7_stage,
        )
