from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _scene(name: str):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=300,
        target_max_shapes=36,
        line_mode="none",
        enable_auto_retry=False,
    )
    return minimalize(CORPUS / name, cfg)


def _prop_types(scene):
    props = scene.metadata["character"]["details"]["props"]
    return [d["prop_type"] for d in props["descriptors"]]


def test_microphone_is_separated_and_redrawn():
    scene = _scene("Isaki-Riona_pr-img_01_a.png")
    assert "microphone_like" in _prop_types(scene)

    shapes = [s for s in scene.shapes if s.character_part == "prop"]
    assert any(s.source_role == "character_microphone_head" for s in shapes)
    assert any(s.source_role == "character_microphone_body" for s in shapes)


def test_staff_is_separated_and_redrawn():
    scene = _scene("Nerissa-Ravencroft_pr-img_01.webp")
    assert "staff_like" in _prop_types(scene)

    shapes = [s for s in scene.shapes if s.character_part == "prop"]
    assert any(s.source_role == "character_staff" for s in shapes)


def test_bag_is_separated_and_redrawn():
    scene = _scene("Kikirara-Vivi_pr-img_01_a.webp")
    assert "bag_like" in _prop_types(scene)

    shapes = [s for s in scene.shapes if s.character_part == "prop"]
    assert any(s.source_role == "character_bag" for s in shapes)


def test_headphones_are_detected_without_false_positive_on_plain_character():
    scene = _scene("Rindo-Chihaya_pr-img_01_a.png")
    assert "headphone_like" in _prop_types(scene)

    plain = _scene("Koganei-Niko_pr-img_01_a.png")
    assert _prop_types(plain) == []


def test_prop_rules_can_be_disabled():
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=260,
        target_max_shapes=32,
        line_mode="none",
        enable_auto_retry=False,
        enable_prop_rules=False,
    )
    scene = minimalize(CORPUS / "Isaki-Riona_pr-img_01_a.png", cfg)
    props = scene.metadata["character"]["details"]["props"]

    assert props["enabled"] is False
    assert props["shape_count"] == 0
    assert props["descriptors"] == []


def test_prop_detection_is_stable_across_analysis_resolution():
    cases = {
        "Isaki-Riona_pr-img_01_a.png": ["microphone_like"],
        "Rindo-Chihaya_pr-img_01_a.png": ["hat_like", "headphone_like"],
    }
    for name, expected in cases.items():
        seen = []
        for max_side in [300, 640]:
            cfg = MinimalizeConfig.from_level(
                4,
                analysis_max_side=max_side,
                target_max_shapes=36,
                line_mode="none",
                enable_auto_retry=False,
            )
            scene = minimalize(CORPUS / name, cfg)
            seen.append(_prop_types(scene))
        assert seen[0] == expected
        assert seen[1] == expected
