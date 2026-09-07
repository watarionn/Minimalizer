from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _scene(name: str, **overrides):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=240,
        target_max_shapes=32,
        line_mode="none",
        enable_auto_retry=False,
        **overrides,
    )
    return minimalize(CORPUS / name, cfg)


def test_outfit_rules_emit_structural_shapes_for_fullbody_character():
    scene = _scene("Rindo-Chihaya_pr-img_01_a.png")
    details = scene.metadata["character"]["details"]["outfit"]

    assert details["enabled"] is True
    assert details["shape_count"] >= 3
    structure = details["structure"]
    assert structure["torso"] is not None
    assert structure["left_shoe"] is not None or structure["right_shoe"] is not None

    outfit_shapes = [s for s in scene.shapes if s.character_part == "outfit"]
    assert any(s.source_role == "character_outfit_torso" for s in outfit_shapes)
    assert any(s.source_role in {"character_sleeve", "character_shoe"} for s in outfit_shapes)


def test_fullbody_budget_reserves_outfit_capacity():
    scene = _scene("Isaki-Riona_pr-img_01_a.png")
    budget = scene.metadata["character"]["budget"]

    assert budget["reserved_outfit"] >= 4
    assert budget["per_part"].get("outfit", 0) == budget["reserved_outfit"]
    assert sum(budget["per_part"].values()) == budget["total"]


def test_outfit_rules_can_be_disabled_independently():
    scene = _scene(
        "Kikirara-Vivi_pr-img_01_a.webp",
        enable_outfit_rules=False,
    )
    details = scene.metadata["character"]["details"]["outfit"]
    assert details["enabled"] is False
    assert details["shape_count"] == 0
