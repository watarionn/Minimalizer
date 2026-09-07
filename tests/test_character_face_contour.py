from pathlib import Path

import cv2
import numpy as np

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.face_contour import fit_face_contour


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _scene(name: str, enabled: bool):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=240,
        target_max_shapes=32,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
        enable_face_contour_fit=enabled,
    )
    return minimalize(CORPUS / name, cfg)


def test_face_contour_fit_matches_semantic_mass_on_synthetic_face():
    head = np.zeros((120, 100), dtype=np.uint8)
    cv2.ellipse(head, (50, 48), (28, 34), 0, 0, 360, 255, -1)
    face = np.zeros_like(head)
    cv2.rectangle(face, (37, 34), (64, 68), 255, -1)
    # Bite one upper corner to make the source mask non-elliptical.
    cv2.circle(face, (39, 36), 7, 0, -1)

    result = fit_face_contour(
        None,
        head,
        face,
        face_bbox_hint=(35, 30, 32, 44),
        validation={
            "left_eye": [43.0, 45.0, 0.9],
            "right_eye": [57.0, 45.5, 0.9],
            "mouth": [50.0, 57.0, 0.8],
        },
    )

    source_area = np.count_nonzero(result.refined_mask)
    ellipse_area = result.diagnostics["ellipse_area"]
    ratio = ellipse_area / max(source_area, 1)
    assert result.confidence >= 0.65
    assert 0.72 <= ratio <= 1.36
    assert result.face_ellipse_bbox[2] > 0
    assert result.face_ellipse_bbox[3] > 0


def test_rindo_face_geometry_improves_with_contour_fit():
    off = _scene("Rindo-Chihaya_pr-img_01_a.png", False)
    on = _scene("Rindo-Chihaya_pr-img_01_a.png", True)

    off_score = off.metadata["character_quality"]["face_geometry_score"]
    on_score = on.metadata["character_quality"]["face_geometry_score"]
    assert off_score < 0.72
    assert on_score >= 0.90
    assert on_score > off_score + 0.20


def test_featureless_raden_candidate_no_longer_expands_into_large_oval():
    off = _scene("Juufuutei-Raden_pr-img_01_a.webp", False)
    on = _scene("Juufuutei-Raden_pr-img_01_a.webp", True)

    off_score = off.metadata["character_quality"]["face_geometry_score"]
    on_score = on.metadata["character_quality"]["face_geometry_score"]
    assert on_score > off_score
    assert on_score >= 0.78
    assert "face_geometry_low" not in on.metadata["character_quality"]["retry_reasons"]


def test_contour_fit_metadata_and_face_base_use_same_ellipse():
    scene = _scene("Otonose-Kanade_pr-img_01_a.png", True)
    structure = scene.metadata["character"]["structure"]
    face_part = next(p for p in structure["parts"] if p["part_type"] == "face")
    contour = face_part["metadata"]["contour_fit"]
    assert contour["enabled"] is not False
    assert contour["confidence"] >= 0.60

    face_base = next(
        s for s in scene.shapes
        if s.source_role == "character_face_base"
    )
    x, y, w, h = contour["face_ellipse_bbox"]
    layout = scene.metadata["character"]["layout"]
    scale = float(layout.get("scale", 1.0)) if layout.get("enabled") else 1.0
    tx = float(layout.get("translate_x", 0.0)) if layout.get("enabled") else 0.0
    ty = float(layout.get("translate_y", 0.0)) if layout.get("enabled") else 0.0
    expected_cx = (x + w / 2.0) * scale + tx
    expected_cy = (y + h / 2.0) * scale + ty
    assert abs(face_base.cx - expected_cx) < 1.5
    assert abs(face_base.cy - expected_cy) < 1.5
    assert abs(face_base.rx - (w / 2.0) * scale) < 1.5
    assert abs(face_base.ry - (h / 2.0) * scale) < 1.5


def test_face_contour_fit_can_be_disabled_independently():
    scene = _scene("Isaki-Riona_pr-img_01_a.png", False)
    structure = scene.metadata["character"]["structure"]
    face_part = next(p for p in structure["parts"] if p["part_type"] == "face")
    contour = face_part["metadata"]["contour_fit"]

    assert contour["enabled"] is False
    assert contour["strategy"] == "disabled"
    assert scene.metadata["engine_version"] == "0.3.0"
