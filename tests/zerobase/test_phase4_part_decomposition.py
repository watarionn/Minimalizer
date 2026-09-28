from __future__ import annotations

import json

import numpy as np
import pytest
from PIL import Image, ImageDraw

from minimalizer_zerobase.parts.artifacts import write_phase4_artifacts
from minimalizer_zerobase.parts.decomposition import (
    PART_NAMES,
    decompose_semantic_parts,
    exclusive_part_labels,
)


def _synthetic_case():
    image = Image.new("RGB", (120, 140), (30, 120, 90))
    draw = ImageDraw.Draw(image)
    draw.ellipse((35, 10, 85, 65), fill=(105, 55, 170))
    draw.ellipse((48, 27, 72, 53), fill=(245, 205, 180))
    draw.rectangle((40, 66, 80, 125), fill=(35, 70, 150))
    draw.rectangle((18, 66, 40, 118), fill=(35, 70, 150))
    draw.rectangle((80, 66, 102, 118), fill=(35, 70, 150))
    draw.rectangle((57, 66, 63, 112), fill=(165, 240, 35))
    rgb = np.asarray(image, dtype=np.uint8)

    shape = (140, 120)
    head_img = Image.new("1", (120, 140), 0)
    ImageDraw.Draw(head_img).ellipse((35, 10, 85, 65), fill=1)
    head = np.asarray(head_img, dtype=bool)
    torso = np.zeros(shape, dtype=bool); torso[66:126, 40:81] = True
    left_arm = np.zeros(shape, dtype=bool); left_arm[66:119, 18:40] = True
    right_arm = np.zeros(shape, dtype=bool); right_arm[66:119, 81:103] = True
    left_leg = np.zeros(shape, dtype=bool); left_leg[119:126, 40:60] = True
    right_leg = np.zeros(shape, dtype=bool); right_leg[119:126, 60:81] = True
    subject = head | torso | left_arm | right_arm | left_leg | right_leg
    structural = {
        "head": head & subject,
        "torso": torso & subject,
        "left_arm": left_arm & subject,
        "right_arm": right_arm & subject,
        "left_leg": left_leg & subject,
        "right_leg": right_leg & subject,
    }
    return image, rgb, subject, structural


def test_semantic_decomposition_splits_face_hair_and_body():
    _, rgb, subject, structural = _synthetic_case()
    result = decompose_semantic_parts(
        rgb,
        subject,
        structural,
        structural_quality=0.8,
    )

    assert set(result.part_masks) == set(PART_NAMES)
    assert result.part_masks["face"].sum() > 0
    assert result.part_masks["hair"].sum() > 0
    assert result.part_masks["torso"].sum() > 0
    assert result.part_masks["left_arm"].sum() > 0
    assert result.part_masks["right_arm"].sum() > 0
    assert result.structural_quality == 0.8


def test_vivid_center_accent_becomes_accessory():
    _, rgb, subject, structural = _synthetic_case()
    result = decompose_semantic_parts(rgb, subject, structural)

    assert result.accessory_kind == "vivid-accent"
    assert result.accessory_score > 0
    assert result.part_masks["accessory_or_held_object"].sum() > 0


def test_exclusive_part_labels_keep_background_outside_subject():
    _, rgb, subject, structural = _synthetic_case()
    result = decompose_semantic_parts(rgb, subject, structural)
    labels = exclusive_part_labels(result)

    assert labels.shape == subject.shape
    assert np.all(labels[~subject] == 255)
    assert np.all(labels[subject] != 255)


def test_phase4_artifacts_include_maps_masks_metrics_and_binding(tmp_path):
    image, rgb, subject, structural = _synthetic_case()
    source = tmp_path / "case.png"
    image.save(source)
    phase3 = tmp_path / "phase_03"
    phase3.mkdir()
    Image.fromarray(subject.astype(np.uint8) * 255).save(
        phase3 / "03_subject_mask.png"
    )
    (phase3 / "stage.json").write_text('{"phase":3}', encoding="utf-8")

    result = decompose_semantic_parts(rgb, subject, structural)
    output = tmp_path / "phase_04"
    stage = write_phase4_artifacts(
        source,
        phase3,
        result,
        output,
        config={"structural_provider": "synthetic"},
        structural={"provider": "synthetic", "quality": 1.0},
    )

    assert (output / "04_part_map.png").exists()
    assert (output / "04_part_overlay.png").exists()
    assert (output / "preview.png").exists()
    assert (output / "metrics.json").exists()
    assert (output / "stage.json").exists()
    for name in PART_NAMES:
        assert (output / "part_masks" / f"{name}.png").exists()

    persisted = json.loads((output / "stage.json").read_text(encoding="utf-8"))
    assert persisted["phase"] == 4
    assert persisted["stage"] == "semantic_part_decomposition"
    assert persisted["source"]["sha256"] == stage["source"]["sha256"]
    assert persisted["outputs"]["04_part_map.png"]
    assert persisted["metrics"]["parts_detected"]


def test_high_confidence_hair_hint_prevents_deep_same_color_spill():
    image, rgb, subject, structural = _synthetic_case()
    modified = rgb.copy()
    # Make the torso deliberately hair-colored so color growth alone would be ambiguous.
    modified[62:126, 40:81] = (235, 120, 45)
    hint = np.zeros(subject.shape, dtype=np.float32)
    hint[10:66, 35:86] = 0.95

    result = decompose_semantic_parts(
        modified,
        subject,
        structural,
        semantic_hints={"hair": hint},
    )

    face_bottom = 60
    deep_center = result.part_masks["hair"][face_bottom + 25 :, 45:76]
    assert int(deep_center.sum()) < 120
    assert int(result.part_masks["hair"][10:66, 35:86].sum()) > 200


def test_face68_landmarks_override_shifted_color_locator_geometry():
    _, rgb, subject, structural = _synthetic_case()
    angles = np.linspace(0.0, 2.0 * np.pi, 68, endpoint=False)
    face_landmarks = np.column_stack(
        (
            67.0 + 16.0 * np.cos(angles),
            42.0 + 19.0 * np.sin(angles),
        )
    ).astype(np.float32)
    face_scores = np.full(68, 0.95, dtype=np.float32)

    result = decompose_semantic_parts(
        rgb,
        subject,
        structural,
        face_landmarks=face_landmarks,
        face_landmark_scores=face_scores,
    )

    assert result.face_source == "rtmlib-wholebody-face68"
    assert result.face_landmark_confidence == pytest.approx(0.95)
    assert result.face_bbox_xywh is not None
    x, y, w, h = result.face_bbox_xywh
    assert abs((x + w / 2.0) - 67.0) <= 2.0
    assert abs((y + h / 2.0) - 42.0) <= 2.0
    assert w >= 32
    assert h >= 38
