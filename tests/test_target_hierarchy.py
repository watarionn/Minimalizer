import numpy as np

from minimalize_engine.models import Scene, Shape
from minimalize_engine.target_hierarchy import (
    OpaqueSubjectHierarchy,
    estimate_opaque_subject_hierarchy,
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
