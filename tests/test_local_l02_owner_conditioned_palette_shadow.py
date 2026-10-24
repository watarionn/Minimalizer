"""Source-free P0 owner-color leakage negatives; no human labels."""
import numpy as np
import pytest
from local_l02_owner_conditioned_palette_shadow import (
    propose_owner_conditioned_palette_abstention, OwnerPaletteHold)


def fixture():
    h, w = 180, 180
    rgba = np.full((h, w, 4), 255, dtype=np.uint8)
    rgba[..., :3] = (225, 35, 45)  # red jacket seed
    base = np.zeros((h, w), dtype=np.uint8)
    base[20:150, 10:30] = 1
    base[20:150, 110:130] = 2
    rgba[20:150, 110:130, :3] = (30, 35, 215)  # blue coat seed
    cls = np.zeros((h, w), dtype=np.uint8)
    cls[base > 0] = 32
    anime = np.zeros((h, w), dtype=np.uint8)
    anime[base > 0] = 10
    return rgba, base, cls, anime


def run(rgba, base, cls, anime, candidate):
    return propose_owner_conditioned_palette_abstention(
        source_rgba=rgba, class_ids=cls, anime_classes=anime,
        baseline_owner=base, candidate_owner=candidate)


def test_owner1_cannot_borrow_owner2_blue_palette():
    rgba, base, cls, anime = fixture()
    proposed = base.copy()
    proposed[30:145, 30:40] = 1
    cls[30:145, 30:40] = 32
    rgba[30:145, 30:40, :3] = (30, 35, 215)
    out, meta = run(rgba, base, cls, anime, proposed)
    assert np.array_equal(out, base)
    assert meta['source_only_abstained_added_px'] == 1150
    assert not meta['semantic_quality_pass']


def test_matching_owner2_palette_can_retain_attached_blue():
    rgba, base, cls, anime = fixture()
    proposed = base.copy()
    proposed[30:145, 100:110] = 2
    cls[30:145, 100:110] = 32
    rgba[30:145, 100:110, :3] = (30, 35, 215)
    out, meta = run(rgba, base, cls, anime, proposed)
    assert np.count_nonzero((base == 0) & (out == 2)) == 1150
    assert meta['source_only_retained_added_px'] == 1150


def test_equal_owner_palettes_abstain_on_ambiguous_colors():
    rgba, base, cls, anime = fixture()
    rgba[20:150, 110:130, :3] = (225, 35, 45)
    proposed = base.copy()
    proposed[30:145, 30:40] = 1
    cls[30:145, 30:40] = 32
    out, _ = run(rgba, base, cls, anime, proposed)
    assert np.array_equal(out, base)


def test_rejects_frozen_owner_reassignment():
    rgba, base, cls, anime = fixture()
    proposed = base.copy()
    proposed[25, 25] = 2
    with pytest.raises(OwnerPaletteHold, match='FROZEN_OWNER'):
        run(rgba, base, cls, anime, proposed)


def test_rejects_added_pixel_outside_source():
    rgba, base, cls, anime = fixture()
    proposed = base.copy()
    proposed[30:145, 30:40] = 1
    cls[30:145, 30:40] = 32
    rgba[35, 35, 3] = 0
    with pytest.raises(OwnerPaletteHold, match='FROZEN_OWNER_SOURCE'):
        run(rgba, base, cls, anime, proposed)


def test_deterministic_and_frozen_without_review_masks():
    rgba, base, cls, anime = fixture()
    proposed = base.copy()
    proposed[30:145, 30:40] = 1
    cls[30:145, 30:40] = 32
    a, am = run(rgba, base, cls, anime, proposed)
    b, bm = run(rgba, base, cls, anime, proposed)
    assert np.array_equal(a, b)
    assert am == bm
    assert am['frozen_owner_changed_px'] == 0
