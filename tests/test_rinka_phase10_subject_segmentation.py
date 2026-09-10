from pathlib import Path

import cv2
import numpy as np

from minimalize_engine.subject_segmentation import segment_subject_without_ai
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

    assert scene.metadata["target_style"]["version"] == "phase10"
    assert segmentation["enabled"] is True
    assert segmentation["activated"] is True
    assert segmentation["confidence"] >= 0.60
    assert segmentation["center_fill_ratio"] >= 0.90
    assert rescue["activated"] is False
    assert rescue["superseded_by_subject_segmentation"] is True
    assert macro["enabled"] is False
    assert scene.metadata["subject_mode"] is True
    assert scene.metadata["target_style"]["phase10_subject_base_removed"] == 1


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
