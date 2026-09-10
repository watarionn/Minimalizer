from pathlib import Path

from minimalize_engine.target_style import minimalize_rinka_reference


CORPUS = Path(__file__).parent / "assets" / "corpus"


def test_phase9_omaru_uses_semantic_tree_and_local_primitives():
    scene = minimalize_rinka_reference(
        CORPUS / "Omaru-Polka_list_thumb.png",
        4,
        analysis_max_side=220,
        enable_ai_free_subject_segmentation=False,
    )
    macro = scene.metadata["rinka_macro_partition"]
    tree = macro["semantic_tree"]
    fits = macro["primitive_fits"]
    counts = macro["part_shape_counts"]

    assert scene.metadata["target_style"]["version"] == "phase13"
    assert macro["enabled"] is True
    assert macro["semantic_tree_nodes"] >= 10
    assert tree["root"] == "subject"
    assert tree["nodes"]["face"]["parent"] == "head"
    assert tree["nodes"]["outfit"]["parent"] == "torso"
    assert tree["nodes"]["accessory"]["parent"] == "head"
    assert fits["face:0"]["selected"]["kind"] == "ellipse"
    assert fits["outfit:0"]["selected"]["kind"].startswith("trapezoid_")
    assert counts["face"] == 1
    assert counts["hair"] <= 3
    assert counts["left_arm"] <= 2
    assert counts["right_arm"] <= 2
    assert counts["outfit"] <= 3


def test_phase9_omaru_preserves_distinctive_blue_head_feature():
    scene = minimalize_rinka_reference(
        CORPUS / "Omaru-Polka_list_thumb.png",
        4,
        analysis_max_side=220,
        enable_ai_free_subject_segmentation=False,
    )
    report = scene.metadata["rinka_macro_partition"]["head_features"]
    assert report["enabled"] is True
    assert 1 <= report["selected_shapes"] <= 3
    assert any(color[2] > color[0] and color[2] > color[1] for color in report["colors"])
