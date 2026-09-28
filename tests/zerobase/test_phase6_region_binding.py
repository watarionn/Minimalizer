from __future__ import annotations

import copy
import json

import numpy as np
import pytest
from PIL import Image

from minimalizer_zerobase.binding import (
    BindingPolicy,
    bind_labeled_regions,
    build_region_bindings,
    write_phase6_artifacts,
)
from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.subject.artifacts import sha256_file


def _masks(shape=(48, 36)) -> dict[str, np.ndarray]:
    masks = {name: np.zeros(shape, dtype=bool) for name in PART_NAMES}
    masks["hair"][6:42, 4:18] = True
    masks["major_clothing"][6:42, 18:32] = True
    return masks


def _graph() -> dict:
    return {
        "present_parts": ["hair", "major_clothing"],
        "relations": [
            {
                "relation_id": "relation:hair:adjacent:major_clothing",
                "source_part": "hair",
                "target_part": "major_clothing",
                "relation_kind": "adjacent",
            }
        ],
        "validation": {"pass": True},
    }


def _source(shape=(48, 36), *, same_color=False) -> np.ndarray:
    image = np.full((*shape, 3), 245, dtype=np.uint8)
    image[6:42, 4:18] = (35, 35, 35)
    image[6:42, 18:32] = (35, 35, 35) if same_color else (35, 80, 180)
    return image


def _split_labels(shape=(48, 36)) -> np.ndarray:
    labels = np.full(shape, -1, dtype=np.int32)
    labels[6:42, 4:18] = 10
    labels[6:42, 18:32] = 20
    return labels


def test_phase4_overlap_binds_regions_without_mutating_upstream_inputs():
    masks = _masks()
    graph = _graph()
    before_masks = {name: value.copy() for name, value in masks.items()}
    before_graph = copy.deepcopy(graph)

    result = bind_labeled_regions(_source(), _split_labels(), masks, graph)

    assert [region.semantic_part_id for region in result.regions] == [
        "hair",
        "major_clothing",
    ]
    assert all(region.decision_basis == "phase04-mask-overlap" for region in result.regions)
    assert result.validation["pass"] is True
    assert graph == before_graph
    for name in PART_NAMES:
        assert np.array_equal(masks[name], before_masks[name])


def test_dark_hair_and_dark_clothing_do_not_cross_bind_by_color():
    result = bind_labeled_regions(
        _source(same_color=True),
        _split_labels(),
        _masks(),
        _graph(),
    )

    assert [region.semantic_part_id for region in result.regions] == [
        "hair",
        "major_clothing",
    ]
    assert result.validation["color_only_binding_count"] == 0
    assert result.validation["hair_clothing_forced_binding_regions"] == []


def test_cross_part_region_is_left_unbound_when_overlap_is_ambiguous():
    labels = np.full((48, 36), -1, dtype=np.int32)
    labels[6:42, 4:32] = 7

    result = bind_labeled_regions(_source(), labels, _masks(), _graph())
    region = result.regions[0]

    assert region.binding_status == "unbound"
    assert region.semantic_part_id is None
    assert "winner-margin-below-threshold" in region.decision_reasons
    assert result.validation["hair_clothing_crossing_unbound_regions"] == [
        "region-0000"
    ]
    assert result.validation["pass"] is True


def test_hair_clothing_crossing_is_unbound_even_with_a_numeric_winner():
    masks = _masks(shape=(20, 20))
    for mask in masks.values():
        mask[:] = False
    masks["hair"][2:18, 2:12] = True
    masks["major_clothing"][2:18, 12:18] = True
    labels = np.full((20, 20), -1, dtype=np.int32)
    labels[2:18, 2:18] = 3
    image = np.full((20, 20, 3), 50, dtype=np.uint8)

    result = bind_labeled_regions(image, labels, masks, _graph())

    assert result.regions[0].semantic_part_id is None
    assert "crosses-hair-clothing-semantic-boundary" in (
        result.regions[0].decision_reasons
    )
    assert result.validation["hair_clothing_forced_binding_regions"] == []


