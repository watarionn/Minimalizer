"""Non-generative, offline tests for face/silhouette-ink research guard."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MODDIR = ROOT / "tools" / "research"
sys.path.insert(0, str(MODDIR))
spec=importlib.util.spec_from_file_location("semantic_art_mixer_v2_guarded", MODDIR/"semantic_art_mixer_v2_guarded.py")
guard=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(guard)

def synthetic_original():
    src=Image.new("RGB", guard.SIZE, (251, 125, 56))
    draw=ImageDraw.Draw(src)
    draw.ellipse((145, 110, 205, 190), fill=(252, 238, 233))
    # Pseudo-eye marks already present in the test source must not be replicated
    # into the deliberately expressionless face plane by the Mixer.
    draw.ellipse((157,137,169,147), fill=(10,18,19))
    draw.ellipse((181,135,194,147), fill=(10,18,19))
    draw.rectangle((155,245,177,315), fill=(116,224,23))
    return src


def test_face_plane_includes_both_eye_positions_but_no_new_pixels():
    original=synthetic_original()
    plane, roi, color=guard.source_face_plane(original)
    assert plane[141,163] and plane[141,187]
    assert plane.sum()>1200
    assert tuple(color) in [tuple(v) for v in np.unique(np.asarray(original)[plane],axis=0)]
    assert not roi[260,167]  # color lock is independently localized


def test_rgba_ink_respects_transparency():
    line=Image.new("RGBA",guard.SIZE,(0,0,0,0))
    assert guard.visible_ink_mask(line).sum()==0
    line.putpixel((150,140),(0,0,0,255))
    mask=guard.visible_ink_mask(line)
    assert mask[140,150] == 1.0
    assert mask[140,151] == 0.0


def test_guards_remove_eye_strokes_and_protect_green_without_inventing_face():
    original=synthetic_original()
    outline=Image.new("RGBA",guard.SIZE,(0,0,0,0))
    d=ImageDraw.Draw(outline)
    # A source-derived line crosses both eyes. It must be suppressed by full ROI.
    d.line([(146,142),(205,142)],fill=(0,0,0,255),width=3)
    # A non-face line must remain as an outline feature.
    d.line([(104,215),(250,215)],fill=(0,0,0,255),width=4)
    dot=Image.new("RGBA",guard.SIZE,(255,255,255,255))
    base=Image.new("RGBA",guard.SIZE,(255,130,50,255))
    assets={
        "shape.voronoi":base,
        "stroke.contour":outline,
        "stroke.sparse":outline,
        "texture.dots":dot,
    }
    face,face_roi,color=guard.source_face_plane(original)
    tie=guard.observed_tie_mask(original)
    recipe=guard.DEFAULT_RECIPES[0]
    legacy, fixed, metrics, protection=guard.compose_guarded(recipe,original,assets,tie)
    out=np.asarray(fixed.convert("RGB"))
    src=np.asarray(original.convert("RGB"))
    assert np.array_equal(out[tie],src[tie])
    assert metrics["tie_pixels_changed_after"]==0
    assert metrics["green_pixels_outside_source_mask_after"]==0
    assert metrics["facial_stroke_source_pixels_suppressed"]>20
    assert metrics["source_sparse_support_ink_pixels"]>100
    assert metrics["face_dark_pixels_after"]==0
    assert np.all(out[protection]==np.array(color))
    # Outside the facial mask an observed contour contributes actual ink.
    assert tuple(out[215,125])!=tuple(np.asarray(base.convert("RGB"))[215,125])
    # Previous style combines independently; inputs are left unchanged.
    assert original.getpixel((163,141))==(10,18,19)
    assert tuple(np.asarray(legacy)[141,163]) != tuple(out[141,163])


def test_face_guard_rejects_empty_non_skin_source():
    # A random coloured image with no original fair-skin plane must fail rather
    # than invent a skin/face region from a manual polygon alone.
    blank=Image.new("RGB",guard.SIZE,(20,50,70))
    import pytest
    with pytest.raises(ValueError,match="no detected connected region"):
        guard.source_face_plane(blank)


def test_keeps_production_isolation():
    source=(MODDIR/"semantic_art_mixer_v2_guarded.py").read_text(encoding="utf-8")
    assert "import local_worker" not in source
    assert "import torch" not in source
    assert "diffusers" not in source
    assert "import img2img" not in source
    assert "from diffusers" not in source
    assert len(guard.DEFAULT_RECIPES)==4
