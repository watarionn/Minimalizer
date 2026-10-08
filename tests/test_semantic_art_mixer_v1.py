"""Offline regression gates for Semantic Art Mixer v1 (no source photo dependency)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "research" / "semantic_art_mixer_v1.py"
SPEC = importlib.util.spec_from_file_location("semantic_art_mixer_v1", SCRIPT)
assert SPEC and SPEC.loader
mixer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mixer)


def sample_source():
    rgb = np.empty((90, 80, 3), dtype=np.uint8)
    rgb[:] = (240, 140, 85)
    rgb[25:62, 22:39] = (119, 222, 25)
    return Image.fromarray(rgb, "RGB"), (18, 20, 50, 70)


def test_original_tie_rgb_preserved_and_no_green_growth():
    src, roi = sample_source()
    mask = mixer.observed_tie_mask(src, roi=roi, min_pixels=50)
    assert int(mask.sum()) == 37*17
    arr = np.asarray(src).copy()
    arr[mask] = [178, 150, 12]     # erroneous lost tie color
    arr[35:52, 40:45] = [111, 232, 19]  # erroneous green expansion outside ROI tie mask
    render = Image.fromarray(arr)
    fixed, metrics = mixer.protect_original_tie(render, src, mask, roi=roi)
    out = np.asarray(fixed)
    source = np.asarray(src)
    assert np.array_equal(out[mask], source[mask])
    assert np.array_equal(out[35:52, 40:45], source[35:52, 40:45])
    assert metrics["tie_pixels_changed_before"] == 37*17
    assert metrics["tie_pixels_changed_after"] == 0
    assert metrics["green_pixels_outside_source_mask_before"] == 17*5
    assert metrics["green_pixels_outside_source_mask_after"] == 0
    assert metrics["restoration_uses_original_rgb_only"] is True


def test_outside_roi_never_modified():
    src, roi = sample_source()
    mask = mixer.observed_tie_mask(src, roi=roi, min_pixels=50)
    arr = np.asarray(src).copy()
    arr[:12, :12] = [100, 240, 8]
    unchanged = arr.copy()
    fixed, _ = mixer.protect_original_tie(Image.fromarray(arr), src, mask, roi=roi)
    assert np.array_equal(np.asarray(fixed)[:12, :12], unchanged[:12, :12])


def test_invalid_masks_and_roi_fail_closed():
    src, roi = sample_source()
    with pytest.raises(ValueError, match="Out-of-bounds"):
        mixer.observed_tie_mask(src, roi=(-1, 0, 20, 90))
    with pytest.raises(ValueError, match="No source tie"):
        mixer.observed_tie_mask(src, roi=(0,0,12,12))
    mask = mixer.observed_tie_mask(src, roi=roi, min_pixels=50)
    wrong = mask.copy()
    wrong[0,0] = True
    with pytest.raises(ValueError, match="outside the observed"):
        mixer.protect_original_tie(src, src, wrong, roi=roi)
    with pytest.raises(ValueError, match="dimensions"):
        mixer.protect_original_tie(src.crop((0,0,20,20)), src, mask, roi=roi)


@pytest.mark.parametrize("recipe", [
    {"id":"a","shape":"mosaic","stroke":"sparse","texture":"none","color":"source_tie_lock"},
    {"id":"b","shape":"pixel","stroke":"none","texture":"dots","color":"none"},
])
def test_valid_recipe_one_role_each(recipe):
    assert mixer.validate_recipe(recipe) == recipe


@pytest.mark.parametrize("patch", [
    {"shape": "unknown"},
    {"stroke": "fake"},
    {"texture": "invent"},
    {"color": "learned_neural_style"},
    {"id": "../escape"},
])
def test_rejects_unsupported_or_unsafe_config(patch):
    recipe = dict(mixer.DEFAULT_RECIPES[0])
    recipe.update(patch)
    with pytest.raises(ValueError):
        mixer.validate_recipe(recipe)


def test_rejects_missing_or_extra_role():
    recipe=dict(mixer.DEFAULT_RECIPES[0])
    del recipe["stroke"]
    with pytest.raises(ValueError):
        mixer.validate_recipe(recipe)
    recipe=dict(mixer.DEFAULT_RECIPES[0])
    recipe["renderer"]="ai_img2img"
    with pytest.raises(ValueError):
        mixer.validate_recipe(recipe)


def test_transparent_black_pixels_cannot_dark_fill_canvas():
    base = Image.new("RGB", mixer.SIZE, (225, 180, 130))
    transparent = Image.new("RGBA", mixer.SIZE, (0, 0, 0, 0))
    result = mixer.add_stroke(base, transparent)
    assert np.array_equal(np.asarray(base), np.asarray(result))
    # Real black ink only affects the one visible pixel.
    transparent.putpixel((35, 43), (0, 0, 0, 255))
    inked = mixer.add_stroke(base, transparent, opacity=1.0)
    assert inked.getpixel((35, 43)) == (24, 33, 34)
    assert inked.getpixel((38, 43)) == base.getpixel((38, 43))


def test_preserves_manual_scope_no_runtime_import_or_generation():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "import local_worker" not in source
    assert "import torch" not in source
    assert "img2img" not in source.replace("img2img or", "")
    assert len(mixer.DEFAULT_RECIPES) == 4
    assert len(set(mixer.ASSETS)) == 8
