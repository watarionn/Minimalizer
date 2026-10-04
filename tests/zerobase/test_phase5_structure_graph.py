from __future__ import annotations

import copy
import json

import numpy as np
from PIL import Image, ImageDraw

from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.structure.artifacts import write_phase5_artifacts
from minimalizer_zerobase.structure.graph import (
    StructuralLayoutGraph,
    build_structural_layout_graph,
    graph_validation,
)
from minimalizer_zerobase.subject.artifacts import sha256_file


def _synthetic_masks() -> dict[str, np.ndarray]:
    shape = (160, 120)
    masks = {name: np.zeros(shape, dtype=bool) for name in PART_NAMES}
    masks["head"][12:58, 38:82] = True
    masks["face"][25:51, 48:72] = True
    masks["hair"][12:29, 38:82] = True
    masks["hair"][29:58, 38:48] = True
    masks["hair"][29:58, 72:82] = True
    masks["neck"][52:68, 54:66] = True
    masks["torso"][68:126, 38:82] = True
    masks["left_arm"][72:124, 82:103] = True
    masks["right_arm"][72:124, 17:38] = True
    masks["lower_body"][126:151, 42:78] = True
    masks["major_clothing"][72:126, 38:45] = True
    masks["accessory_or_held_object"][76:116, 57:63] = True
    return masks


def _synthetic_source(path, masks):
    image = Image.new("RGB", (120, 160), (35, 45, 70))
    draw = ImageDraw.Draw(image)
    draw.ellipse((38, 12, 82, 58), fill=(210, 130, 70))
    draw.rectangle((38, 68, 82, 126), fill=(65, 100, 190))
    image.save(path)
    return image


def _relation_keys(graph):
    return {
        (relation.source_part, relation.relation_kind, relation.target_part)
        for relation in graph.relations
    }


def test_graph_builds_canonical_person_relations_without_mutating_masks():
    masks = _synthetic_masks()
    before = {name: mask.copy() for name, mask in masks.items()}
    graph = build_structural_layout_graph(
        masks,
        accessory_kind="vivid-accent",
        accessory_confidence=0.8,
    )
    relations = _relation_keys(graph)

    assert ("head", "above", "torso") in relations
    assert ("face", "inside", "head") in relations
    assert ("hair", "surrounds", "face") in relations
    assert ("left_arm", "attached_to", "torso") in relations
    assert ("right_arm", "attached_to", "torso") in relations
    assert ("accessory_or_held_object", "attached_to", "torso") in relations
    assert graph.to_dict()["validation"]["pass"] is True
    for name in PART_NAMES:
        assert np.array_equal(masks[name], before[name])


def test_held_linear_accessory_attaches_to_nearest_arm():
    masks = _synthetic_masks()
    masks["accessory_or_held_object"][:] = False
    # The line overlaps the broad structural head mask, but its semantic kind
    # says it is held. Phase 5 must prefer the nearest arm candidate.
    masks["accessory_or_held_object"][50:65, 30:42] = True
    graph = build_structural_layout_graph(
        masks,
        accessory_kind="held-linear",
        accessory_confidence=0.7,
    )
    assert (
        "accessory_or_held_object",
        "attached_to",
        "right_arm",
    ) in _relation_keys(graph)


def test_graph_serialization_is_deterministic_and_normalized():
    masks = _synthetic_masks()
    first = build_structural_layout_graph(masks).to_dict()
    second = build_structural_layout_graph(masks).to_dict()

    assert first == second
    assert first["schema_version"] == "1.0"
    for anchor in first["anchors"]:
        assert 0.0 <= anchor["xy_normalized"][0] <= 1.0
        assert 0.0 <= anchor["xy_normalized"][1] <= 1.0


def test_unsupported_accessory_attachment_fails_closed():
    masks = _synthetic_masks()
    masks["accessory_or_held_object"][:] = False
    masks["accessory_or_held_object"][0:3, 0:3] = True
    graph = build_structural_layout_graph(
        masks,
        accessory_kind="none",
        accessory_confidence=0.0,
    )

    validation = graph.to_dict()["validation"]
    assert validation["missing_accessory_attachment"] is True
    assert validation["pass"] is False


