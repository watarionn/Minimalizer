import numpy as np
import pytest

from minimalizer_zerobase.compose.composer import ComposedPrimitive, VectorScene
from minimalizer_zerobase.semantic_abstraction.required_semantic_mass import (
    RequiredSemanticMass,
)
from minimalizer_zerobase.semantic_abstraction.required_semantic_mass_scene import (
    apply_required_semantic_mass_scene,
)


def _scene_primitive() -> ComposedPrimitive:
    return ComposedPrimitive(
        primitive_id="subject",
        source_region_id="torso",
        selected_candidate_id="subject",
        primitive_type="rectangle",
        parameters={"bbox": [5.0, 5.0, 20.0, 20.0]},
        fill_ref="#888888",
        z_order=2,
    )


def _reservation(role: str, polygon, rgb=(20, 20, 20)) -> RequiredSemanticMass:
    return RequiredSemanticMass(
        version="test",
        role=role,
        cluster_index=0,
        polygon=tuple((float(x), float(y)) for x, y in polygon),
        rgb=rgb,
        source_area=100,
        role_area_ratio=.2,
        contrast_from_role_median=100.0,
        source_coverage=.9,
        expansion_ratio=1.0,
        outside_role_pixels=0,
    )


def test_adds_safe_reservations_without_mutating_existing_scene():
    scene = VectorScene(40, 40, (_scene_primitive(),), {})
    torso = np.zeros((40, 40), dtype=bool)
    torso[5:25, 5:25] = True
    arm = np.zeros((40, 40), dtype=bool)
    arm[5:25, 28:36] = True
    result = apply_required_semantic_mass_scene(
        scene,
        (
            _reservation("torso", [(8, 8), (16, 8), (16, 16), (8, 16)]),
            _reservation("right_arm", [(29, 8), (34, 8), (34, 16), (29, 16)]),
        ),
        {"torso": torso, "right_arm": arm},
    )
    assert result.added_count == 2
    assert result.scene.primitives[0] == scene.primitives[0]
    added = [p for p in result.scene.primitives if p.primitive_id.startswith("required-semantic-mass:")]
    assert len(added) == 2
    assert min(p.z_order for p in added) > scene.primitives[0].z_order


def test_rejects_protected_semantic_overlap():
    scene = VectorScene(30, 30, (_scene_primitive(),), {})
    torso = np.zeros((30, 30), dtype=bool)
    torso[5:25, 5:25] = True
    face = np.zeros((30, 30), dtype=bool)
    face[10:15, 10:15] = True
    reservation = _reservation(
        "torso",
        [(8, 8), (18, 8), (18, 18), (8, 18)],
    )
    with pytest.raises(ValueError, match="protected"):
        apply_required_semantic_mass_scene(
            scene,
            (reservation,),
            {"torso": torso, "face": face},
        )


def test_rejects_polygon_outside_semantic_role():
    scene = VectorScene(30, 30, (_scene_primitive(),), {})
    torso = np.zeros((30, 30), dtype=bool)
    torso[10:20, 10:20] = True
    reservation = _reservation(
        "torso",
        [(8, 8), (18, 8), (18, 18), (8, 18)],
    )
    with pytest.raises(ValueError, match="exits role"):
        apply_required_semantic_mass_scene(scene, (reservation,), {"torso": torso})


def test_rejects_overlapping_reservations():
    scene = VectorScene(30, 30, (_scene_primitive(),), {})
    torso = np.zeros((30, 30), dtype=bool)
    torso[5:25, 5:25] = True
    rows = (
        _reservation("torso", [(8, 8), (16, 8), (16, 16), (8, 16)]),
        _reservation("torso", [(12, 12), (20, 12), (20, 20), (12, 20)], rgb=(200, 20, 20)),
    )
    with pytest.raises(ValueError, match="overlap"):
        apply_required_semantic_mass_scene(scene, rows, {"torso": torso})
