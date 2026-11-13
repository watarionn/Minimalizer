import numpy as np

from tools.research.build_local_l04_candidate_triple import OWNERS, _path_from_mask


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
