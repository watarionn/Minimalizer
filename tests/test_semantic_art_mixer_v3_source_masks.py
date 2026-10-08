"""Isolated checks for original-source face/subject ownership, not learned models."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

HERE=Path(__file__).resolve().parents[1]/"tools"/"research"
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location("mixer3",HERE/"semantic_art_mixer_v3_source_masks.py")
m=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m)


def sample():
    raw=np.zeros((340,340,3),dtype=np.uint8)
    raw[:]=(241,133,70)
    face=np.zeros((340,340),dtype=bool)
    face[108:185,130:213]=True
    raw[face]=(252,238,233)
    # Two measured color islands used as eye-observer tests (not renderer inputs).
    raw[124:132,142:154]=(58,164,197)
    raw[124:132,185:198]=(58,164,197)
    raw[140:149,169:179]=(243,205,189)  # original nose color
    raw[156:159,159:165]=(151,91,82)   # original mouth stroke fragment
    raw[156:159,175:182]=(151,91,82)
    return Image.fromarray(raw,"RGB"),face


def test_existing_source_masks_are_aligned_and_include_observed_face():
    masks,files=m.load_observed_masks()
    assert len(files)==10
    assert all(item["sha256"] and len(item["sha256"])==64 for item in files)
    assert masks["subject"].shape==(340,340)
    assert masks["face"].sum()==4808
    assert masks["subject"].sum()==54450
    assert (masks["face"]&masks["subject"]).sum() > 0.98*masks["face"].sum()
    assert masks["left_arm"].sum()>500 and masks["right_arm"].sum()>500


def test_detects_two_source_observed_eye_components_without_drawing():
    original,face=sample()
    pixels,observations=m.identify_eyes_from_source(original,face)
    assert len(pixels)==2 and len(observations)==2
    assert all(x["visibility_role"]=="audit_only_not_rendered" for x in observations)
    assert observations[0]["center_source_xy"][0]<observations[1]["center_source_xy"][0]
    assert all(v.sum()>20 for v in pixels)


def test_rejects_missing_or_ambiguous_eye_color():
    original,face=sample()
    rgb=np.asarray(original).copy()
    rgb[124:132,185:198]=(252,238,233)
    with pytest.raises(ValueError,match="Expected two"):
        m.identify_eyes_from_source(Image.fromarray(rgb),face)


def test_nose_mouth_hypotheses_are_non_authoritative():
    original,face=sample()
    out=m.facial_micro_observations(original,face)
    assert out["nose"]["source_observed_candidates"]
    assert out["mouth"]["source_observed_candidates"]
    assert all(v["authority"] is False and v["render_permission"] is False for v in out.values())


def test_face_plan_uses_only_observed_skin_rgb_not_eye_shapes():
    original,face=sample()
    eye_masks,observations=m.identify_eyes_from_source(original,face)
    painting,bands=m.face_plan(original,face,eye_masks)
    source=np.asarray(original.convert("RGB"))
    srcset={tuple(p) for p in source[face]}
    assert len(bands)==3
    assert all(tuple(b["original_rgb"]) in srcset for b in bands)
    assert all(int(q)>=2 for b in bands for q in b["original_rgb"])
    assert np.all(painting[face].mean(axis=1)>125)
    # The optical eye pixels do NOT appear as drawn new or copied features.
    assert not np.any(np.all(painting[eye_masks[0]]==source[eye_masks[0]],axis=1))


def test_palette_can_only_choose_actual_source_rgb_and_respects_budget():
    original,face=sample()
    painting,palette=m.source_part_palette(original,face,3)
    assert len(palette)<=3
    observed={tuple(v) for v in np.asarray(original)[face]}
    assert all(tuple(c) in observed for c in palette)
    assert all(tuple(c) in observed for c in np.unique(painting[face].reshape(-1,3),axis=0))


def test_background_support_clip_and_trial_contracts():
    mask=np.zeros((340,340),dtype=bool)
    mask[50:320,55:260]=True
    edge=m.foreground_boundary(mask)
    assert edge.sum()>0
    assert np.all(edge<=mask)
    assert not edge[200,120]  # interior is not accidentally marked boundary
    assert set(m.TRIALS)=={"A_subject_clip","B_face_parts_observed",
                          "C_part_palette","D_extended_parts"}
    assert len(m.DEFAULT_RECIPES)==4


def test_research_never_changes_production_or_runs_generator():
    code=(HERE/"semantic_art_mixer_v3_source_masks.py").read_text(encoding="utf-8")
    assert "import local_worker" not in code
    assert "import torch" not in code
    assert "from diffusers" not in code
    assert "from transformers" not in code
    assert "vsketch.Vsketch()" not in code
