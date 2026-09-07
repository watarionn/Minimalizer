from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.retry import suggest_character_retry_config


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _scene(name: str, **overrides):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=240,
        target_max_shapes=32,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        **overrides,
    )
    return minimalize(CORPUS / name, cfg)


def test_character_quality_report_uses_character_specific_metrics():
    scene = _scene("Isaki-Riona_pr-img_01_a.png", enable_face_primitives=True)
    cq = scene.metadata["character_quality"]

    assert scene.metadata["engine_version"] == "0.3.0"
    assert cq["score"] >= 0.85
    assert cq["face_applicable"] is True
    assert cq["face_retention_score"] >= 0.79
    assert cq["face_safety_score"] == 1.0
    assert cq["body_readability_score"] >= 0.80
    assert cq["layout_score"] >= 0.72
    assert cq["geometry_fidelity_score"] >= 0.40
    assert cq["retry_reasons"] == []


def test_rejected_face_is_not_penalized_as_missing_face():
    false_face = ROOT / "tests" / "assets" / "false_face_phase85.png"
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=28,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
    )
    scene = minimalize(false_face, cfg)
    cq = scene.metadata["character_quality"]
    validation = scene.metadata["character"]["structure"]["metadata"]["face_validation"]

    assert validation["accepted"] is False
    assert cq["face_applicable"] is False
    assert cq["face_retention_score"] is None
    assert cq["face_safety_score"] == 1.0
    assert "face_retention_low" not in cq["retry_reasons"]
    assert "false_face_generated" not in cq["retry_reasons"]


def test_disabled_body_primitives_are_not_scored_or_reenabled():
    scene = _scene(
        "Rindo-Chihaya_pr-img_01_a.png",
        enable_body_primitives=False,
    )
    cq = scene.metadata["character_quality"]

    assert cq["body_applicable"] is False
    assert cq["body_readability_score"] is None
    assert cq["limb_separation_applicable"] is False
    assert "body_readability_low" not in cq["retry_reasons"]
    assert "limb_separation_low" not in cq["retry_reasons"]


def test_retry_strategy_targets_body_failure_without_overriding_feature_switches():
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_body_primitives=True,
    )
    updated, info = suggest_character_retry_config(
        cfg,
        {
            "retry_reasons": ["body_readability_low"],
            "score": 0.50,
        },
        {"identity_score": 0.70, "complexity_score": 0.90},
        0,
    )

    assert updated.enable_body_primitives is True
    assert updated.analysis_max_side > cfg.analysis_max_side
    assert updated.target_max_shapes >= cfg.target_max_shapes
    assert "recover_body_parts" in info["strategy"]


def test_character_auto_retry_separates_overlapping_limbs():
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=True,
        character_max_retries=1,
        character_limb_width_scale=1.20,
        character_quality_min_limb_separation=0.99,
    )
    scene = minimalize(
        CORPUS / "Rindo-Chihaya_pr-img_01_a.png",
        cfg,
    )

    assert scene.metadata["character_retry_attempts"] == 1
    assert scene.metadata["character_quality"]["limb_separation_score"] >= 0.99
    assert any(
        "separate_limbs" in item.get("strategy", [])
        for item in scene.metadata["retry_history"]
    )


def test_character_auto_retry_improves_poor_layout():
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=True,
        character_max_retries=1,
        character_layout_visual_center_strength=0.0,
        character_quality_min_layout=0.98,
    )
    scene = minimalize(
        CORPUS / "Isaki-Riona_pr-img_01_a.png",
        cfg,
    )

    assert scene.metadata["character_retry_attempts"] == 1
    assert scene.metadata["character_quality"]["layout_score"] >= 0.90
    assert any(
        "normalize_layout" in item.get("strategy", [])
        for item in scene.metadata["retry_history"]
    )


def test_character_quality_can_be_disabled():
    scene = _scene(
        "Isaki-Riona_pr-img_01_a.png",
        enable_character_quality=False,
    )
    assert "character_quality" not in scene.metadata
