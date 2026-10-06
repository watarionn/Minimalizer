import numpy as np
import pytest

from minimalizer_zerobase.compose.composer import ComposedPrimitive, VectorScene
from minimalizer_zerobase.evaluation.forbidden_face_detail_gate import (
    forbidden_face_detail_ratio,
)
from minimalizer_zerobase.semantic_abstraction.face_surface_stage import (
    apply_face_surface_stage,
)


def _primitive(pid: str, role: str, fill: str, z: int) -> ComposedPrimitive:
    return ComposedPrimitive(
        primitive_id=pid,
        source_region_id=role,
        selected_candidate_id=pid,
        primitive_type="rectangle",
        parameters={"bbox": [0.0, 0.0, 40.0, 40.0]},
        fill_ref=fill,
        z_order=z,
    )


def test_face_surface_is_exact_source_observed_flat_surface():
    source = np.full((40, 40, 3), [245, 220, 210], dtype=np.uint8)
    face = np.zeros((40, 40), dtype=bool)
    face[10:30, 12:28] = True
    source[15:18, 15:18] = [30, 30, 30]

    scene = VectorScene(
        40,
        40,
        (
            _primitive("head-base", "head", "#ffffff", 1),
            _primitive("identity-accent:head", "head", "#000000", 5),
        ),
        {},
    )
    result = apply_face_surface_stage(scene, source, face)

    assert result.outside_face_pixels == 0
    assert result.covered_pixels == int(face.sum())
    assert result.fill_rgb in {tuple(int(v) for v in row) for row in source[face]}
    face_primitives = [
        p for p in result.scene.primitives if p.source_region_id == "face"
    ]
    assert face_primitives
    assert min(p.z_order for p in face_primitives) > 5


def test_face_stage_does_not_mutate_non_face_primitives():
    source = np.full((30, 30, 3), [230, 200, 190], dtype=np.uint8)
    face = np.zeros((30, 30), dtype=bool)
    face[8:22, 9:21] = True
    original = _primitive("hair", "hair", "#222222", 8)
    scene = VectorScene(30, 30, (original,), {})
    result = apply_face_surface_stage(scene, source, face)
    assert next(p for p in result.scene.primitives if p.primitive_id == "hair") == original


def test_face_mask_with_hole_fails_closed():
    source = np.full((30, 30, 3), [230, 200, 190], dtype=np.uint8)
    face = np.zeros((30, 30), dtype=bool)
    face[5:25, 5:25] = True
    face[12:18, 12:18] = False
    scene = VectorScene(30, 30, (), {})
    with pytest.raises(ValueError, match="holes"):
        apply_face_surface_stage(scene, source, face)
