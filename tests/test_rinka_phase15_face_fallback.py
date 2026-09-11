from __future__ import annotations

import numpy as np

from minimalize_engine.face_plane_fallback import build_face_plane_fallback
from minimalize_engine.macro_subject_guard import MacroSubjectGuardResult, build_macro_subject_guard
from minimalize_engine.subject_segmentation import SubjectSegmentation


def _candidate() -> SubjectSegmentation:
    height = width = 120
    background = (236, 76, 146)
    rgb = np.full((height, width, 3), background, dtype=np.uint8)
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[12:46, 36:84] = 1
    rgb[12:46, 36:84] = (92, 104, 132)
    mask[22:43, 49:71] = 1
    rgb[22:43, 49:71] = (225, 187, 172)
    mask[42:112, 33:87] = 1
    rgb[42:112, 33:87] = (63, 88, 177)
    mask[46:90, 7:38] = 1
    rgb[46:90, 7:38] = (70, 96, 183)
    mask[46:90, 82:113] = 1
    rgb[46:90, 82:113] = (70, 96, 183)
    return SubjectSegmentation(
        True,
        "accepted",
        rgba=np.dstack([rgb, mask * 255]).astype(np.uint8),
        mask=mask,
        background_rgb=background,
        border_dominant_fraction=0.68,
        foreground_area_ratio=float(mask.mean()),
        center_fill_ratio=0.90,
        border_leak_ratio=0.08,
        confidence=0.70,
    )


def test_phase15_face_fallback_builds_one_blank_skin_plane_from_macro_head():
    segmentation = _candidate()
    macro = build_macro_subject_guard(segmentation, 120, 120)
    result = build_face_plane_fallback(segmentation, macro, 120, 120)

    assert macro.enabled is True
    assert result.enabled is True
    assert result.reason == "fallback_face_plane"
    assert result.shape is not None
    assert result.shape.source_role == "phase15_face_fallback_anchor"
    assert result.shape.character_part == "face"
    assert len(result.shape.points) == 6
    assert result.area_ratio <= 0.085
    assert result.shape.fill_color[0] > result.shape.fill_color[1] > result.shape.fill_color[2]


def test_phase15_face_fallback_refuses_to_run_without_macro_subject_guard():
    segmentation = _candidate()
    disabled_macro = MacroSubjectGuardResult(False, "not_requested")
    result = build_face_plane_fallback(segmentation, disabled_macro, 120, 120)

    assert result.enabled is False
    assert result.reason == "macro_subject_guard_required"
    assert result.shape is None
