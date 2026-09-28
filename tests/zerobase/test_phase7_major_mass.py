from __future__ import annotations

import copy
import json

import numpy as np
import pytest
from PIL import Image

from minimalizer_zerobase.mass import (
    MajorMassPolicy,
    reconstruct_major_masses,
    write_phase7_artifacts,
)
from minimalizer_zerobase.subject.artifacts import sha256_file


def _region(
    region_id: str,
    *,
    part: str | None,
    status: str,
    y0: int,
    y1: int,
    x0: int,
    x1: int,
    adjacent: tuple[tuple[str, int], ...] = (),
) -> dict:
    runs = [[y, x0, x1] for y in range(y0, y1)]
    pixel_count = (y1 - y0) * (x1 - x0)
    return {
        "region_id": region_id,
        "semantic_part_id": part,
        "binding_status": status,
        "binding_confidence": 0.8 if status == "bound" else 0.4,
        "pixel_count": pixel_count,
        "bbox_xywh": [x0, y0, x1 - x0, y1 - y0],
        "centroid_xy": [(x0 + x1 - 1) / 2, (y0 + y1 - 1) / 2],
        "mean_rgb": [40.0, 50.0, 60.0],
        "std_rgb": [0.0, 0.0, 0.0],
        "pixel_runs": runs,
        "adjacent_regions": [
            {
                "region_id": other,
                "shared_boundary_pixels": boundary,
            }
            for other, boundary in adjacent
        ],
        "evidence_refs": [],
    }


def _payload() -> dict:
    regions = [
        _region(
            "region-0000",
            part="hair",
            status="bound",
            y0=1,
            y1=5,
            x0=1,
            x1=4,
            adjacent=(("region-0001", 4),),
        ),
        _region(
            "region-0001",
            part="hair",
            status="bound",
            y0=1,
            y1=5,
            x0=4,
            x1=7,
            adjacent=(("region-0000", 4), ("region-0002", 4)),
        ),
        _region(
            "region-0002",
            part="major_clothing",
            status="bound",
            y0=1,
            y1=5,
            x0=7,
            x1=10,
            adjacent=(("region-0001", 4),),
        ),
        _region(
            "region-0003",
            part=None,
            status="unbound",
            y0=6,
            y1=8,
            x0=4,
            x1=7,
        ),
    ]
    return {
        "schema_version": "1.1",
        "coordinate_space": {
            "pixel_width": 12,
            "pixel_height": 10,
            "normalized_origin": "top-left",
            "normalized_range": [0.0, 1.0],
        },
        "regions": regions,
        "validation": {
            "subject_pixel_count": sum(r["pixel_count"] for r in regions),
            "pass": True,
        },
    }


def _source() -> np.ndarray:
    yy, xx = np.mgrid[0:10, 0:12]
    return np.stack(
        [
            (xx * 11 + 20) % 255,
            (yy * 17 + 30) % 255,
            ((xx + yy) * 9 + 40) % 255,
        ],
        axis=-1,
    ).astype(np.uint8)


def test_same_part_adjacent_regions_merge_into_one_major_mass() -> None:
    result = reconstruct_major_masses(_source(), _payload())
    hair = [mass for mass in result.masses if mass.semantic_part_id == "hair"]
    clothing = [
        mass for mass in result.masses
        if mass.semantic_part_id == "major_clothing"
    ]
    unbound = [mass for mass in result.masses if mass.binding_status == "unbound"]

    assert len(hair) == 1
    assert hair[0].region_ids == ("region-0000", "region-0001")
    assert len(clothing) == 1
    assert clothing[0].region_ids == ("region-0002",)
    assert len(unbound) == 1
    assert result.validation["cross_part_merge_count"] == 0
    assert result.validation["subject_pixel_coverage"] == 1.0
    assert result.validation["pass"] is True


def test_adjacent_regions_from_different_parts_never_merge() -> None:
    result = reconstruct_major_masses(_source(), _payload())
    region_to_mass = {
        region_id: mass.mass_id
        for mass in result.masses
        for region_id in mass.region_ids
    }
    assert region_to_mass["region-0001"] != region_to_mass["region-0002"]


def test_unbound_region_is_not_absorbed_by_neighboring_bound_mass() -> None:
    payload = _payload()
    payload["regions"][2]["adjacent_regions"].append(
        {"region_id": "region-0003", "shared_boundary_pixels": 2}
    )
    payload["regions"][3]["adjacent_regions"].append(
        {"region_id": "region-0002", "shared_boundary_pixels": 2}
    )
    result = reconstruct_major_masses(_source(), payload)
    unbound = [mass for mass in result.masses if mass.binding_status == "unbound"]
    assert len(unbound) == 1
    assert unbound[0].region_ids == ("region-0003",)
    assert result.validation["unbound_absorbed_into_bound_count"] == 0


def test_phase7_is_deterministic_and_does_not_mutate_phase6_payload() -> None:
    payload = _payload()
    before = copy.deepcopy(payload)
    first = reconstruct_major_masses(_source(), payload)
    second = reconstruct_major_masses(_source(), payload)
    assert first.to_dict() == second.to_dict()
    assert np.array_equal(first.mass_labels, second.mass_labels)
    assert payload == before


