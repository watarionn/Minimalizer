"""Regression for central bangs: source-connected component and no face plate."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from xml.etree import ElementTree as ET
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import bangs_continuity_source_bridge as b

def synthetic():
    a=np.zeros((340,340,3),dtype=np.uint8)
    a[:]=(252,239,233)
    a[100:134,150:178]=(234,108,43)
    face=np.zeros((340,340),dtype=bool);face[112:195,140:207]=True
    hair=np.zeros((340,340),dtype=bool);hair[100:112,140:208]=True
    owner=np.ones((340,340),dtype=bool)
    return Image.fromarray(a,"RGB"),{"face":face,"hair":hair,"subject":owner}

def test_missed_connected_hair_from_original_crosses_face():
    src,masks=synthetic()
    missing,whole=b.extract(src,masks)
    assert int(whole.sum())==34*28
    assert int(missing.sum())==22*28
    assert (missing&~masks["face"]).sum()==0
    assert (missing&masks["hair"]).sum()==0

def test_reject_disconnected_or_missing_top_to_tip():
    src,masks=synthetic()
    a=np.asarray(src).copy()
    a[113:133,150:178]=(252,239,233)
    with pytest.raises(ValueError):
        b.extract(Image.fromarray(a),masks)

def test_svg_repair_is_not_skin_plate():
    s=Path(b.__file__).read_text(encoding="utf-8")
    assert '"data-part":"hair"' in s
    assert 'source_missing_bang_pixels' in s
    assert "root.findall(\".//{%s}path[@data-part='subject']\"" in s
    assert "import torch" not in s
    assert "from diffusers" not in s
