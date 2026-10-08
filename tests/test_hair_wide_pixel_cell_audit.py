"""Research-only full-head source hair mask boundary audit."""
from pathlib import Path
import sys
import numpy as np
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import hair_wide_pixel_cell_audit as m

def test_only_hair_source_svg_without_raster_or_face(tmp_path):
    area=np.zeros((340,340),dtype=bool)
    area[100:130,160:180]=True
    out=tmp_path/"hair.svg"
    vertices,n=m.write_hair(area,(229,106,45),out,0.35)
    assert vertices>0 and n>0
    root=ET.parse(out).getroot()
    ns="{http://www.w3.org/2000/svg}"
    assert not root.findall(".//"+ns+"image")
    assert len(root.findall(".//"+ns+"path"))==1
    assert root.findall(".//"+ns+"path")[0].get("data-part")=="hair"

def test_research_does_not_overwrite_original_mask_or_face_plate():
    code=Path(m.__file__).read_text(encoding="utf-8")
    assert 'derived=old_hair|missing' in code
    assert 'newly=derived&~old_hair' in code
    assert 'if int(newly.sum())!=390' in code
    assert "from diffusers" not in code
    assert "import torch" not in code
    assert '"core_golden_pass":False' in code
