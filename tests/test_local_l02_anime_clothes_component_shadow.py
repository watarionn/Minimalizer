"""Source-free negative controls. No character labels or private arrays."""
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_anime_clothes_component_shadow import (
    propose_anime_clothes_component_shadow, AnimeClothesComponentHold)


def _sample():
    source = np.zeros((50, 50, 4), np.uint8)
    source[10:40, 10:40, 3] = 255
    classes = np.zeros((50, 50), np.uint8)
    anime = np.zeros((50, 50), np.uint8)
    owner = np.zeros((50, 50), np.uint8)
    classes[10:40, 10:40] = 32
    anime[10:40, 10:40] = 10
    owner[10:20, 10:20] = 1
    classes[10:20, 10:20] = 5
    return source, classes, anime, owner


def test_source_only_clothing_additions_never_promote_quality():
    source, classes, anime, owner = _sample()
    original = owner.copy()
    out, receipt = propose_anime_clothes_component_shadow(
        source_rgba=source, class_ids=classes,
        anime_classes=anime, frozen_owner=owner)
    assert np.array_equal(owner, original)
    assert np.all(out[original > 0] == original[original > 0])
    assert receipt['added_source_pixels'] > 0
    assert np.all(classes[(out > 0) & (original == 0)] == 32)
    assert receipt['Phase4'] == 'FAIL' and receipt['quality'] == 'FAIL'


def test_independent_nonclothing_abstains():
    source, classes, anime, owner = _sample()
    anime[:] = 11
    out, receipt = propose_anime_clothes_component_shadow(
        source_rgba=source, class_ids=classes,
        anime_classes=anime, frozen_owner=owner)
    assert np.array_equal(out, owner)
    assert receipt['added_source_pixels'] == 0


def test_transparent_pixels_never_added():
    source, classes, anime, owner = _sample()
    source[25:35, 25:35, 3] = 0
    out, _ = propose_anime_clothes_component_shadow(
        source_rgba=source, class_ids=classes,
        anime_classes=anime, frozen_owner=owner)
    assert not np.any(out[source[..., 3] == 0])


def test_frozen_owner_outside_source_rejected():
    source, classes, anime, owner = _sample()
    source[10, 10, 3] = 0
    with pytest.raises(AnimeClothesComponentHold, match='INVALID_FROZEN_SOURCE_DOMAIN'):
        propose_anime_clothes_component_shadow(
            source_rgba=source, class_ids=classes,
            anime_classes=anime, frozen_owner=owner)


def test_wrong_shape_rejected():
    source, classes, anime, owner = _sample()
    with pytest.raises(AnimeClothesComponentHold, match='INVALID_MODEL_OR_OWNER_ARRAY'):
        propose_anime_clothes_component_shadow(
            source_rgba=source, class_ids=classes[:-1],
            anime_classes=anime, frozen_owner=owner)