def test_phase7_rejects_missing_adjacency_target() -> None:
    payload = _payload()
    payload["regions"][0]["adjacent_regions"] = [
        {"region_id": "region-9999", "shared_boundary_pixels": 4}
    ]
    with pytest.raises(ValueError, match="missing region"):
        reconstruct_major_masses(_source(), payload)


def test_phase7_rejects_overlapping_region_pixel_ownership() -> None:
    payload = _payload()
    payload["regions"][3]["pixel_runs"] = [[1, 1, 2]]
    payload["regions"][3]["pixel_count"] = 1
    payload["validation"]["subject_pixel_count"] -= 5
    with pytest.raises(ValueError, match="pixel ownership overlaps"):
        reconstruct_major_masses(_source(), payload)


def test_phase7_policy_rejects_cross_part_merge_authority() -> None:
    with pytest.raises(ValueError, match="forbids cross-part merge"):
        MajorMassPolicy(allow_cross_part_merge=True)


def test_phase7_artifacts_bind_phase6_inputs(tmp_path) -> None:
    source_path = tmp_path / "case.png"
    Image.fromarray(_source(), mode="RGB").save(source_path)
    result = reconstruct_major_masses(_source(), _payload())

    phase6 = tmp_path / "phase_06"
    phase6.mkdir()
    for name, payload in (
        ("06_region_bindings.json", json.dumps(_payload(), sort_keys=True)),
        ("metrics.json", '{"pass": true}'),
        ("stage.json", '{"phase": 6}'),
    ):
        (phase6 / name).write_text(payload, encoding="utf-8")
    Image.fromarray(
        np.zeros((10, 12), dtype=np.uint16)
    ).save(phase6 / "06_region_labels.png")

    phase6_stage = {
        "source": {
            "path": source_path.name,
            "sha256": sha256_file(source_path),
            "width": 12,
            "height": 10,
        },
        "config_sha256": "phase6-config",
    }
    output = tmp_path / "phase_07"
    stage = write_phase7_artifacts(
        source_path,
        phase6,
        result,
        output,
        config=MajorMassPolicy().to_dict(),
        phase6_stage=phase6_stage,
    )

    mandatory = (
        "07_masses.json",
        "07_mass_labels.png",
        "07_mass_silhouette.png",
        "07_mass_blocks.png",
        "07_mass_outline_overlay.png",
        "preview.png",
        "metrics.json",
        "stage.json",
    )
    assert all((output / name).is_file() for name in mandatory)
    assert stage["phase"] == 7
    assert stage["stage"] == "major_mass_reconstruction"
    assert stage["merge_policy"]["cross_part_merge"] == "forbidden-v1"
    assert stage["metrics"]["pass"] is True
    assert stage["inputs"]["phase6"]["06_region_bindings.json"] == sha256_file(
        phase6 / "06_region_bindings.json"
    )
    assert sha256_file(output / "preview.png") == sha256_file(
        output / "07_mass_blocks.png"
    )
    silhouette = np.asarray(Image.open(output / "07_mass_silhouette.png"))
    assert int(np.count_nonzero(silhouette)) == result.validation["subject_pixel_count"]
    preview = np.asarray(Image.open(output / "preview.png").convert("RGB"))
    assert tuple(preview[0, 0]) == (238, 238, 236)


def test_phase7_rejects_nonreciprocal_phase6_adjacency() -> None:
    payload = _payload()
    payload["regions"][1]["adjacent_regions"] = [
        item
        for item in payload["regions"][1]["adjacent_regions"]
        if item["region_id"] != "region-0000"
    ]
    with pytest.raises(ValueError, match="adjacency is not reciprocal"):
        reconstruct_major_masses(_source(), payload)


def test_phase7_policy_rejects_unbound_merge_authority() -> None:
    with pytest.raises(ValueError, match="forbids merging unbound"):
        MajorMassPolicy(merge_unbound_regions=True)


def test_phase7_rejects_nonreciprocal_unbound_adjacency() -> None:
    payload = _payload()
    payload["regions"][3]["adjacent_regions"] = [
        {"region_id": "region-0002", "shared_boundary_pixels": 2}
    ]
    with pytest.raises(ValueError, match="adjacency is not reciprocal"):
        reconstruct_major_masses(_source(), payload)


def test_phase7_writer_rejects_source_contract_mismatch(tmp_path) -> None:
    source_path = tmp_path / "case.png"
    Image.fromarray(_source(), mode="RGB").save(source_path)
    result = reconstruct_major_masses(_source(), _payload())
    with pytest.raises(ValueError, match="source SHA"):
        write_phase7_artifacts(
            source_path,
            tmp_path / "phase_06",
            result,
            tmp_path / "phase_07",
            config=MajorMassPolicy().to_dict(),
            phase6_stage={
                "source": {
                    "path": source_path.name,
                    "sha256": "0" * 64,
                    "width": 12,
                    "height": 10,
                }
            },
        )
