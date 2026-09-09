import numpy as np

from minimalize_engine.character.models import CharacterPartCandidate, CharacterStructure
from minimalize_engine.character.part_types import CharacterPartType
from minimalize_engine.character.semantic_shape_tree import build_semantic_shape_tree


def _part(pid, kind, bbox, budget):
    mask = np.ones((32, 32), dtype=np.uint8)
    return CharacterPartCandidate(
        id=pid, part_type=kind, mask=mask, bbox=bbox,
        centroid=(16.0, 16.0), area=64, area_ratio=0.0625,
        confidence=0.9, shape_budget=budget,
    )


def test_semantic_shape_tree_builds_character_hierarchy():
    parts = [
        _part(1, CharacterPartType.HEAD, (8, 2, 16, 12), 1),
        _part(2, CharacterPartType.FACE, (11, 5, 8, 7), 1),
        _part(3, CharacterPartType.HAIR, (8, 2, 16, 12), 3),
        _part(4, CharacterPartType.TORSO, (9, 13, 14, 12), 1),
        _part(5, CharacterPartType.OUTFIT, (8, 12, 16, 14), 3),
        _part(6, CharacterPartType.PROP, (2, 6, 5, 18), 2),
    ]
    structure = CharacterStructure((0, 0, 32, 32), np.ones((32, 32), dtype=np.uint8), parts)
    tree = build_semantic_shape_tree(structure)

    assert tree.root == "subject"
    assert tree.get("face").parent == "head"
    assert tree.get("hair").parent == "head"
    assert tree.get("outfit").parent == "torso"
    assert tree.get("prop").protected is True
    assert tree.get("outfit").primitive_budget == 3
    assert tree.can_merge("face", "hair") is False
    assert tree.can_merge("hair", "hair") is True
