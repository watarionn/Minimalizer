from __future__ import annotations

import numpy as np

from minimalize_engine.v2.palette import PaletteEntry
from minimalize_engine.v2.pipeline import SceneModel, SceneShape
from minimalize_engine.v2.primitive import PrimitiveGeometry
from minimalize_engine.v2.semantic_advisor import probe_semantic_scene


def _poly(points):
    return PrimitiveGeometry(
        kind="polygon",
        loops=(np.asarray(points, dtype=np.float32),),
    )


def _entry(pid, rid, rgb):
    return PaletteEntry(
        pid,
        (rid,),
        rid,
        np.asarray([50.0, 0.0, 0.0]),
        rgb,
        (0, 0),
    )


def _scene_with_hidden_accent():
    base = SceneShape(
        region_id=1,
        geometry=_poly([[2,2],[18,2],[18,18],[2,18]]),
        palette_id=0,
        visible=True,
    )
    accent = SceneShape(
        region_id=3,
        geometry=_poly([[6,6],[12,6],[12,12],[6,12]]),
        palette_id=1,
        visible=False,
    )
    return SceneModel(
        24,
        24,
        (base, accent),
        (
            _entry(0, 1, (100,100,100)),
            _entry(1, 3, (220,30,30)),
        ),
    )


def test_probe_returns_only_render_impacting_hidden_plane():
    scene = _scene_with_hidden_accent()
    part = np.ones((24,24), dtype=bool)
    source = np.full((24,24,3), 100, dtype=np.uint8)
    source[6:13,6:13] = (220,30,30)

    items = probe_semantic_scene(
        scene,
        part,
        source,
        part_name="torso",
        preset="minimal",
        target_plane_limit=3,
    )

    assert len(items) == 1
    assert items[0].region_id == 3
    assert items[0].changed_pixels > 0
    assert items[0].source_part_mae_improvement > 0.0


def test_probe_does_not_mutate_visibility():
    scene = _scene_with_hidden_accent()
    before = tuple(shape.visible for shape in scene.shapes)
    part = np.ones((24,24), dtype=bool)
    source = np.full((24,24,3), 100, dtype=np.uint8)

    probe_semantic_scene(
        scene,
        part,
        source,
        part_name="torso",
        preset="minimal",
        target_plane_limit=3,
    )

    assert tuple(shape.visible for shape in scene.shapes) == before


def test_probe_drops_fully_occluded_hidden_plane():
    hidden = SceneShape(
        region_id=1,
        geometry=_poly([[4,4],[16,4],[16,16],[4,16]]),
        palette_id=0,
        visible=False,
    )
    covering = SceneShape(
        region_id=2,
        geometry=_poly([[4,4],[16,4],[16,16],[4,16]]),
        palette_id=1,
        visible=True,
    )
    scene = SceneModel(
        24,
        24,
        (hidden, covering),
        (
            _entry(0, 1, (220,30,30)),
            _entry(1, 2, (30,30,220)),
        ),
    )
    part = np.ones((24,24), dtype=bool)
    source = np.full((24,24,3), 255, dtype=np.uint8)

    assert probe_semantic_scene(
        scene,
        part,
        source,
        part_name="head",
        preset="minimal",
        target_plane_limit=5,
    ) == ()


def test_candidate_payload_is_plain_runtime_data():
    scene = _scene_with_hidden_accent()
    part = np.ones((24,24), dtype=bool)
    source = np.full((24,24,3), 100, dtype=np.uint8)

    item = probe_semantic_scene(
        scene,
        part,
        source,
        part_name="torso",
        preset="minimal",
        target_plane_limit=3,
    )[0]
    payload = item.as_dict()

    assert payload["region_id"] == 3
    assert "changed_ratio_of_part" in payload
    assert "source_part_mae_improvement" in payload
    assert all(not isinstance(value, np.ndarray) for value in payload.values())
