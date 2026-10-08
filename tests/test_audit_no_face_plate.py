"""Regression: detect a disguised face plate beneath observed face/hair."""
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
import pytest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import audit_no_face_plate as m

def synthetic():
    face=np.zeros((40,40),dtype=bool);face[9:21,11:25]=True
    hair=np.zeros((40,40),dtype=bool);hair[3:10,8:28]=True
    body=np.ones((40,40),dtype=bool)
    return {"face":face,"hair":hair,"subject":body}

def test_opaque_subject_underlay_is_rejected_as_face_plate(tmp_path):
    path=tmp_path/"scene.svg"
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><path data-part="subject" data-layer="underlay" fill="#f4d8cf" d="M 0 0 L 40 0 L 40 40 Z" /></svg>')
    report=m.audit(path,synthetic())
    assert report["visual_status"]=="NO_GO_FACE_PLATE"
    assert report["source_face_pixels_covered_by_plate"]==168
    assert report["source_hair_pixels_covered_by_plate"]>0
    assert report["do_not_promote"] is True

def test_missing_subject_provenance_fails_closed(tmp_path):
    path=tmp_path/"unknown.svg"
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><path data-part="hair" fill="#e68c4c" d="M 0 0 L 40 0 L 40 40 Z" /></svg>')
    with pytest.raises(ValueError,match="exactly one"):
        m.audit(path,synthetic())

def test_no_face_overlay_false_compliance_language():
    code=Path(m.__file__).read_text(encoding="utf-8")
    assert "NO_GO_FACE_PLATE" in code
    assert "do_not_promote" in code
    assert "from diffusers" not in code
    assert "import torch" not in code
