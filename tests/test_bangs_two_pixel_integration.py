"""GC001 bang integration contracts; base remains explicitly incomplete."""
from pathlib import Path
import sys,json
from xml.etree import ElementTree as ET
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import bangs_two_pixel_integration as m

def test_missing_coordinates_order_yx():
    a=np.zeros((340,340),bool)
    b=np.zeros((340,340),bool)
    a[130,175]=True;a[131,177]=True
    report=m.inspect(a,b)
    assert report["missing_yx"]==[[130,175],[131,177]]
    assert report["covered"]==0

def test_only_original_hair_parts_can_be_stitched(tmp_path):
    a=tmp_path/"base.svg";b=tmp_path/"source.svg";o=tmp_path/"result.svg"
    ns="http://www.w3.org/2000/svg"
    a.write_text(f'<svg xmlns="{ns}"><path data-part="hair" d="M 1 1 L 4 1 L 4 4 Z" fill="#ed7032"/></svg>')
    b.write_text(f'<svg xmlns="{ns}"><path data-part="hair" d="M 10 10 L 11 10 L 11 11 Z" fill="#f28135"/></svg>')
    assert m.stitch(a,b,o)==1
    root=ET.parse(o).getroot()
    paths=root.findall(".//{"+ns+"}path")
    assert len(paths)==2
    assert paths[-1].get("data-layer")=="source-bang-cell-verified"
    assert not root.findall(".//{"+ns+"}image")

def test_refuse_subject_underlay(tmp_path):
    a=tmp_path/"base.svg";b=tmp_path/"source.svg";o=tmp_path/"result.svg"
    ns="http://www.w3.org/2000/svg"
    a.write_text(f'<svg xmlns="{ns}"><path data-part="subject" d="M0 0L1 1Z" fill="#eee"/></svg>')
    b.write_text(f'<svg xmlns="{ns}"><path data-part="hair" d="M0 0L1 1Z" fill="#b63"/></svg>')
    try:
        m.stitch(a,b,o)
    except AssertionError:
        pass
    else:
        raise AssertionError("Should reject implicit skin-colored subject plate")

def test_no_generated_face_or_production_code_changes():
    code=Path(m.__file__).read_text(encoding="utf-8")
    assert "from diffusers" not in code and "import torch" not in code
    assert "full_character_golden_pass" in code
    assert "changed_outside_2px_source_neighborhood" in code
