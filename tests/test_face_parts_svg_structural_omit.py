"""Tests for honest feature-scoped SVG omission (not full Core SVG)."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from xml.etree import ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import face_parts_svg_structural_omit as m


def test_real_svg_research_golden_source_only():
    # No need to regenerate a remote user's private source in unit tests.
    source=Path(m.__file__).read_text(encoding="utf-8")
    assert "from diffusers" not in source
    assert "import torch" not in source
    assert "from local_worker" not in source
    assert "draw.rectangle" not in source.split("def make_svg(")[1].split("def render_svg_preview")[0]
    assert "SVGNS" in source


def test_path_export_contains_no_face_overlay_or_raster(tmp_path):
    out=tmp_path/"research.svg"
    m.make_svg([[(0,0),(2,2),(4,3)],[(10,10),(20,20)]],out)
    xml=out.read_text(encoding="utf-8")
    assert "<path" in xml
    assert "<image" not in xml
    assert "<rect" not in xml
    assert "<circle" not in xml
    assert 'fill="none"' in xml
    root=ET.parse(out).getroot()
    assert len(root.findall(".//{http://www.w3.org/2000/svg}path"))==2


def test_filter_excludes_feature_intersecting_line_but_keeps_nonfeature():
    rgb=np.ones((340,340,3),dtype=np.uint8)*255
    # High contrast feature stroke and another separate outline, no synthetic
    # fill. The observed feature mask intersects the first source edge.
    rgb[160:165,160:190]=0
    rgb[215:220,90:250]=0
    mask=np.zeros((340,340),dtype=bool)
    mask[158:170,150:200]=True
    hairs=np.zeros_like(mask)
    face=np.zeros_like(mask)
    face[115:180,125:216]=True
    subject=np.ones_like(mask)
    paths,meta=m.paths_for_observed_edges(Image.fromarray(rgb,"RGB"),
        {"face":face,"hair":hairs,"subject":subject},
        {"eye_left":mask})
    assert meta["excluded_face_feature_intersecting_paths"]>0
    assert meta["retained_paths"]>0


def test_source_only_output_has_no_background_fill():
    code=Path(m.__file__).read_text(encoding="utf-8")
    assert "ET.SubElement(root" in code
    assert '"fill":"none"' in code
    assert "not_full_character_render" in code
    assert '"core_golden_pass":False' in code
