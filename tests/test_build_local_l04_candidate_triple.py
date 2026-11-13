import numpy as np

from tools.research.build_local_l04_candidate_triple import (
    OWNERS,
    _path_from_mask,
    _source_palette,
)


def test_stage8_path_builder_emits_closed_geometry_and_vertex_count():
    mask = np.zeros((12, 12), dtype=bool)
    mask[2:8, 3:9] = True
    path, vertices = _path_from_mask(mask)
    assert path.startswith("M ")
    assert path.endswith(" Z")
    assert vertices >= 4


def test_candidate_triple_uses_all_phase4_parts_without_vertex_cap():
    assert set(OWNERS) == {
        "head", "hair", "face", "neck", "torso", "left_arm", "right_arm",
        "lower_body", "major_clothing", "accessory_or_held_object", "unknown",
    }


def test_source_palette_keeps_torso_and_outerwear_visually_distinct():
    rgba = np.zeros((6, 6, 4), dtype=np.uint8)
    rgba[..., 3] = 255
    rgba[1:5, 1:3, :3] = (245, 245, 235)
    rgba[1:5, 3:5, :3] = (190, 125, 65)
    masks = {owner: np.zeros((6, 6), dtype=bool) for owner in OWNERS}
    masks["torso"][1:5, 1:3] = True
    masks["major_clothing"][1:5, 3:5] = True
    palette = _source_palette(rgba, masks)
    assert palette["torso"] == "#f5f5eb"
    assert palette["major_clothing"] == "#be7d41"
    assert palette["torso"] != palette["major_clothing"]
