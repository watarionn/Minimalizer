"""Pixel cell contour research regression gates."""
from pathlib import Path
import sys
import numpy as np
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import bangs_pixel_cell_boundary as m

def test_pixel_cell_closed_path_on_original_footprint():
    pixels=np.zeros((340,340),dtype=bool)
    pixels[115:135,155:175]=True
    data,contours,vertices=m.pixel_cell_path(pixels)
    assert data.startswith("M ")
    assert " Z" in data
    assert contours>=1 and vertices>=4
    assert ".25" in data and ".75" in data  # doubled OpenCV pixel-grid coordinates

def test_svg_is_source_hair_only(tmp_path):
    mask=np.zeros((340,340),dtype=bool)
    mask[114:131,157:178]=True
    destination=tmp_path/"hair.svg"
    vertices,count=m.build([(mask,(220,95,40),"source")],destination)
    assert vertices>=4 and count>0
    root=ET.parse(destination).getroot()
    children=root.findall(".//{http://www.w3.org/2000/svg}path")
    assert len(children)==1
    assert children[0].get("data-part")=="hair"
    assert root.findall(".//{http://www.w3.org/2000/svg}image")==[]

def test_isolated_from_production_and_generative_models():
    source=Path(m.__file__).read_text(encoding="utf-8")
    assert "import torch" not in source
    assert "from diffusers" not in source
    assert "import local_worker" not in source
    assert '"core_golden_pass":False' in source
