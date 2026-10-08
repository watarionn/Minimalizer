"""Offline regression of feature-only rendering, no face cover-up."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import face_parts_only_v1 as m


def fixture():
    rgb=np.full((340,340,3),(239,190,174),dtype=np.uint8)
    rgb[126:133,143:155]=(59,165,199)
    rgb[126:133,187:199]=(59,165,199)
    rgb[143:151,170:180]=(243,205,189)
    rgb[155:158,160:166]=(150,90,80)
    rgb[155:158,176:183]=(150,90,80)
    face=np.zeros((340,340),bool);face[109:185,131:214]=True
    hair=np.zeros((340,340),bool);hair[107:125,130:214]=True
    subject=np.ones((340,340),bool)
    return Image.fromarray(rgb,"RGB"),{"face":face,"hair":hair,"subject":subject}


def test_detects_feature_only_components_and_unverified_brow():
    source,masks=fixture()
    parts,meta=m.source_components(source,masks)
    assert set(parts)==set(m.PARTS)
    assert all(not np.any(mask&masks["hair"]) for mask in parts.values())
    assert meta["brow"]["status"]=="NOT_VERIFIED"
    assert not meta["brow"]["render_allowed"]


def test_a_preserves_face_and_fringe_b_changes_only_part_pixels():
    source,masks=fixture()
    src=np.asarray(source)
    style=Image.new("RGB",m.SIZE,(8,20,33))
    a,b,c,metrics=m.process_abc(source,masks,style)
    aa=np.asarray(a);bb=np.asarray(b)
    parts,_=m.source_components(source,masks)
    union=np.logical_or.reduce(list(parts.values()))
    assert np.array_equal(aa[masks["face"]],src[masks["face"]])
    assert np.array_equal(aa[masks["hair"]],src[masks["hair"]])
    assert np.array_equal(bb[masks["face"]&~union],src[masks["face"]&~union])
    assert np.array_equal(bb[masks["hair"]],src[masks["hair"]])
    assert not np.any(np.any(bb!=aa,axis=2)&~union)
    assert metrics["face_nonfeature_changed_from_original"]==0
    assert metrics["hair_pixels_changed_from_original_b"]==0
    assert metrics["b_changed_outside_verified_features"]==0
    assert c["status"]=="BLOCKED_FAIL_CLOSED"
    assert not c["generated_output"]


def test_b_medoids_only_existing_color_no_hallucination():
    source,masks=fixture()
    rgb=np.asarray(source)
    parts,_=m.source_components(source,masks)
    for mask in parts.values():
        color=m.reduce_one_observed_part(rgb,mask)
        assert any(np.array_equal(color,part) for part in rgb[mask])


def test_missing_eye_refuses_to_guess():
    source,masks=fixture()
    raw=np.asarray(source).copy()
    raw[126:133,187:199]=(239,190,174)
    with pytest.raises(ValueError,match="Expected two"):
        m.source_components(Image.fromarray(raw),masks)


def test_scope_only_research_no_face_overlay():
    text=Path(m.__file__).read_text(encoding="utf-8")
    assert "from diffusers" not in text and "import torch" not in text
    assert "import local_worker" not in text
    assert "face_plan(" not in text
    assert "face&~union" in text
