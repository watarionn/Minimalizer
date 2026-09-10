from __future__ import annotations

import numpy as np

from minimalize_engine.target_style import (
    _phase13_lab_distance,
    _phase13_pick_face_color,
    _phase13_pick_hair_colors,
)


def _pixels(color: tuple[int, int, int], count: int) -> np.ndarray:
    return np.repeat(np.asarray([color], dtype=np.uint8), count, axis=0)


def test_phase13_face_color_prefers_warm_skin_cluster_over_pale_contamination():
    pixels = np.vstack([
        _pixels((226, 198, 188), 90),
        _pixels((232, 229, 226), 35),
        _pixels((210, 227, 219), 10),
    ])
    color, stats = _phase13_pick_face_color(pixels, (165, 230, 208))
    assert stats["enabled"] is True
    assert color[0] > color[1] > color[2]
    assert _phase13_lab_distance(color, (226, 198, 188)) < 8.0


def test_phase13_hair_color_prefers_neutral_silver_over_skin_tinted_median():
    pixels = np.vstack([
        _pixels((232, 229, 226), 120),
        _pixels((226, 201, 193), 70),
        _pixels((205, 211, 214), 30),
    ])
    primary, secondary, stats = _phase13_pick_hair_colors(
        pixels,
        (165, 230, 208),
        (226, 198, 188),
    )
    assert stats["enabled"] is True
    assert _phase13_lab_distance(primary, (232, 229, 226)) < 8.0
    assert _phase13_lab_distance(primary, (226, 198, 188)) >= 13.0
    assert secondary is None or secondary != primary


def test_phase13_hair_color_uses_separated_cluster_when_dominant_is_face_like():
    pixels = np.vstack([
        _pixels((226, 201, 193), 110),
        _pixels((235, 233, 231), 70),
    ])
    primary, _secondary, stats = _phase13_pick_hair_colors(
        pixels,
        (165, 230, 208),
        (226, 198, 188),
    )
    assert stats["enabled"] is True
    assert _phase13_lab_distance(primary, (235, 233, 231)) < 8.0
    assert stats["face_distance"] >= 16.0


def test_phase13_color_stats_are_wired_into_phase12_anchor_geometry():
    from minimalize_engine.subject_segmentation import SubjectSegmentation
    from minimalize_engine.target_style import _phase12_face_anchor, _phase12_hair_anchor

    rgb = np.full((120, 120, 3), (232, 229, 226), dtype=np.uint8)
    mask = np.zeros((120, 120), dtype=np.uint8)
    mask[8:116, 18:102] = 1
    rgb[34:63, 45:76] = (226, 198, 188)
    rgb[62:116, 28:92] = (42, 38, 46)
    segmentation = SubjectSegmentation(
        False,
        "confidence_gate",
        rgba=np.dstack([rgb, mask * 255]),
        mask=mask,
        background_rgb=(165, 230, 208),
    )
    face, face_stats = _phase12_face_anchor(segmentation, 120, 120)
    assert face is not None
    assert "phase13_face_color" in face_stats
    hair, hair_stats = _phase12_hair_anchor(segmentation, 120, 120, face)
    assert hair is not None
    assert "phase13_hair_color" in hair_stats
    assert _phase13_lab_distance(face.fill_color, hair.fill_color) >= 10.0
