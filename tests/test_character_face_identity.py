from pathlib import Path

import numpy as np

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.face_identity import (
    analyze_face_identity_signals,
    estimate_face_render_scale,
    score_mouth_salience,
)
from minimalize_engine.character.face_rules import FaceFeatureLayout
from minimalize_engine.character.models import CharacterPartCandidate, CharacterStructure
from minimalize_engine.character.part_types import CharacterPartType


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _scene(name: str, **overrides):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
        **overrides,
    )
    return minimalize(CORPUS / name, cfg)


def _dummy_face(size: int = 100, bbox=(45, 35, 10, 12)):
    mask = np.zeros((size, size), dtype=np.uint8)
    x, y, w, h = bbox
    mask[y:y+h, x:x+w] = 255
    face = CharacterPartCandidate(
        id=1,
        part_type=CharacterPartType.FACE,
        mask=mask,
        bbox=bbox,
        centroid=(x + w / 2.0, y + h / 2.0),
        area=int(np.count_nonzero(mask)),
        area_ratio=float(np.count_nonzero(mask) / mask.size),
        confidence=0.8,
        metadata={"contour_fit": {"face_ellipse_bbox": list(bbox), "confidence": 0.8}},
    )
    structure = CharacterStructure(
        subject_bbox=(20, 5, 60, 90),
        subject_mask=np.ones((size, size), dtype=np.uint8) * 255,
        parts=[face],
        confidence=0.8,
    )
    return face, structure


def test_phase105a_emits_identity_signals_without_changing_face_rendering():
    on = _scene(
        "Isaki-Riona_pr-img_01_a.png",
        enable_face_identity_budget=False,
    )
    off = _scene(
        "Isaki-Riona_pr-img_01_a.png",
        enable_face_identity_analysis=False,
        enable_face_identity_budget=False,
    )

    signals = on.metadata["character"]["details"]["face"]["identity_signals"]
    assert on.metadata["engine_version"] == "0.3.0"
    assert signals is not None
    assert signals["diagnostics"]["phase"] == "10.5-a"
    assert signals["diagnostics"]["rendering_changed"] is False
    assert off.metadata["character"]["details"]["face"]["identity_signals"] is None

    # 10.5-a is analysis-only. Enabling it must not alter any generated Shape.
    assert on.shapes == off.shapes


def test_identity_signal_scores_are_bounded_and_have_visibility_tier():
    scene = _scene("Rindo-Chihaya_pr-img_01_a.png")
    signals = scene.metadata["character"]["details"]["face"]["identity_signals"]

    for key in [
        "face_size_score",
        "eye_salience_score",
        "second_eye_salience_score",
        "mouth_salience_score",
        "fringe_relation_score",
        "contour_salience_score",
        "expression_salience_score",
        "feature_density_score",
    ]:
        assert 0.0 <= signals[key] <= 1.0
    assert signals["visibility_tier"] in {"micro", "small", "medium", "large"}
    assert signals["primary_eye_side"] in {"left", "right", "none"}


def test_tiny_face_is_classified_as_micro_visibility():
    face, structure = _dummy_face(size=100, bbox=(47, 40, 5, 6))
    image = np.full((100, 100, 3), 220, dtype=np.uint8)
    layout = FaceFeatureLayout(
        face_bbox=face.bbox,
        left_eye=None,
        right_eye=None,
        mouth=None,
    )

    signals = analyze_face_identity_signals(
        image,
        structure,
        face,
        layout,
        abstraction_level=5,
    )

    assert estimate_face_render_scale(structure, face, layout) < 0.07
    assert signals.visibility_tier == "micro"
    assert signals.face_size_score < 0.20
    assert signals.abstraction_level == 5


def test_missing_mouth_has_zero_salience():
    face, structure = _dummy_face()
    image = np.full((100, 100, 3), 210, dtype=np.uint8)
    layout = FaceFeatureLayout(
        face_bbox=face.bbox,
        left_eye=(48.0, 40.0, 0.8),
        right_eye=(52.0, 40.0, 0.7),
        mouth=None,
    )

    score, diagnostics = score_mouth_salience(
        image,
        face,
        layout,
        visibility=0.7,
    )
    assert score == 0.0
    assert diagnostics["mouth_detected"] is False


def test_wink_is_marked_as_high_expression_signal():
    face, structure = _dummy_face(size=100, bbox=(40, 30, 20, 24))
    image = np.full((100, 100, 3), 220, dtype=np.uint8)
    image[39:42, 44:47] = 20
    layout = FaceFeatureLayout(
        face_bbox=face.bbox,
        left_eye=(45.0, 40.0, 0.9),
        right_eye=None,
        mouth=None,
        wink_side="right",
        confidence=0.8,
    )

    signals = analyze_face_identity_signals(image, structure, face, layout)
    assert signals.expression_salience_score >= 0.90
    assert signals.diagnostics["expression"]["wink_side"] == "right"
