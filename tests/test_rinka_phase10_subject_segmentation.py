from pathlib import Path

import cv2
import numpy as np

from minimalize_engine.subject_segmentation import segment_subject_without_ai
from minimalize_engine.subject_planes import build_subject_color_planes, _is_upper_gesture_representative
from minimalize_engine.subject_plane_cleanup import absorb_small_label_fragments
from minimalize_engine.target_style import minimalize_rinka_reference


CORPUS = Path(__file__).parent / "assets" / "corpus"


def test_phase10_omaru_uses_ai_free_subject_segmentation():
    scene = minimalize_rinka_reference(
        CORPUS / "Omaru-Polka_list_thumb.png",
        4,
        analysis_max_side=220,
    )
    segmentation = scene.metadata["rinka_subject_segmentation"]
    rescue = scene.metadata["rinka_opaque_subject_rescue"]
    macro = scene.metadata["rinka_macro_partition"]

    assert scene.metadata["target_style"]["version"] == "phase16"
    assert segmentation["enabled"] is True
    assert segmentation["activated"] is True
    assert segmentation["confidence"] >= 0.60
    assert segmentation["center_fill_ratio"] >= 0.90
    assert rescue["activated"] is False
    assert rescue["superseded_by_subject_segmentation"] is True
    planes = scene.metadata["rinka_subject_planes"]
    assert macro["enabled"] is False
    assert scene.metadata["subject_mode"] is True
    assert planes["enabled"] is True
    assert planes["color_count"] == 6
    assert 14 <= planes["plane_count"] <= 17
    assert planes["vertex_count"] <= 200
    assert planes["contrast_adjusted_colors"] >= 1
    assert planes["gesture_plane_count"] >= 1
    assert planes["bridge_kernel_size"] == 3
    assert planes["subject_coverage_ratio"] >= 0.68
    assert planes["outside_subject_ratio"] <= 0.03
    assert planes["protected_structure_shapes"] >= 2
    assert planes["replaced_structure_shapes"] >= 20
    assert planes["absorbed_fragment_count"] > 0
    assert planes["suppressed_plane_count"] > 0
    assert planes["macro_anchor_count"] >= 10
    assert segmentation["activation_gate"]["reason"] == "legacy_failure_gate"
    assert scene.metadata["target_style"]["phase10_subject_base_removed"] == 0
    assert any(shape.source_role == "phase10_gesture_plane" and shape.side_hint == "right" for shape in scene.shapes)
    assert any("character_sword_blade" in (shape.source_role or "") for shape in scene.shapes)


def test_phase10_edge_connected_background_keeps_enclosed_matching_color():
    image = np.full((128, 128, 3), (205, 38, 48), dtype=np.uint8)
    cv2.rectangle(image, (30, 18), (98, 116), (35, 32, 38), thickness=-1)
    cv2.rectangle(image, (38, 26), (90, 108), (225, 198, 150), thickness=-1)
    cv2.rectangle(image, (48, 54), (80, 92), (205, 38, 48), thickness=-1)

    result = segment_subject_without_ai(image)

    assert result.enabled is True
    assert result.mask is not None
    assert result.mask[10, 10] == 0
    assert result.mask[70, 64] == 1
    assert result.mask[35, 64] == 1


def test_phase10_existing_alpha_subject_is_not_resegmented():
    rgba = np.zeros((96, 96, 4), dtype=np.uint8)
    rgba[:, :, :3] = (100, 120, 140)
    rgba[20:80, 24:72, 3] = 255
    result = segment_subject_without_ai(rgba)
    assert result.enabled is False
    assert result.reason == "alpha_subject"


def test_phase10_subject_planes_are_deterministic_and_preserve_side_gesture():
    rgba = np.zeros((128, 128, 4), dtype=np.uint8)
    rgba[24:112, 28:92, :3] = (235, 220, 195)
    rgba[24:112, 28:92, 3] = 255
    rgba[24:70, 90:105, :3] = (48, 46, 47)
    rgba[24:70, 90:105, 3] = 255
    rgba[82:116, 18:60, :3] = (70, 145, 210)
    rgba[82:116, 18:60, 3] = 255
    rgba[70:108, 62:92, :3] = (180, 30, 38)
    rgba[70:108, 62:92, 3] = 255

    first = build_subject_color_planes(rgba, 128, 128, (207, 40, 48), max_colors=4)
    second = build_subject_color_planes(rgba, 128, 128, (207, 40, 48), max_colors=4)
    signature = lambda result: [
        (shape.fill_color, shape.semantic_type, shape.side_hint, tuple(shape.points))
        for shape in result.shapes
    ]

    assert first.enabled is True
    assert first.to_dict() == second.to_dict()
    assert signature(first) == signature(second)
    assert first.contrast_adjusted_colors == 1
    assert first.gesture_plane_count == 1
    assert first.subject_coverage_ratio >= 0.90
    assert first.outside_subject_ratio <= 0.03
    assert any(shape.semantic_type == "phase10_gesture_plane" and shape.side_hint == "right" for shape in first.shapes)


def test_phase10_checkpoint3_generalizes_to_opaque_thumbnail_set():
    cases = {
        "Oozora-Subaru_list_thumb.png": "confident_subject",
        "Omaru-Polka_list_thumb.png": "legacy_failure_gate",
        "Shirogane-Noel_list_thumb.png": "confident_subject",
        "Juufuutei-Raden_list_thumb.png": "dense_subject",
    }
    for name, reason in cases.items():
        scene = minimalize_rinka_reference(CORPUS / name, 4, analysis_max_side=220)
        segmentation = scene.metadata["rinka_subject_segmentation"]
        planes = scene.metadata["rinka_subject_planes"]
        assert segmentation["activated"] is True, name
        assert segmentation["activation_gate"]["reason"] == reason, name
        assert planes["enabled"] is True, name
        assert 10 <= planes["plane_count"] <= 17, name
        assert planes["subject_coverage_ratio"] >= 0.64, name
        assert planes["outside_subject_ratio"] <= 0.05, name
        assert planes["macro_anchor_count"] >= 8, name
        assert planes["absorbed_fragment_count"] > 0, name


def test_phase10_checkpoint3_absorbs_neutral_fragment_but_keeps_accent():
    labels = np.zeros((64, 64), dtype=np.int16)
    subject = np.ones((64, 64), dtype=np.uint8)
    labels[20:22, 20:22] = 1
    labels[40:43, 40:43] = 2
    centers = np.asarray([(220, 210, 200), (170, 165, 160), (20, 160, 220)], dtype=np.uint8)
    out, absorbed, pixels, protected = absorb_small_label_fragments(labels, centers, subject)
    assert absorbed >= 1
    assert pixels >= 4
    assert np.all(out[20:22, 20:22] == 0)
    assert np.all(out[40:43, 40:43] == 2)
    assert protected >= 1



def test_phase16_upper_gesture_gate_requires_bright_outer_upper_mass():
    stats = np.asarray([90, 5, 24, 24, 576], dtype=np.int32)
    centroid = np.asarray([102.0, 22.0], dtype=np.float64)
    assert _is_upper_gesture_representative(
        576, stats, centroid, np.asarray((245, 220, 205), dtype=np.uint8), 128, 128, 128 * 128
    )
    assert not _is_upper_gesture_representative(
        576, stats, centroid, np.asarray((90, 85, 88), dtype=np.uint8), 128, 128, 128 * 128
    )
    centered = np.asarray([64.0, 22.0], dtype=np.float64)
    assert not _is_upper_gesture_representative(
        576, stats, centered, np.asarray((245, 220, 205), dtype=np.uint8), 128, 128, 128 * 128
    )