def test_phase5_artifacts_bind_phase4_inputs_and_emit_mandatory_files(tmp_path):
    masks = _synthetic_masks()
    source = tmp_path / "case.png"
    _synthetic_source(source, masks)
    phase4 = tmp_path / "phase_04"
    masks_dir = phase4 / "part_masks"
    masks_dir.mkdir(parents=True)
    for name, mask in masks.items():
        Image.fromarray(mask.astype(np.uint8) * 255, mode="L").save(
            masks_dir / f"{name}.png"
        )
    (phase4 / "metrics.json").write_text("{}", encoding="utf-8")
    phase4_stage = {
        "config_sha256": "phase4-config",
        "structural": {"provider": "synthetic", "model": "fixture"},
    }
    (phase4 / "stage.json").write_text(
        json.dumps(phase4_stage, sort_keys=True),
        encoding="utf-8",
    )
    graph = build_structural_layout_graph(
        masks,
        accessory_kind="vivid-accent",
        accessory_confidence=0.8,
    )
    output = tmp_path / "phase_05"
    stage = write_phase5_artifacts(
        source,
        phase4,
        masks,
        graph,
        output,
        config={"mask_mutation": "forbidden"},
        phase4_stage=phase4_stage,
    )

    for name in (
        "05_structure_graph.json",
        "05_structure_graph_overlay.png",
        "preview.png",
        "metrics.json",
        "stage.json",
    ):
        assert (output / name).is_file()
    assert sha256_file(output / "05_structure_graph_overlay.png") == sha256_file(
        output / "preview.png"
    )
    assert stage["phase"] == 5
    assert stage["stage"] == "structural_layout_graph"
    assert stage["metrics"]["pass"] is True
    assert set(stage["inputs"]["phase4"]) >= {
        "stage.json",
        "metrics.json",
        "part_masks/head.png",
    }


def test_missing_or_mismatched_phase4_masks_fail_local():
    masks = _synthetic_masks()
    missing = copy.copy(masks)
    missing.pop("face")
    try:
        build_structural_layout_graph(missing)
    except ValueError as exc:
        assert "missing Phase 4 part masks" in str(exc)
    else:
        raise AssertionError("missing Phase 4 mask must fail")

    mismatched = copy.copy(masks)
    mismatched["face"] = np.zeros((20, 20), dtype=bool)
    try:
        build_structural_layout_graph(mismatched)
    except ValueError as exc:
        assert "share one shape" in str(exc)
    else:
        raise AssertionError("mismatched Phase 4 mask must fail")


def test_hair_face_depth_is_left_unresolved_for_whole_hair_mask():
    graph = build_structural_layout_graph(_synthetic_masks())
    relations = _relation_keys(graph)

    assert ("hair", "surrounds", "face") in relations
    assert ("hair", "behind", "face") not in relations
    assert ("hair", "in_front_of", "face") not in relations


def test_missing_face_inside_head_is_a_core_gate_failure():
    graph = build_structural_layout_graph(_synthetic_masks())
    filtered = tuple(
        relation
        for relation in graph.relations
        if not (
            relation.source_part == "face"
            and relation.relation_kind == "inside"
            and relation.target_part == "head"
        )
    )
    broken = StructuralLayoutGraph(
        width=graph.width,
        height=graph.height,
        present_parts=graph.present_parts,
        anchors=graph.anchors,
        relations=filtered,
    )

    validation = graph_validation(broken)
    assert "face-inside-head" in validation["missing_core_relations"]
    assert validation["pass"] is False


def test_tiny_neck_may_use_conservative_extended_torso_gap():
    masks = _synthetic_masks()
    masks["neck"][:] = False
    masks["neck"][55:57, 54:59] = True
    masks["torso"][:] = False
    masks["torso"][66:126, 38:82] = True
    graph = build_structural_layout_graph(masks)
    relation = next(
        item for item in graph.relations
        if item.source_part == "neck"
        and item.relation_kind == "attached_to"
        and item.target_part == "torso"
    )
    assert relation.confidence <= 0.55
    assert "derived:tiny-neck-conservative-gap" in relation.evidence_refs
    assert graph.to_dict()["validation"]["pass"] is True
