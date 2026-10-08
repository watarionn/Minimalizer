"""Isolated source-color garment composition and goggle confidence guard."""
import sys
from pathlib import Path
import numpy as np
from xml.etree import ElementTree as ET
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_clothing_source_poc as m

def test_preserve_fringe_and_original_garment_z_order(tmp_path):
    ns="http://www.w3.org/2000/svg"
    root=ET.Element("{%s}svg"%ns)
    ET.SubElement(root,"{%s}path"%ns,{"data-part":"major_clothing","d":"M1 1L2 1L2 2Z"})
    ET.SubElement(root,"{%s}path"%ns,{"data-part":"hair","d":"M1 1L2 1L2 2Z"})
    ET.SubElement(root,"{%s}path"%ns,{"data-part":"lower_body","d":"M1 1L2 1L2 2Z"})
    for _ in range(3):ET.SubElement(root,"{%s}path"%ns,{"data-part":"hair","data-layer":"source-bang-cell-verified","d":"M1 1L2 1L2 2Z"})
    class FauxSource:
        def convert(self,*args):
            from PIL import Image
            return Image.fromarray(np.full((340,340,3),[30,80,160],dtype=np.uint8))
    masks={"subject":np.ones((340,340),bool)}
    for role in ("major_clothing","lower_body"):
        mask=np.zeros((340,340),bool);mask[130:165,155:190]=True;masks[role]=mask
    records=m.replace_roles(ET.ElementTree(root),FauxSource(),masks)
    assert records and all(r["part"] in ("major_clothing","lower_body") for r in records)
    assert len([e for e in root if e.get("data-layer")=="source-bang-cell-verified"])==3
    assert not [e for e in root if e.get("data-part") in ("face","subject")]

def test_no_unobserved_goggle_claim():
    src=Path(m.__file__).read_text(encoding="utf-8")
    assert '"goggles_mask_verified":False' in src
    assert "from diffusers" not in src and "import torch" not in src
    assert '"core_golden_pass":False' in src
