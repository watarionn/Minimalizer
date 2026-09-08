import numpy as np

from minimalize_engine.models import Scene, Shape
from minimalize_engine.target_hierarchy import (
    OpaqueSubjectHierarchy,
    dominant_shape_zone,
    estimate_opaque_subject_hierarchy,
    estimate_opaque_subject_zones,
    estimate_structure_subject_zones,
    shape_subject_overlap,
)


def _scene(width=200, height=160):
    return Scene(
        width,
        height,
        (235, 235, 230),
        [],
        metadata={"subject_mode": False, "source_has_alpha": False},
    )


def test_opaque_hierarchy_detects_distinct_central_subject():
    image = np.full((160, 200, 3), (232, 232, 226), dtype=np.uint8)
    image[28:145, 58:148] = (45, 58, 76)
    image[48:92, 82:128] = (198, 170, 148)

    hierarchy = estimate_opaque_subject_hierarchy(image, _scene())

    assert hierarchy.enabled is True
    assert hierarchy.confidence >= 0.56
    assert 0.10 <= hierarchy.subject_area_ratio <= 0.55
    assert hierarchy.bbox is not None


def test_opaque_hierarchy_stays_off_for_flat_image():
    image = np.full((160, 200, 3), (120, 130, 140), dtype=np.uint8)

    hierarchy = estimate_opaque_subject_hierarchy(image, _scene())

    assert hierarchy.enabled is False
    assert hierarchy.reason in {"no_component", "low_confidence", "area_gate"}


def test_alpha_subject_scene_skips_opaque_hierarchy():
    image = np.full((160, 200, 3), (120, 130, 140), dtype=np.uint8)
    scene = _scene()
    scene.metadata["subject_mode"] = True

    hierarchy = estimate_opaque_subject_hierarchy(image, scene)

    assert hierarchy.enabled is False
    assert hierarchy.reason == "alpha_subject"


def test_shape_overlap_distinguishes_subject_and_background():
    mask = np.zeros((100, 120), dtype=np.uint8)
    mask[20:90, 35:85] = 1
    hierarchy = OpaqueSubjectHierarchy(
        True,
        confidence=0.8,
        subject_area_ratio=float(mask.mean()),
        bbox=(35, 20, 85, 90),
        reason="accepted",
        mask=mask,
    )
    subject = Shape(1, "rectangle", (40, 50, 60), x=45, y=30, width=25, height=40)
    background = Shape(2, "rectangle", (210, 210, 205), x=2, y=2, width=20, height=18)

    assert shape_subject_overlap(subject, hierarchy) > 0.95
    assert shape_subject_overlap(background, hierarchy) == 0.0



def test_phase4_derives_coarse_body_zones_from_vertical_subject():
    mask = np.zeros((160, 200), dtype=np.uint8)
    mask[18:150, 70:130] = 1
    mask[58:112, 50:70] = 1
    mask[58:112, 130:150] = 1
    hierarchy = OpaqueSubjectHierarchy(
        True,
        confidence=0.82,
        subject_area_ratio=float(mask.mean()),
        bbox=(50, 18, 150, 150),
        reason="accepted",
        mask=mask,
    )

    zones = estimate_opaque_subject_zones(hierarchy, _scene())

    assert zones.enabled is True
    assert {"head", "torso", "legs"}.issubset(zones.zone_masks)
    assert "left_arm" in zones.zone_masks
    assert "right_arm" in zones.zone_masks
    assert zones.zone_bbox("head") is not None


def test_phase4_zone_assignment_distinguishes_head_torso_and_arm():
    mask = np.zeros((160, 200), dtype=np.uint8)
    mask[18:150, 70:130] = 1
    mask[58:112, 50:70] = 1
    hierarchy = OpaqueSubjectHierarchy(True, 0.82, float(mask.mean()), (50, 18, 130, 150), "accepted", mask)
    zones = estimate_opaque_subject_zones(hierarchy, _scene())

    head = Shape(1, "rectangle", (40, 50, 60), x=82, y=24, width=25, height=22)
    torso = Shape(2, "rectangle", (40, 50, 60), x=82, y=68, width=25, height=26)
    arm = Shape(3, "rectangle", (40, 50, 60), x=53, y=66, width=14, height=28)

    assert dominant_shape_zone(head, zones) == "head"
    assert dominant_shape_zone(torso, zones) == "torso"
    assert dominant_shape_zone(arm, zones) == "left_arm"


def test_phase4_structure_zones_reuse_character_metadata_and_drop_weak_limb():
    parts = [
        {"part_type": "subject", "bbox": [20, 5, 80, 130], "confidence": 1.0},
        {"part_type": "head", "bbox": [42, 20, 38, 42], "confidence": 0.76},
        {"part_type": "face", "bbox": [50, 31, 20, 20], "confidence": 0.78},
        {"part_type": "hair", "bbox": [36, 18, 50, 55], "confidence": 0.68},
        {"part_type": "torso", "bbox": [43, 58, 36, 34], "confidence": 0.72},
        {"part_type": "outfit", "bbox": [38, 58, 46, 55], "confidence": 0.77},
        {"part_type": "left_arm", "bbox": [24, 56, 16, 42], "confidence": 0.56},
        {"part_type": "right_arm", "bbox": [82, 58, 12, 40], "confidence": 0.20},
        {"part_type": "left_leg", "bbox": [42, 94, 18, 40], "confidence": 0.60},
        {"part_type": "right_leg", "bbox": [62, 94, 18, 40], "confidence": 0.60},
    ]
    scene = Scene(120, 140, (245, 245, 240), [], {
        "subject_mode": True,
        "character": {"structure": {"parts": parts}},
    })

    zones = estimate_structure_subject_zones(scene)

    assert zones.enabled is True
    assert zones.reason == "character_structure"
    assert {"hair", "clothing", "head", "torso", "left_arm", "left_leg", "right_leg"}.issubset(zones.zone_masks)
    assert "right_arm" not in zones.zone_masks
    assert np.logical_and(zones.zone_masks["hair"] > 0, zones.zone_masks["head"] > 0).sum() == 0
