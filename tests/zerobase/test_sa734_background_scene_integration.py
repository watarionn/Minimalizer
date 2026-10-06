import numpy as np

from minimalizer_zerobase.compose.composer import ComposedPrimitive, VectorScene
from minimalizer_zerobase.semantic_abstraction.background_scene_integration import (
    apply_background_scene_stage,
)


def _primitive(pid: str, role: str, z: int) -> ComposedPrimitive:
    return ComposedPrimitive(
        pid,
        role,
        pid,
        "rectangle",
        {"bbox": [1.0, 1.0, 4.0, 4.0]},
        "#111111",
        z,
    )


def test_background_stage_replaces_old_background_and_stays_behind_subject():
    rgb = np.zeros((40, 40, 3), dtype=np.uint8)
    rgb[:] = [20, 30, 40]
    rgb[:, 20:] = [180, 90, 30]
    subject = np.zeros((40, 40), dtype=bool)
    subject[10:30, 14:26] = True
    scene = VectorScene(
        40,
        40,
        (
            _primitive("old-bg", "background", 0),
            _primitive("subject", "torso", 1),
        ),
        {"golden_raster_used": False},
    )
    result = apply_background_scene_stage(scene, rgb, subject)
    assert result.generated_background_count >= 1
    assert not any(p.primitive_id == "old-bg" for p in result.scene.primitives)
    bg = [p for p in result.scene.primitives if p.source_region_id == "background"]
    torso = next(p for p in result.scene.primitives if p.source_region_id == "torso")
    assert all(p.z_order < torso.z_order for p in bg)
    assert result.scene.provenance["golden_raster_used"] is False


def test_wrapped_uniform_background_uses_bbox_frame_fallback():
    rgb = np.full((80, 80, 3), [180, 90, 30], dtype=np.uint8)
    subject = np.zeros((80, 80), dtype=bool)
    subject[20:60, 28:52] = True
    scene = VectorScene(80, 80, (_primitive("subject", "torso", 2),), {})
    result = apply_background_scene_stage(scene, rgb, subject)
    assert result.mode == "bbox_frame"
    assert 1 <= result.generated_background_count <= 4
    assert all(p.primitive_type == "rectangle" for p in result.scene.primitives if p.source_region_id == "background")


def test_subject_primitives_are_not_mutated():
    rgb = np.full((50, 50, 3), [30, 40, 50], dtype=np.uint8)
    subject = np.zeros((50, 50), dtype=bool)
    subject[15:35, 15:35] = True
    original = _primitive("identity-accent:test", "head", 7)
    scene = VectorScene(50, 50, (original,), {})
    result = apply_background_scene_stage(scene, rgb, subject)
    after = next(p for p in result.scene.primitives if p.primitive_id == original.primitive_id)
    assert after == original


def test_invalid_subject_mask_fails():
    import pytest
    rgb = np.zeros((20, 20, 3), dtype=np.uint8)
    scene = VectorScene(20, 20, (), {})
    with pytest.raises(ValueError):
        apply_background_scene_stage(scene, rgb, np.zeros((20, 20), dtype=bool))
