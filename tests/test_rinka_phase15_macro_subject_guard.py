from __future__ import annotations

import numpy as np

from minimalize_engine.macro_subject_guard import build_macro_subject_guard
from minimalize_engine.subject_segmentation import SubjectSegmentation


def _portrait_candidate(*, confidence: float = 0.64, reason: str = "accepted") -> SubjectSegmentation:
    height = width = 120
    background = (244, 91, 154)
    rgb = np.full((height, width, 3), background, dtype=np.uint8)
    mask = np.zeros((height, width), dtype=np.uint8)

    mask[14:46, 38:82] = 1
    rgb[14:46, 38:82] = (220, 184, 142)
    mask[42:110, 34:86] = 1
    rgb[42:110, 34:86] = (72, 98, 182)
    mask[45:88, 8:38] = 1
    rgb[45:88, 8:38] = (81, 105, 190)
    mask[45:88, 82:112] = 1
    rgb[45:88, 82:112] = (81, 105, 190)

    rgba = np.dstack([rgb, mask * 255]).astype(np.uint8)
    return SubjectSegmentation(
        enabled=reason == "accepted",
        reason=reason,
        rgba=rgba,
        mask=mask,
        background_rgb=background,
        border_dominant_fraction=0.64,
        foreground_area_ratio=float(mask.mean()),
        center_fill_ratio=0.88,
        border_leak_ratio=0.08,
        confidence=confidence,
    )


def test_phase15_macro_guard_builds_head_torso_and_side_anchors():
    result = build_macro_subject_guard(_portrait_candidate(), 120, 120)

    assert result.enabled is True
    assert result.reason == "macro_subject_anchors"
    assert result.head_anchor_count == 1
    assert result.torso_anchor_count == 1
    assert result.arm_anchor_count == 2
    assert result.subject_coverage_ratio >= 0.28
    assert result.outside_subject_ratio <= 0.28
    assert len(result.shapes) == 4
    assert {shape.character_part for shape in result.shapes} == {
        "head",
        "torso",
        "left_arm",
        "right_arm",
    }
    assert all(3 <= len(shape.points) <= 8 for shape in result.shapes)
    assert all(shape.source_role.startswith("phase15_macro_") for shape in result.shapes)


def test_phase15_macro_guard_accepts_existing_low_confidence_candidate_only_above_floor():
    accepted = build_macro_subject_guard(
        _portrait_candidate(confidence=0.50, reason="confidence_gate"), 120, 120
    )
    rejected = build_macro_subject_guard(
        _portrait_candidate(confidence=0.30, reason="confidence_gate"), 120, 120
    )

    assert accepted.enabled is True
    assert rejected.enabled is False
    assert rejected.reason == "confidence_gate"


def test_phase15_macro_guard_requires_existing_ai_free_subject_candidate():
    segmentation = SubjectSegmentation(False, "border_gate")
    result = build_macro_subject_guard(segmentation, 120, 120)

    assert result.enabled is False
    assert result.reason == "subject_candidate_missing"
    assert result.shapes == ()
