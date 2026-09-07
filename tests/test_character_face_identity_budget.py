from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.face_identity import FaceIdentitySignals
from minimalize_engine.character.face_identity_budget import (
    apply_face_identity_budget,
    build_face_identity_plan,
)


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _signals(**overrides) -> FaceIdentitySignals:
    values = dict(
        face_size_score=0.85,
        eye_salience_score=0.78,
        second_eye_salience_score=0.62,
        mouth_salience_score=0.58,
        fringe_relation_score=0.20,
        contour_salience_score=0.66,
        expression_salience_score=0.58,
        primary_eye_side="left",
        visibility_tier="large",
        face_render_scale=0.22,
        face_area_ratio=0.03,
        feature_density_score=0.70,
        abstraction_level=4,
        diagnostics={},
    )
    values.update(overrides)
    return FaceIdentitySignals(**values)


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


def test_phase105c_consumes_adaptive_identity_budget_for_rendering():
    on = _scene("Rindo-Chihaya_pr-img_01_a.png")
    off = _scene(
        "Rindo-Chihaya_pr-img_01_a.png",
        enable_face_identity_budget=False,
    )

    face_meta = on.metadata["character"]["details"]["face"]
    budget = face_meta["identity_budget"]
    rendering = face_meta["identity_rendering"]
    off_face = off.metadata["character"]["details"]["face"]

    assert on.metadata["engine_version"] == "0.3.0"
    assert budget is not None
    assert budget["diagnostics"]["phase"] == "10.5-b"
    assert budget["total_reserved"] <= budget["available_shapes"]
    assert rendering["phase"] == "10.5-c"
    assert rendering["enabled"] is True
    assert rendering["plan_fulfilled"] is True
    assert face_meta["shape_count"] == budget["total_reserved"]
    assert face_meta["shape_count"] < off_face["shape_count"]
    assert off_face["identity_budget"] is None
    assert off_face["identity_rendering"]["enabled"] is False

    roles = [
        s.source_role
        for s in on.shapes
        if s.character_part == "face"
    ]
    assert roles == ["character_face_base", "character_mouth"]
    assert "face_retention_low" not in on.metadata["character_quality"]["retry_reasons"]


def test_large_salient_face_can_request_multiple_cues_but_stays_bounded():
    plan = build_face_identity_plan(
        _signals(),
        available_shapes=8,
        abstraction_level=4,
    )
    result = apply_face_identity_budget(plan, available_shapes=8)

    assert plan.include_face_base is True
    assert plan.include_primary_eye is True
    assert plan.target_shape_count <= 4
    assert result.total_reserved == plan.target_shape_count
    assert result.released_shapes == 8 - result.total_reserved


def test_weak_large_face_does_not_spend_slots_just_because_they_exist():
    plan = build_face_identity_plan(
        _signals(
            eye_salience_score=0.10,
            second_eye_salience_score=0.08,
            mouth_salience_score=0.12,
            fringe_relation_score=0.08,
            contour_salience_score=0.82,
            expression_salience_score=0.10,
            feature_density_score=0.08,
        ),
        available_shapes=7,
        abstraction_level=4,
    )

    assert plan.target_shape_count == 1
    assert plan.minimality_level == "iconic"
    assert set(plan.omitted_features) == {
        "primary_eye",
        "secondary_eye",
        "mouth",
        "helper",
    }


def test_micro_face_never_becomes_a_miniature_full_face():
    plan = build_face_identity_plan(
        _signals(
            visibility_tier="micro",
            face_render_scale=0.05,
            face_size_score=0.04,
            eye_salience_score=1.0,
            second_eye_salience_score=1.0,
            mouth_salience_score=1.0,
            fringe_relation_score=1.0,
            expression_salience_score=1.0,
        ),
        available_shapes=10,
        abstraction_level=4,
    )

    assert plan.max_shape_count <= 2
    assert plan.target_shape_count <= 2


def test_higher_abstraction_never_uses_more_face_slots_for_same_signals():
    signals = _signals(
        visibility_tier="large",
        eye_salience_score=0.90,
        second_eye_salience_score=0.82,
        mouth_salience_score=0.76,
        fringe_relation_score=0.72,
    )
    level3 = build_face_identity_plan(
        signals,
        available_shapes=8,
        abstraction_level=3,
    )
    level5 = build_face_identity_plan(
        signals,
        available_shapes=8,
        abstraction_level=5,
    )
    assert level5.target_shape_count <= level3.target_shape_count
    assert level5.max_shape_count <= level3.max_shape_count


def test_wink_expression_can_keep_one_eye_without_forcing_second_eye():
    plan = build_face_identity_plan(
        _signals(
            visibility_tier="medium",
            eye_salience_score=0.30,
            second_eye_salience_score=0.04,
            mouth_salience_score=0.18,
            fringe_relation_score=0.05,
            expression_salience_score=0.92,
        ),
        available_shapes=5,
        abstraction_level=4,
    )

    assert plan.include_primary_eye is True
    assert plan.include_secondary_eye is False
    assert plan.target_shape_count == 2


def test_available_shape_ceiling_is_hard():
    plan = build_face_identity_plan(
        _signals(
            eye_salience_score=1.0,
            second_eye_salience_score=1.0,
            mouth_salience_score=1.0,
            fringe_relation_score=1.0,
        ),
        available_shapes=4,
        abstraction_level=2,
    )
    result = apply_face_identity_budget(plan, available_shapes=2)
    assert result.total_reserved == 2
    assert sum(result.reserved_shapes.values()) == 2
    assert result.diagnostics["hard_ceiling_respected"] is True


def test_debug_mode_writes_identity_budget_json(tmp_path):
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
    minimalize(CORPUS / "Isaki-Riona_pr-img_01_a.png", cfg)
    path = tmp_path / "14_face_identity_budget.json"
    assert path.exists()
    assert '"phase": "10.5-b"' in path.read_text(encoding="utf-8")
