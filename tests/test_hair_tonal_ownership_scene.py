"""Whole-hair toner integration and no-face-plate tests."""
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import hair_tonal_ownership_scene as m

def test_original_hair_replaced_at_original_z_order(tmp_path):
    ns="http://www.w3.org/2000/svg"
    root=ET.Element("{%s}svg"%ns)
    ET.SubElement(root,"{%s}path"%ns,{"data-part":"torso","d":"M1 1L2 2Z"})
    ET.SubElement(root,"{%s}path"%ns,{"data-part":"hair","d":"M2 2L3 3Z","data-layer":"base"})
    ET.SubElement(root,"{%s}path"%ns,{"data-part":"accessory","d":"M3 3L4 4Z"})
    for _ in range(3):
        ET.SubElement(root,"{%s}path"%ns,{"data-part":"hair","d":"M4 4L5 5Z","data-layer":"source-bang-cell-verified"})
    mask=np.zeros((340,340),bool);mask[105:125,155:180]=True
    data=m.replace_hair(ET.ElementTree(root),[(mask,(234,108,43),"base")])
    assert data and [x.get("data-part") for x in list(root)][:3]==["torso","hair","accessory"]
    assert len([x for x in root if x.get("data-layer")=="source-bang-cell-verified"])==3
    assert not [x for x in root if x.get("data-part")=="face"]

def test_refuse_missing_fringe_or_broad_skin():
    ns="http://www.w3.org/2000/svg"
    root=ET.Element("{%s}svg"%ns)
    ET.SubElement(root,"{%s}path"%ns,{"data-part":"hair","d":"M1 1L2 2Z"})
    mask=np.zeros((340,340),bool);mask[110:130,160:175]=True
    with pytest.raises(AssertionError):
        m.replace_hair(ET.ElementTree(root),[(mask,(233,100,40),"base")])

def test_no_generative_or_production_mutation():
    source=Path(m.__file__).read_text(encoding="utf-8")
    assert "from diffusers" not in source and "import torch" not in source
    assert '"full_character_golden_pass":False' in source
    assert "source-owned-cell-" in source
