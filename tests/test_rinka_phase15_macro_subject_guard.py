from __future__ import annotations

import numpy as np

from minimalize_engine.macro_subject_guard import build_macro_subject_guard, phase15_subject_candidate
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


def test_phase16_rejected_candidate_does_not_outrank_accepted_opaque_rescue():
    segmentation = _portrait_candidate(confidence=0.52, reason="confidence_gate")
    rescue_rgba = segmentation.rgba.copy()
    rescue_mask = segmentation.mask.copy()
    from minimalize_engine.opaque_subject_rescue import OpaqueSubjectRescue

    rescue = OpaqueSubjectRescue(
        True,
        "accepted",
        rgba=rescue_rgba,
        background_rgb=segmentation.background_rgb,
        border_dominant_fraction=0.62,
        foreground_area_ratio=float(rescue_mask.mean()),
        center_fill_ratio=0.84,
    )
    chosen = phase15_subject_candidate(np.dstack([rescue_rgba[:, :, :3], np.full_like(rescue_mask, 255)]), segmentation, rescue)

    assert chosen.reason == "phase15_opaque_rescue"
    assert chosen is not segmentation


def test_phase16_accepted_candidate_still_has_priority_over_rescue():
    segmentation = _portrait_candidate(confidence=0.64, reason="accepted")
    from minimalize_engine.opaque_subject_rescue import OpaqueSubjectRescue

    rescue = OpaqueSubjectRescue(
        True,
        "accepted",
        rgba=segmentation.rgba.copy(),
        background_rgb=segmentation.background_rgb,
        border_dominant_fraction=0.70,
        foreground_area_ratio=float(segmentation.mask.mean()),
        center_fill_ratio=0.90,
    )
    chosen = phase15_subject_candidate(np.dstack([segmentation.rgba[:, :, :3], np.full_like(segmentation.mask, 255)]), segmentation, rescue)

    assert chosen is segmentation
