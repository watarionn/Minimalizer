from __future__ import annotations

import pytest

from minimalize_engine.models import Scene, Shape
from minimalize_engine.target_style import (
    DEFAULT_RINKA_REFERENCE_PRESET,
    RINKA_REFERENCE_PRESETS,
    _geometrize_background,
    apply_rinka_reference_style,
    normalize_rinka_reference_preset,
)


def _poly(i, points, *, color, part="unknown", semantic="generic", role="misc", layer="foreground", z=10, importance=0.9):
    return Shape(
        id=i,
        shape_type="polygon",
        fill_color=color,
        points=points,
        character_part=part,
        semantic_type=semantic,
        source_role=role,
        layer_name=layer,
        z_index=z,
        importance=importance,
    )


def _subject_scene(background=None):
    hair = _poly(
        1,
        [(35, 15), (72, 14), (80, 58), (30, 60)],
        color=(45, 38, 62),
        part="hair",
        semantic="character_hair",
        role="character_hair_base",
        z=30,
        importance=1.0,
    )
    outfit = _poly(
        2,
        [(38, 55), (74, 55), (84, 104), (28, 104)],
        color=(128, 68, 150),
        part="outfit",
        semantic="character_outfit_torso",
        role="character_outfit_torso",
        z=40,
        importance=0.98,
    )
    return Scene(120, 140, background, [hair, outfit], {"subject_mode": True})


def test_phase11_priority3_preset_names_are_stable():
    assert DEFAULT_RINKA_REFERENCE_PRESET == "geometric_poster"
    assert RINKA_REFERENCE_PRESETS == ("geometric_poster", "faceless_subject", "approved_reference")
    assert normalize_rinka_reference_preset("GEOMETRIC_POSTER") == "geometric_poster"
    with pytest.raises(ValueError):
        normalize_rinka_reference_preset("unknown")


def test_phase11_priority3_geometric_background_adds_three_large_panels():
    scene = _subject_scene(background=None)
    shapes, background, stats = _geometrize_background(scene, scene.shapes, style="geometric")

    panels = [shape for shape in shapes if shape.semantic_type == "target_geometric_background"]
    assert background is not None
    assert stats["enabled"] is True
    assert stats["generated_panels"] == 3
    assert len(panels) == 3
    assert all(shape.shape_type == "polygon" and len(shape.points) == 5 for shape in panels)
    assert max(shape.z_index for shape in panels) < min(shape.z_index for shape in scene.shapes)


def test_phase11_priority3_source_background_preset_is_non_synthetic():
    scene = _subject_scene(background=None)
    shapes, background, stats = _geometrize_background(scene, scene.shapes, style="source")

    assert shapes == scene.shapes
    assert background is None
    assert stats["enabled"] is False
    assert stats["generated_panels"] == 0


def test_phase11_priority3_does_not_posterize_general_scene_without_subject_evidence():
    sky = _poly(
        10,
        [(0, 0), (120, 0), (120, 70), (0, 70)],
        color=(70, 100, 130),
        semantic="skyline",
        role="background",
        layer="background",
        z=2,
    )
    scene = Scene(120, 140, (230, 225, 215), [sky], {"subject_mode": False})
    shapes, background, stats = _geometrize_background(scene, scene.shapes, style="geometric")

    assert shapes == scene.shapes
    assert background == scene.background
    assert stats["enabled"] is False
    assert stats["reason"] == "no_subject_evidence"


def test_phase11_priority3_pipeline_reports_and_preserves_poster_panels():
    scene = _subject_scene(background=None)
    out = apply_rinka_reference_style(
        scene,
        target_max_shapes=12,
        background_style="geometric",
        preset="geometric_poster",
    )
    target = out.metadata["target_style"]
    geometry = target["background_geometry"]

    assert out.background is not None
    assert target["preset"] == "geometric_poster"
    assert geometry["enabled"] is True
    assert geometry["generated_panels"] == 3
    assert geometry["surviving_panels"] == 3
    assert sum(shape.semantic_type == "target_geometric_background" for shape in out.shapes) == 3


def test_phase11_priority3_keeps_generic_midground_identity_carrier():
    scene = _subject_scene(background=None)
    identity_carrier = _poly(
        40,
        [(12, 42), (31, 37), (35, 85), (14, 91)],
        color=(156, 96, 132),
        semantic="subject_mass",
        role="structure",
        layer="midground",
        z=20,
        importance=0.91,
    )
    scene.shapes.append(identity_carrier)

    shapes, _background, stats = _geometrize_background(scene, scene.shapes, style="geometric")

    assert any(shape.id == identity_carrier.id for shape in shapes)
    assert stats["replaced_background_shapes"] == 0



def test_phase11_priority3_replaces_definite_low_value_background_shape():
    scene = _subject_scene(background=(80, 90, 100))
    backdrop = _poly(
        50,
        [(0, 0), (120, 0), (120, 140), (0, 140)],
        color=(75, 85, 95),
        semantic="background_fill",
        role="background",
        layer="background",
        z=1,
        importance=0.35,
    )
    scene.shapes.insert(0, backdrop)

    shapes, _background, stats = _geometrize_background(scene, scene.shapes, style="geometric")

    assert all(shape.id != backdrop.id for shape in shapes)
    assert stats["replaced_background_shapes"] == 1
    assert stats["generated_panels"] == 3


def test_phase11_priority3_preserves_one_strong_scene_cue():
    scene = _subject_scene(background=(80, 90, 100))
    skyline = _poly(
        60,
        [(0, 20), (120, 20), (120, 58), (0, 58)],
        color=(55, 62, 74),
        semantic="skyline",
        role="background",
        layer="background",
        z=2,
        importance=0.92,
    )
    scene.shapes.insert(0, skyline)

    shapes, _background, stats = _geometrize_background(scene, scene.shapes, style="geometric")

    assert any(shape.id == skyline.id for shape in shapes)
    assert stats["preserved_scene_cues"] == 1
    assert stats["replaced_background_shapes"] == 0
