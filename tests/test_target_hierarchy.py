import numpy as np

from minimalize_engine.models import Scene, Shape
from minimalize_engine.target_hierarchy import (
    OpaqueSubjectHierarchy,
    dominant_shape_zone,
    estimate_opaque_subject_hierarchy,
    estimate_opaque_subject_zones,
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
