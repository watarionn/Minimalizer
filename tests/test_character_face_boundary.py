from pathlib import Path

import cv2
import numpy as np

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.face_boundary import apply_face_boundary_guard


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def test_boundary_guard_removes_cheek_intrusion_but_keeps_forehead_bangs():
    h = w = 180
    face = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(face, (90, 82), (28, 38), 0, 0, 360, 255, -1)

    hair = np.zeros_like(face)
    # Legal forehead bangs.
    cv2.rectangle(hair, (77, 42), (103, 59), 255, -1)
    # Illegal side-hair intrusion into the eye/cheek protection halo.
    cv2.rectangle(hair, (57, 70), (72, 112), 255, -1)

    head = np.zeros_like(face)
    cv2.ellipse(head, (90, 72), (45, 55), 0, 0, 360, 255, -1)
    subject = cv2.bitwise_or(head, hair)

    result = apply_face_boundary_guard(
        None,
        face_mask=face,
        hair_mask=hair,
        head_mask=head,
        subject_mask=subject,
        validation={
            "left_eye": [80, 78, 0.9],
            "right_eye": [100, 78, 0.9],
            "mouth": [90, 100, 0.8],
        },
        guard_strength=0.70,
    )

    assert result.diagnostics["conflict_pixels_before"] > 0
    assert result.diagnostics["conflict_pixels_after"] == 0
    assert np.count_nonzero(result.hair_mask[42:60, 77:104]) > 0
    assert np.count_nonzero(result.hair_mask[76:108, 58:71]) < np.count_nonzero(hair[76:108, 58:71])
    assert np.array_equal(result.face_mask, face)


def test_boundary_guard_is_recorded_in_character_metadata():
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=240,
        target_max_shapes=32,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
    )
    scene = minimalize(CORPUS / "Isaki-Riona_pr-img_01_a.png", cfg)
    boundary = scene.metadata["character"]["structure"]["metadata"]["face_boundary"]
    cq = scene.metadata["character_quality"]

    assert boundary["enabled"] is True
    assert 0.0 <= boundary["boundary_score_hint"] <= 1.0
    assert boundary["diagnostics"]["conflict_pixels_after"] <= boundary["diagnostics"]["conflict_pixels_before"]
    assert cq["face_boundary_applicable"] is True
    assert cq["face_boundary_score"] == boundary["boundary_score_hint"]


def test_boundary_guard_can_be_disabled_without_disabling_face_or_hair():
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
        enable_face_boundary_guard=False,
    )
    scene = minimalize(CORPUS / "Rindo-Chihaya_pr-img_01_a.png", cfg)
    structure = scene.metadata["character"]["structure"]
    boundary = structure["metadata"]["face_boundary"]
    parts = {p["part_type"] for p in structure["parts"]}

    assert boundary["enabled"] is False
    assert "face" in parts
    assert "hair" in parts
    assert scene.metadata["character_quality"]["face_boundary_applicable"] is False
    assert scene.metadata["character_quality"]["face_boundary_score"] is None


def test_boundary_debug_artifacts_are_written(tmp_path):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
        debug_mode=True,
        debug_output_dir=str(tmp_path),
    )
    minimalize(CORPUS / "Isaki-Riona_pr-img_01_a.png", cfg)

    assert (tmp_path / "11_face_boundary.png").exists()
    assert (tmp_path / "11_face_boundary.json").exists()
