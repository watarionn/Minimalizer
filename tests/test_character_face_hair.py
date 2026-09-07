from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _scene_for(name: str):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=240,
        target_max_shapes=32,
        line_mode="none",
        enable_auto_retry=False,
        enable_face_primitives=True,
    )
    return minimalize(CORPUS / name, cfg)


def test_face_rules_emit_base_eyes_and_mouth_when_available():
    scene = _scene_for("Isaki-Riona_pr-img_01_a.png")
    details = scene.metadata["character"]["details"]["face"]

    assert details["enabled"] is True
    assert details["shape_count"] >= 3

    layout = details["layout"]
    assert layout is not None
    assert layout["left_eye"] is not None or layout["right_eye"] is not None
    assert layout["mouth"] is not None

    face_shapes = [s for s in scene.shapes if s.character_part == "face"]
    assert any(s.source_role == "character_face_base" for s in face_shapes)
    assert any(s.source_role == "character_eye" for s in face_shapes)


def test_hair_rules_emit_base_and_flow_shapes():
    scene = _scene_for("Rindo-Chihaya_pr-img_01_a.png")
    details = scene.metadata["character"]["details"]["hair"]

    assert details["enabled"] is True
    assert details["shape_count"] >= 2
    assert len(details["flows"]) >= 1

    hair_shapes = [s for s in scene.shapes if s.character_part == "hair"]
    assert any(s.source_role == "character_hair_base" for s in hair_shapes)
    assert any(
        s.source_role in {
            "character_bangs",
            "character_side_hair",
            "character_back_hair",
            "character_hair_feature",
        }
        for s in hair_shapes
    )


def test_face_hair_rules_can_be_disabled_independently():
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
        enable_face_primitives=True,
        enable_face_rules=False,
        enable_hair_rules=False,
    )
    scene = minimalize(
        CORPUS / "Kikirara-Vivi_pr-img_01_a.webp",
        cfg,
    )
    details = scene.metadata["character"]["details"]

    assert details["face"]["enabled"] is False
    assert details["hair"]["enabled"] is False
    assert details["face"]["shape_count"] == 0
    assert details["hair"]["shape_count"] == 0


def test_face_refinement_metadata_is_recorded_and_can_shrink_face_mass():
    scene = _scene_for("Isaki-Riona_pr-img_01_a.png")
    structure = scene.metadata["character"]["structure"]
    face_part = next(p for p in structure["parts"] if p["part_type"] == "face")
    refinement = face_part["metadata"]["validation"]["refinement"]

    assert refinement["applied"] is True
    assert refinement["strategy"].startswith("feature_guided_bbox") or refinement["strategy"] == "central_shrink"
    assert refinement["refined_area"] <= refinement["candidate_area"]


def test_hair_candidate_records_generation_strategy_metadata():
    scene = _scene_for("Rindo-Chihaya_pr-img_01_a.png")
    structure = scene.metadata["character"]["structure"]
    hair_part = next(p for p in structure["parts"] if p["part_type"] == "hair")

    assert hair_part["metadata"]["hair_pixels"] > 0
    assert hair_part["metadata"]["candidate_pixels"] > 0
    assert hair_part["metadata"]["strategy"] in {
        "seed_connected_color",
        "candidate_fallback",
        "legacy_zone",
    }
