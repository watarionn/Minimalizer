from __future__ import annotations

import numpy as np

from minimalize_engine.models import Scene, Shape
from minimalize_engine.subject_segmentation import SubjectSegmentation
from minimalize_engine.target_style import (
    _phase12_face_anchor,
    _phase12_hair_anchor,
    _phase12_portrait_collapse_gate,
    _phase12_repair_quality_gate,
)


def _slab(shape_id: int, x0: float, y0: float, x1: float, y1: float, color=(120, 120, 120)) -> Shape:
    return Shape(
        id=shape_id,
        shape_type="polygon",
        fill_color=color,
        points=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
        z_index=shape_id,
        importance=0.9,
    )


def _candidate_segmentation() -> SubjectSegmentation:
    rgb = np.full((120, 120, 3), (225, 224, 224), dtype=np.uint8)
    mask = np.zeros((120, 120), dtype=np.uint8)
    mask[8:116, 18:102] = 1
    rgb[8:58, 18:102] = (232, 229, 226)
    rgb[34:63, 45:76] = (226, 198, 188)
    rgb[62:116, 28:92] = (42, 38, 46)
    rgba = np.dstack([rgb, mask * 255])
    return SubjectSegmentation(
        False,
        "confidence_gate",
        rgba=rgba,
        mask=mask,
        background_rgb=(165, 230, 208),
        border_dominant_fraction=0.32,
        foreground_area_ratio=0.70,
        center_fill_ratio=0.93,
        border_leak_ratio=0.42,
        confidence=0.50,
    )


def test_phase12_collapse_gate_accepts_three_dominant_portrait_slabs():
    segmentation = _candidate_segmentation()
    scene = Scene(
        120,
        120,
        (165, 230, 208),
        [
            _slab(1, 0, 0, 70, 55),
            _slab(2, 50, 10, 120, 65),
            _slab(3, 15, 58, 105, 92),
        ],
        {"subject_mode": False},
    )
    gate = _phase12_portrait_collapse_gate(segmentation, scene)
    assert gate["accepted"] is True
    assert gate["reason"] == "portrait_collapse_rescue"


def test_phase12_two_slab_poster_rescue_accepts_strong_centered_portrait():
    segmentation = _candidate_segmentation()
    segmentation.border_dominant_fraction = 0.39
    segmentation.foreground_area_ratio = 0.65
    segmentation.center_fill_ratio = 0.95
    segmentation.border_leak_ratio = 0.39
    segmentation.confidence = 0.52
    scene = Scene(
        120,
        120,
        (205, 40, 48),
        [
            _slab(1, 0, 0, 69, 51),
            _slab(2, 51, 4, 120, 55),
            _slab(3, 54, 72, 69, 83),
        ],
        {"subject_mode": False},
    )
    gate = _phase12_portrait_collapse_gate(segmentation, scene)
    assert gate["accepted"] is True
    assert gate["variant"] == "two_slab_poster"


def test_phase12_collapse_gate_rejects_when_third_slab_is_small():
    segmentation = _candidate_segmentation()
    scene = Scene(
        120,
        120,
        (205, 40, 48),
        [
            _slab(1, 0, 0, 72, 55),
            _slab(2, 48, 10, 120, 65),
            _slab(3, 52, 70, 72, 82),
        ],
        {"subject_mode": False},
    )
    gate = _phase12_portrait_collapse_gate(segmentation, scene)
    assert gate["accepted"] is False


def test_phase12_face_anchor_extracts_one_faceless_skin_plane():
    segmentation = _candidate_segmentation()
    anchor, stats = _phase12_face_anchor(segmentation, 120, 120)
    assert anchor is not None
    assert stats["face_anchor_created"] is True
    assert anchor.semantic_type == "character_face_anchor"
    assert anchor.character_part == "face"
    assert anchor.source_role == "phase12_face_anchor"
    assert len(anchor.points) == 6
    assert anchor.fill_color[0] > anchor.fill_color[2]
    assert 0.0015 <= stats["face_anchor_area_ratio"] <= 0.085



def test_phase12_hair_anchor_keeps_one_geometric_hair_mass_behind_face():
    segmentation = _candidate_segmentation()
    face_anchor, _ = _phase12_face_anchor(segmentation, 120, 120)
    assert face_anchor is not None
    hair_anchor, stats = _phase12_hair_anchor(segmentation, 120, 120, face_anchor)
    assert hair_anchor is not None
    assert stats["hair_anchor_created"] is True
    assert hair_anchor.semantic_type == "character_hair_anchor"
    assert hair_anchor.character_part == "hair"
    assert hair_anchor.source_role == "phase12_hair_anchor"
    assert 4 <= len(hair_anchor.points) <= 12
    assert hair_anchor.z_index < face_anchor.z_index

def test_phase12_repair_quality_requires_face_and_body_anchors():
    segmentation = _candidate_segmentation()
    face_anchor, _ = _phase12_face_anchor(segmentation, 120, 120)
    assert face_anchor is not None
    hair_anchor, _ = _phase12_hair_anchor(segmentation, 120, 120, face_anchor)
    assert hair_anchor is not None

    from minimalize_engine.subject_planes import SubjectPlaneResult
    torso = _slab(20, 30, 58, 90, 112, color=(40, 36, 44))
    healthy = SubjectPlaneResult(
        True,
        "accepted",
        shapes=(torso,),
        plane_count=12,
        subject_coverage_ratio=0.82,
        outside_subject_ratio=0.02,
    )
    gate = _phase12_repair_quality_gate(healthy, face_anchor, hair_anchor, 120, 120)
    assert gate["accepted"] is True
    assert gate["torso_anchor_count"] == 1

    missing_body = SubjectPlaneResult(
        True,
        "accepted",
        shapes=(_slab(21, 44, 10, 76, 35),),
        plane_count=12,
        subject_coverage_ratio=0.82,
        outside_subject_ratio=0.02,
    )
    rejected = _phase12_repair_quality_gate(missing_body, face_anchor, hair_anchor, 120, 120)
    assert rejected["accepted"] is False
    assert rejected["reason"] == "torso_anchor_missing"
