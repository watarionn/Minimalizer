from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.retry import suggest_character_retry_config


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def test_face_geometry_retry_repairs_oversized_face_width():
    base = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
        face_contour_width_scale=1.22,
        character_quality_min_face_geometry=0.90,
    )
    before = minimalize(
        CORPUS / "Rindo-Chihaya_pr-img_01_a.png",
        base,
    )
    after = minimalize(
        CORPUS / "Rindo-Chihaya_pr-img_01_a.png",
        base.with_overrides(
            enable_character_auto_retry=True,
            character_max_retries=1,
        ),
    )

    before_q = before.metadata["character_quality"]
    after_q = after.metadata["character_quality"]

    assert "face_geometry_low" in before_q["retry_reasons"]
    assert after.metadata["face_retry_attempts"] == 1
    assert after_q["face_geometry_score"] > before_q["face_geometry_score"]
    assert "face_geometry_low" not in after_q["retry_reasons"]
    assert any(
        "repair_face_geometry" in item.get("strategy", [])
        for item in after.metadata["face_retry_history"]
    )


def test_face_boundary_retry_can_clear_strict_boundary_gate():
    base = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
        face_boundary_guard_strength=0.30,
        character_quality_min_face_boundary=0.904,
    )
    before = minimalize(
        CORPUS / "Isaki-Riona_pr-img_01_a.png",
        base,
    )
    after = minimalize(
        CORPUS / "Isaki-Riona_pr-img_01_a.png",
        base.with_overrides(
            enable_character_auto_retry=True,
            character_max_retries=1,
        ),
    )

    before_q = before.metadata["character_quality"]
    after_q = after.metadata["character_quality"]

    assert "face_boundary_low" in before_q["retry_reasons"]
    assert after.metadata["face_retry_attempts"] == 1
    assert after_q["face_boundary_score"] > before_q["face_boundary_score"]
    assert "face_boundary_low" not in after_q["retry_reasons"]
    assert any(
        "refine_face_boundary" in item.get("strategy", [])
        for item in after.metadata["face_retry_history"]
    )


def test_face_retry_respects_disabled_contour_fit():
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_face_contour_fit=False,
    )
    updated, info = suggest_character_retry_config(
        cfg,
        {
            "retry_reasons": ["face_geometry_low"],
            "diagnostics": {
                "face_geometry": {
                    "diagnostics": {
                        "generated_to_source_area_ratio": 1.35,
                    }
                }
            },
        },
        {"identity_score": 0.7, "complexity_score": 0.9},
        0,
    )

    assert updated.enable_face_contour_fit is False
    assert "recheck_face_geometry" in info["strategy"]
    assert "repair_face_geometry" not in info["strategy"]


def test_face_retry_debug_artifact_is_written(tmp_path):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
        enable_face_primitives=True,
        enable_character_auto_retry=True,
        character_max_retries=1,
        face_contour_width_scale=1.22,
        character_quality_min_face_geometry=0.90,
        debug_mode=True,
        debug_output_dir=str(tmp_path),
    )
    scene = minimalize(
        CORPUS / "Rindo-Chihaya_pr-img_01_a.png",
        cfg,
    )

    assert scene.metadata["face_retry_attempts"] == 1
    assert (tmp_path / "12_face_retry.json").exists()
