"""Verify observed edge trace exports never invent a closed goggle surface."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_source_contour_trace as m

def test_edge_paths_use_original_image_coordinates_only():
    arr=np.zeros((340,340,3),np.uint8)
    arr[40:90,106:200]=[210,160,40]
    arr[50:70,120:175]=[40,180,220]
    result=m.trace(Image.fromarray(arr))
    assert set(result)==set(m.ZONES)
    for name,paths in result.items():
        x0,y0,x1,y1=m.ZONES[name]
        assert all(x0<=x<x1 and y0<=y<y1 for p in paths for x,y in p["points"])

def test_no_semantic_polygon_or_goggle_render_permission():
    code=Path(m.__file__).read_text(encoding="utf-8")
    assert '"verified_visible_goggle_contours":False' in code
    assert '"svg_render_authorized":False' in code
    assert '"svg_generated":False' in code
    assert "from diffusers" not in code
