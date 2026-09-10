from pathlib import Path

from minimalize_engine.target_style import minimalize_rinka_reference


CORPUS = Path(__file__).parent / "assets" / "corpus"


def _shape_area(shape) -> float:
    if shape.shape_type == "rectangle":
        return float(shape.width or 0.0) * float(shape.height or 0.0)
    if shape.shape_type == "polygon" and len(shape.points) >= 3:
        pts = shape.points
        return abs(sum(
            pts[i][0] * pts[(i + 1) % len(pts)][1]
            - pts[(i + 1) % len(pts)][0] * pts[i][1]
            for i in range(len(pts))
        )) * 0.5
    if shape.shape_type in {"circle", "ellipse"}:
        import math
        rx = float(shape.rx or 0.0)
        ry = rx if shape.shape_type == "circle" else float(shape.ry or 0.0)
        return math.pi * rx * ry
    return 0.0


def _largest_ratio(scene) -> float:
    canvas = max(float(scene.width * scene.height), 1.0)
    return max((
        _shape_area(shape) / canvas
        for shape in scene.shapes
        if shape.fill_color is not None
        and shape.semantic_type != "target_geometric_background"
    ), default=0.0)


def test_phase8_rescues_omaru_single_slab_failure():
    scene = minimalize_rinka_reference(
        CORPUS / "Omaru-Polka_list_thumb.png",
        4,
        analysis_max_side=220,
        enable_ai_free_subject_segmentation=False,
    )
    rescue = scene.metadata["rinka_opaque_subject_rescue"]
    macro = scene.metadata["rinka_macro_partition"]
    gate = rescue["baseline_gate"]

    assert scene.metadata["target_style"]["version"] == "phase12"
    assert rescue["activated"] is True
    assert gate["largest_shape_ratio"] >= 0.25
    assert gate["second_shape_ratio"] >= 0.22
    assert macro["enabled"] is True
    assert macro["part_shape_counts"]["face"] >= 1
    assert macro["part_shape_counts"]["outfit"] >= 1
    assert _largest_ratio(scene) <= 0.08


def test_phase8_does_not_rescue_subaru_without_two_giant_shapes():
    scene = minimalize_rinka_reference(
        CORPUS / "Oozora-Subaru_list_thumb.png",
        4,
        analysis_max_side=220,
        enable_ai_free_subject_segmentation=False,
    )
    rescue = scene.metadata["rinka_opaque_subject_rescue"]
    macro = scene.metadata.get("rinka_macro_partition", {})
    gate = rescue["baseline_gate"]

    assert scene.metadata["target_style"]["version"] == "phase12"
    assert rescue["enabled"] is True
    assert rescue["activated"] is False
    assert gate["accepted"] is False
    assert gate["second_shape_ratio"] < 0.22
    assert macro.get("enabled", False) is False
