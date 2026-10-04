from __future__ import annotations

import json

import numpy as np
import pytest
from PIL import Image, ImageDraw

from minimalizer_zerobase.parts.artifacts import write_phase4_artifacts
from minimalizer_zerobase.parts.decomposition import (
    PART_NAMES,
    _detect_vivid_torso_accent,
    _rescue_bright_face_side_hair_strands,
    _rescue_face_side_hair_strands,
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



def test_semantic_head_evidence_excludes_remote_structural_head_spill():
    _, rgb, subject, structural = _synthetic_case()
    structural = {name: mask.copy() for name, mask in structural.items()}
    remote = np.zeros_like(subject)
    remote[66:86, 18:38] = True
    remote &= subject
    structural["head"] |= remote

    angles = np.linspace(0.0, 2.0 * np.pi, 68, endpoint=False)
    face_landmarks = np.column_stack(
        (
            60.0 + 13.0 * np.cos(angles),
            40.0 + 15.0 * np.sin(angles),
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

    assert not np.any(result.part_masks["head"] & remote)
    assert np.any(result.part_masks["head"] & result.part_masks["face"])

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


def test_face_side_bright_hair_strand_is_rescued_without_remote_skin_spill():
    shape = (100, 100)
    rgb = np.full((*shape, 3), 35, dtype=np.uint8)
    face = np.zeros(shape, dtype=bool)
    face[20:45, 45:65] = True
    hair = np.zeros(shape, dtype=bool)
    hair[10:20, 35:75] = True
    hair[10:45, 35:45] = True
    hair[10:45, 65:75] = True

    strand = np.zeros(shape, dtype=bool)
    strand[43:75, 39:44] = True
    rgb[strand] = (190, 170, 160)

    remote_skin = np.zeros(shape, dtype=bool)
    remote_skin[25:35, 5:12] = True
    rgb[remote_skin] = (235, 200, 190)

    subject = face | hair | strand | remote_skin
    rescued = _rescue_face_side_hair_strands(rgb, subject, face, hair)

    assert int(np.count_nonzero(rescued & strand)) >= 120
    assert not np.any(rescued & remote_skin)


def test_vivid_torso_accent_can_extend_just_outside_structural_torso():
    shape = (100, 100)
    rgb = np.full((*shape, 3), (42, 42, 47), dtype=np.uint8)
    subject = np.zeros(shape, dtype=bool)
    face = np.zeros(shape, dtype=bool)
    torso = np.zeros(shape, dtype=bool)
    face[10:30, 35:65] = True
    torso[35:90, 35:76] = True
    subject |= face | torso

    accent = np.zeros(shape, dtype=bool)
    accent[52:82, 25:31] = True
    subject |= accent
    rgb[accent] = (190, 105, 72)

    result = _detect_vivid_torso_accent(rgb, subject, torso, face)

    assert result is not None
    mask, score = result
    assert int(np.count_nonzero(mask & accent)) >= 150
    assert score > 0.60


def test_bright_face_side_hair_rescue_uses_existing_hair_color_and_proximity():
    shape = (120, 120)
    rgb = np.full((*shape, 3), (35, 35, 40), dtype=np.uint8)
    subject = np.zeros(shape, dtype=bool)
    face = np.zeros(shape, dtype=bool)
    hair = np.zeros(shape, dtype=bool)

    face[30:60, 45:75] = True
    rgb[face] = (235, 205, 195)
    hair[18:30, 35:85] = True
    hair[18:64, 35:45] = True
    hair[18:64, 75:85] = True
    rgb[hair] = (58, 52, 62)

    bright_seed = np.zeros(shape, dtype=bool)
    bright_seed[44:62, 37:44] = True
    hair |= bright_seed
    rgb[bright_seed] = (208, 196, 190)

    strand = np.zeros(shape, dtype=bool)
    strand[62:88, 36:43] = True
    rgb[strand] = (205, 194, 189)

    remote_same_color = np.zeros(shape, dtype=bool)
    remote_same_color[70:88, 5:12] = True
    rgb[remote_same_color] = (205, 194, 189)

    nearby_wrong_color = np.zeros(shape, dtype=bool)
    nearby_wrong_color[64:78, 77:83] = True
    rgb[nearby_wrong_color] = (210, 105, 65)

    subject |= face | hair | strand | remote_same_color | nearby_wrong_color
    rescued = _rescue_bright_face_side_hair_strands(
        rgb, subject, face, hair
    )

    assert int(np.count_nonzero(rescued & strand)) >= 120
    assert not np.any(rescued & remote_same_color)
    assert not np.any(rescued & nearby_wrong_color)


def test_secondary_vivid_accents_recover_shoulders_but_not_face_or_wrong_color():
    from minimalizer_zerobase.parts.decomposition import (
        _recover_secondary_vivid_accents,
    )

    shape = (120, 120)
    rgb = np.full((*shape, 3), (42, 42, 47), dtype=np.uint8)
    subject = np.zeros(shape, dtype=bool)
    face = np.zeros(shape, dtype=bool)
    torso = np.zeros(shape, dtype=bool)

    face[30:55, 45:75] = True
    torso[50:105, 25:95] = True
    subject |= face | torso

    primary = np.zeros(shape, dtype=bool)
    primary[78:108, 38:46] = True
    rgb[primary] = (190, 105, 72)
    subject |= primary

    left_shoulder = np.zeros(shape, dtype=bool)
    left_shoulder[56:63, 30:35] = True
    rgb[left_shoulder] = (170, 88, 66)
    subject |= left_shoulder

    right_shoulder = np.zeros(shape, dtype=bool)
    right_shoulder[57:64, 84:90] = True
    rgb[right_shoulder] = (182, 96, 70)
    subject |= right_shoulder

    face_warm = np.zeros(shape, dtype=bool)
    face_warm[42:49, 61:66] = True
    rgb[face_warm] = (170, 105, 95)
    subject |= face_warm

    wrong_color = np.zeros(shape, dtype=bool)
    wrong_color[58:65, 76:82] = True
    rgb[wrong_color] = (65, 150, 190)
    subject |= wrong_color

    recovered = _recover_secondary_vivid_accents(
        rgb, subject, torso, face, primary
    )

    assert int(np.count_nonzero(recovered & left_shoulder)) >= 20
    assert int(np.count_nonzero(recovered & right_shoulder)) >= 20
    assert not np.any(recovered & face_warm)
    assert not np.any(recovered & wrong_color)


def test_hair_like_unknown_rescue_prefers_hair_color_over_competitors_and_requires_contact():
    from minimalizer_zerobase.parts.decomposition import (
        _rescue_hair_like_unknown_components,
    )

    shape = (100, 100)
    rgb = np.full((*shape, 3), (24, 24, 28), dtype=np.uint8)
    hair = np.zeros(shape, dtype=bool)
    hair[20:55, 35:55] = True
    rgb[hair] = (60, 55, 70)

    left_arm = np.zeros(shape, dtype=bool)
    left_arm[55:90, 10:30] = True
    rgb[left_arm] = (40, 42, 45)
    right_arm = np.zeros(shape, dtype=bool)
    right_arm[55:90, 70:90] = True
    rgb[right_arm] = (42, 43, 47)
    clothing = np.zeros(shape, dtype=bool)
    clothing[60:90, 35:65] = True
    rgb[clothing] = (39, 41, 44)
    torso = np.zeros(shape, dtype=bool)
    torso[45:70, 38:62] = True
    rgb[torso] = (44, 44, 49)

    hair_tail = np.zeros(shape, dtype=bool)
    hair_tail[40:68, 55:65] = True
    rgb[hair_tail] = (62, 57, 72)

    clothing_like = np.zeros(shape, dtype=bool)
    clothing_like[35:58, 25:34] = True
    rgb[clothing_like] = (41, 42, 45)

    remote_hair_color = np.zeros(shape, dtype=bool)
    remote_hair_color[75:90, 75:90] = True
    rgb[remote_hair_color] = (62, 57, 72)

    unknown = hair_tail | clothing_like | remote_hair_color
    rescued = _rescue_hair_like_unknown_components(
        rgb,
        unknown,
        hair,
        {
            "left_arm": left_arm,
            "right_arm": right_arm,
            "major_clothing": clothing,
            "torso": torso,
        },
    )

    assert np.count_nonzero(rescued & hair_tail) == np.count_nonzero(hair_tail)
    assert not np.any(rescued & clothing_like)
    assert not np.any(rescued & remote_hair_color)


def test_large_unknown_owner_rescue_requires_contact_color_and_clear_winner():
    from minimalizer_zerobase.parts.decomposition import (
        _rescue_large_unknown_components_by_owner,
    )

    shape = (120, 120)
    rgb = np.full((*shape, 3), (18, 18, 22), dtype=np.uint8)

    right_arm = np.zeros(shape, dtype=bool)
    right_arm[20:45, 12:24] = True
    rgb[right_arm] = (40, 42, 46)

    left_arm = np.zeros(shape, dtype=bool)
    left_arm[20:45, 92:104] = True
    rgb[left_arm] = (70, 68, 74)

    clothing = np.zeros(shape, dtype=bool)
    clothing[62:88, 58:78] = True
    rgb[clothing] = (36, 35, 38)

    torso = np.zeros(shape, dtype=bool)
    torso[62:88, 79:96] = True
    rgb[torso] = (54, 53, 58)

    sleeve_unknown = np.zeros(shape, dtype=bool)
    sleeve_unknown[22:43, 24:42] = True
    rgb[sleeve_unknown] = (39, 41, 45)

    clothing_unknown = np.zeros(shape, dtype=bool)
    clothing_unknown[64:86, 40:58] = True
    rgb[clothing_unknown] = (37, 36, 39)

    remote_unknown = np.zeros(shape, dtype=bool)
    remote_unknown[94:108, 48:62] = True
    rgb[remote_unknown] = (39, 41, 45)

    unknown = sleeve_unknown | clothing_unknown | remote_unknown
    subject = (
        unknown
        | right_arm
        | left_arm
        | clothing
        | torso
    )

    rescued = _rescue_large_unknown_components_by_owner(
        rgb,
        subject,
        unknown,
        {
            "left_arm": left_arm,
            "right_arm": right_arm,
            "major_clothing": clothing,
            "torso": torso,
        },
    )

    assert np.count_nonzero(
        rescued["right_arm"] & sleeve_unknown
    ) == np.count_nonzero(sleeve_unknown)
    assert np.count_nonzero(
        rescued["major_clothing"] & clothing_unknown
    ) == np.count_nonzero(clothing_unknown)
    assert not any(
        np.any(mask & remote_unknown)
        for mask in rescued.values()
    )


def test_semantic_head_evidence_fails_closed_on_large_structural_shrinkage():
    shape = (120, 120)
    subject = np.ones(shape, dtype=bool)
    structural_head = np.zeros(shape, dtype=bool)
    structural_head[12:92, 20:100] = True
    face = np.zeros(shape, dtype=bool)
    face[28:58, 45:75] = True

    from minimalizer_zerobase.parts.decomposition import _semantic_head_mask

    refined = _semantic_head_mask(structural_head, face, subject)

    # Face-local evidence may refine a head only when it preserves most of the
    # structural envelope. Large destructive shrinkage must fail closed.
    assert np.array_equal(refined, structural_head)


def test_bright_hair_rescue_chroma_guard_rejects_pale_face_adjacent_region():
    shape = (120, 120)
    rgb = np.full((*shape, 3), (35, 35, 40), dtype=np.uint8)
    subject = np.zeros(shape, dtype=bool)
    face = np.zeros(shape, dtype=bool)
    hair = np.zeros(shape, dtype=bool)
    face[30:60, 45:75] = True
    rgb[face] = (235, 205, 195)
    hair[18:64, 35:45] = True
    hair[18:30, 35:85] = True
    rgb[hair] = (55, 48, 65)
    pale = np.zeros(shape, dtype=bool)
    pale[62:90, 36:43] = True
    rgb[pale] = (205, 192, 185)
    subject |= face | hair | pale

    candidate = _rescue_bright_face_side_hair_strands(rgb, subject, face, hair)
    if np.any(candidate):
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
        hair_lab = np.median(lab[hair], axis=0)
        candidate_lab = np.median(lab[candidate], axis=0)
        chroma_distance = float(
            np.linalg.norm(candidate_lab[1:] - hair_lab[1:])
        )
        assert chroma_distance > 6.0