def test_graph_color_boundary_and_pixel_support_are_retained_as_evidence():
    result = bind_labeled_regions(_source(), _split_labels(), _masks(), _graph())
    hair = result.regions[0]
    payload = hair.to_dict()

    assert hair.pixel_runs
    assert hair.adjacent_regions[0].region_id == "region-0001"
    assert hair.adjacent_regions[0].shared_boundary_pixels > 0
    assert hair.candidates[0].graph_relation_ids == (
        "relation:hair:adjacent:major_clothing",
    )
    assert payload["mean_rgb"] == [35.0, 35.0, 35.0]
    assert "source:rgb-color-statistics" in payload["evidence_refs"]


def test_slic_region_generation_is_deterministic_and_mask_bounded():
    policy = BindingPolicy(n_segments=24, compactness=10.0)
    first = build_region_bindings(_source(), _masks(), _graph(), policy=policy)
    second = build_region_bindings(_source(), _masks(), _graph(), policy=policy)

    assert first.to_dict() == second.to_dict()
    assert np.array_equal(first.region_labels, second.region_labels)
    subject = np.logical_or.reduce(list(_masks().values()))
    assert np.all(first.region_labels[~subject] == -1)
    assert first.validation["pass"] is True


def test_region_labels_fail_closed_when_they_claim_background():
    labels = _split_labels()
    labels[0, 0] = 99
    with pytest.raises(ValueError, match="outside the Phase 4 subject"):
        bind_labeled_regions(_source(), labels, _masks(), _graph())


def test_phase6_artifacts_bind_phase4_and_phase5_inputs(tmp_path):
    source = tmp_path / "case.png"
    Image.fromarray(_source(), mode="RGB").save(source)
    masks = _masks()
    result = bind_labeled_regions(_source(), _split_labels(), masks, _graph())

    phase4 = tmp_path / "phase_04"
    masks_dir = phase4 / "part_masks"
    masks_dir.mkdir(parents=True)
    for name, mask in masks.items():
        Image.fromarray(mask.astype(np.uint8) * 255, mode="L").save(
            masks_dir / f"{name}.png"
        )
    (phase4 / "metrics.json").write_text("{}", encoding="utf-8")
    phase4_stage = {
        "source": {
            "path": source.name,
            "sha256": sha256_file(source),
            "width": 36,
            "height": 48,
        },
        "config_sha256": "phase4-config",
    }
    (phase4 / "stage.json").write_text(
        json.dumps(phase4_stage, sort_keys=True), encoding="utf-8"
    )

    phase5 = tmp_path / "phase_05"
    phase5.mkdir()
    graph_path = phase5 / "05_structure_graph.json"
    graph_path.write_text(json.dumps(_graph(), sort_keys=True), encoding="utf-8")
    (phase5 / "metrics.json").write_text('{"pass": true}', encoding="utf-8")
    phase5_stage = {"config_sha256": "phase5-config"}
    (phase5 / "stage.json").write_text(
        json.dumps(phase5_stage, sort_keys=True), encoding="utf-8"
    )

    output = tmp_path / "phase_06"
    stage = write_phase6_artifacts(
        source,
        phase4,
        phase5,
        result,
        output,
        config={"low_confidence_policy": "unbound"},
        phase4_stage=phase4_stage,
        phase5_stage=phase5_stage,
    )

    mandatory = (
        "06_region_bindings.json",
        "06_region_labels.png",
        "06_region_binding.png",
        "06_unbound_overlay.png",
        "preview.png",
        "metrics.json",
        "stage.json",
    )
    assert all((output / name).is_file() for name in mandatory)
    assert stage["phase"] == 6
    assert stage["stage"] == "region_to_part_binding"
    assert stage["metrics"]["pass"] is True
    assert stage["inputs"]["phase4"]["part_masks/hair.png"] == sha256_file(
        masks_dir / "hair.png"
    )
    assert stage["inputs"]["phase5"]["05_structure_graph.json"] == sha256_file(
        graph_path
    )
    assert sha256_file(output / "preview.png") == sha256_file(
        output / "06_region_binding.png"
    )
