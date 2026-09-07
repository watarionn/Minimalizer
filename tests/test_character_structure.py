from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _part_types(scene):
    ch = scene.metadata.get("character", {})
    assert ch.get("enabled") is True
    return {
        p["part_type"]
        for p in ch["structure"]["parts"]
    }


def test_fullbody_character_detects_core_parts_and_pose_graph():
    path = CORPUS / "Isaki-Riona_pr-img_01_a.png"
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=240,
        target_max_shapes=32,
        line_mode="none",
        enable_auto_retry=False,
    )
    scene = minimalize(path, cfg)

    assert scene.metadata["engine_version"] == "0.3.0"
    types = _part_types(scene)

    assert {"subject", "head", "face", "hair", "torso"} <= types
    assert {"left_leg", "right_leg"} <= types
    assert "left_arm" in types or "right_arm" in types

    graph = scene.metadata["character"]["structure"]["pose_graph"]
    assert graph is not None
    assert graph["confidence"] > 0.45
    assert any(e["relation"] == "head_to_torso" for e in graph["edges"])


def test_character_budget_is_bounded_and_reserves_face_hair():
    path = CORPUS / "Rindo-Chihaya_pr-img_01_a.png"
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
    )
    scene = minimalize(path, cfg)
    budget = scene.metadata["character"]["budget"]

    assert budget["total"] == 30
    assert sum(budget["per_part"].values()) == 30
    assert budget["per_part"].get("face", 0) >= 3
    assert budget["per_part"].get("hair", 0) >= 3


def test_character_engine_stays_off_for_general_scene():
    path = ROOT / "examples" / "input.webp"
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
    )
    scene = minimalize(path, cfg)

    assert scene.metadata["subject_mode"] is False
    assert scene.metadata["character"]["enabled"] is False


def test_character_engine_can_be_disabled():
    path = CORPUS / "Kikirara-Vivi_pr-img_01_a.webp"
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_structure=False,
    )
    scene = minimalize(path, cfg)
    assert scene.metadata["character"]["enabled"] is False
