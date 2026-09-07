from pathlib import Path

import numpy as np

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.face_identity import FaceIdentitySignals
from minimalize_engine.character.face_identity_budget import FaceIdentityPlan
from minimalize_engine.character.face_identity_validation import (
    apply_single_feature_rollback,
    validate_face_identity_loss,
)
from minimalize_engine.models import Shape


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _signals(**overrides):
    values = dict(
        face_size_score=0.90,
        eye_salience_score=0.86,
        second_eye_salience_score=0.22,
        mouth_salience_score=0.18,
        fringe_relation_score=0.10,
        contour_salience_score=0.55,
        expression_salience_score=0.20,
        primary_eye_side="right",
        visibility_tier="large",
        face_render_scale=0.20,
        face_area_ratio=0.04,
        feature_density_score=0.68,
        abstraction_level=4,
    )
    values.update(overrides)
    return FaceIdentitySignals(**values)


def _plan(**overrides):
    values = dict(
        include_face_base=True,
        include_primary_eye=False,
        include_secondary_eye=False,
        include_mouth=False,
        include_helper=False,
        target_shape_count=1,
        max_shape_count=4,
        minimality_level="iconic",
        feature_priority=["primary_eye", "mouth", "secondary_eye", "helper"],
        omitted_features=["primary_eye", "secondary_eye", "mouth", "helper"],
        utilities={"primary_eye": 0.82, "secondary_eye": 0.18, "mouth": 0.15, "helper": 0.05},
        thresholds={"primary_eye": 0.40, "secondary_eye": 0.54, "mouth": 0.49, "helper": 0.60},
    )
    values.update(overrides)
    return FaceIdentityPlan(**values)


def _face_base():
    return Shape(
        id=1,
        shape_type="ellipse",
        cx=50.0,
        cy=50.0,
        rx=15.0,
        ry=20.0,
        fill_color=(220, 220, 220),
        source_role="character_face_base",
        character_part="face",
    )


def test_identity_loss_validator_requests_only_one_strong_omitted_cue():
    report = validate_face_identity_loss(
        _signals(),
        _plan(),
        [_face_base()],
        min_score=0.80,
    )
    assert report.rollback_recommended is True
    assert report.rollback_feature == "primary_eye"
    repaired, feature = apply_single_feature_rollback(
        {"face_base": 1, "primary_eye": 0, "secondary_eye": 0, "mouth": 0, "helper": 0},
        report,
        available_shapes=4,
    )
    assert feature == "primary_eye"
    assert sum(repaired.values()) == 2


def test_identity_loss_validator_does_not_restore_weak_details():
    plan = _plan(
        utilities={"primary_eye": 0.18, "secondary_eye": 0.10, "mouth": 0.12, "helper": 0.04},
        thresholds={"primary_eye": 0.40, "secondary_eye": 0.54, "mouth": 0.49, "helper": 0.60},
    )
    report = validate_face_identity_loss(
        _signals(feature_density_score=0.18, face_size_score=0.52),
        plan,
        [_face_base()],
        min_score=0.72,
    )
    assert report.rollback_recommended is False
    assert report.rollback_feature is None


def test_adaptive_rollback_never_exceeds_face_budget():
    report = validate_face_identity_loss(
        _signals(),
        _plan(),
        [_face_base()],
        min_score=0.80,
    )
    repaired, feature = apply_single_feature_rollback(
        {"face_base": 1, "primary_eye": 0, "secondary_eye": 0, "mouth": 0, "helper": 0},
        report,
        available_shapes=1,
    )
    assert feature is None
    assert sum(repaired.values()) == 1


def test_corpus_identity_validation_metadata_and_debug(tmp_path):
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
    scene = minimalize(CORPUS / "Rindo-Chihaya_pr-img_01_a.png", cfg)
    face = scene.metadata["character"]["details"]["face"]
    assert face["identity_validation"] is not None
    assert face["identity_validation"]["diagnostics"]["phase"] == "10.5-d"
    assert (tmp_path / "16_face_identity_validation.json").exists()
