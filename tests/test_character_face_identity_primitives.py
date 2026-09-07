from pathlib import Path

import numpy as np

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.face_rules import FaceFeatureLayout, build_face_shapes
from minimalize_engine.character.models import CharacterPartCandidate
from minimalize_engine.character.part_types import CharacterPartType


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _dummy_face():
    image = np.full((100, 100, 3), 220, dtype=np.uint8)
    image[39:42, 43:46] = 20
    image[39:42, 55:58] = 25
    image[53:55, 49:52] = 30
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[28:66, 34:66] = 255
    face = CharacterPartCandidate(
        id=1,
        part_type=CharacterPartType.FACE,
        mask=mask,
        bbox=(34, 28, 32, 38),
        centroid=(50.0, 47.0),
        area=int(np.count_nonzero(mask)),
        area_ratio=float(np.count_nonzero(mask) / mask.size),
        confidence=0.9,
        metadata={"contour_fit": {"face_ellipse_bbox": [35, 29, 30, 36]}},
    )
    layout = FaceFeatureLayout(
        face_bbox=(35, 29, 30, 36),
        left_eye=(44.0, 40.0, 0.72),
        right_eye=(57.0, 40.0, 0.93),
        mouth=(50.0, 54.0, 0.80),
        confidence=0.9,
    )
    return image, face, layout


def test_identity_face_renderer_keeps_only_requested_primary_eye_side():
    image, face, layout = _dummy_face()
    shapes = build_face_shapes(
        image,
        face,
        layout,
        5,
        start_id=10,
        identity_reservation={
            "face_base": 1,
            "primary_eye": 1,
            "secondary_eye": 0,
            "mouth": 0,
            "helper": 0,
        },
        primary_eye_side="right",
    )

    assert [shape.source_role for shape in shapes] == [
        "character_face_base",
        "character_eye",
    ]
    eye = shapes[1]
    assert eye.side_hint == "right"
    assert eye.cx == 57.0


def test_identity_face_renderer_can_use_face_base_only():
    image, face, layout = _dummy_face()
    shapes = build_face_shapes(
        image,
        face,
        layout,
        5,
        start_id=20,
        identity_reservation={
            "face_base": 1,
            "primary_eye": 0,
            "secondary_eye": 0,
            "mouth": 0,
            "helper": 0,
        },
        primary_eye_side="left",
    )
    assert len(shapes) == 1
    assert shapes[0].source_role == "character_face_base"


def test_adaptive_identity_rendering_reduces_optional_face_shapes_on_corpus():
    common = dict(
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
    )
    on = minimalize(
        CORPUS / "Rindo-Chihaya_pr-img_01_a.png",
        MinimalizeConfig.from_level(4, **common),
    )
    off = minimalize(
        CORPUS / "Rindo-Chihaya_pr-img_01_a.png",
        MinimalizeConfig.from_level(
            4,
            enable_face_identity_budget=False,
            **common,
        ),
    )

    on_face = on.metadata["character"]["details"]["face"]
    off_face = off.metadata["character"]["details"]["face"]
    assert on_face["shape_count"] == 2
    assert off_face["shape_count"] > on_face["shape_count"]
    assert on_face["identity_rendering"]["released_shape_slots"] >= 1
    assert on_face["identity_rendering"]["plan_fulfilled"] is True
    assert on.metadata["character_quality"]["face_retention_score"] >= 0.95


def test_debug_mode_writes_identity_primitives_json(tmp_path):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=180,
        target_max_shapes=28,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
        debug_mode=True,
        debug_output_dir=str(tmp_path),
    )
    minimalize(CORPUS / "Rindo-Chihaya_pr-img_01_a.png", cfg)
    path = tmp_path / "15_face_identity_primitives.json"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert '"phase": "10.5-c"' in text
    assert '"rendering_changed": true' in text
