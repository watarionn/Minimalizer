"""Regression: goggles edge topology is evidence, not shape invention."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_edge_topology as m

def test_edge_candidates_stay_in_diagnostic_window():
    rgb=np.full((340,340,3),(235,150,50),np.uint8)
    rgb[50:80,120:155]=(80,180,230)
    hair=np.zeros((340,340),bool)
    hair[38:104,104:241]=True
    edges,features=m.inspect(Image.fromarray(rgb),{"hair":hair})
    assert edges.shape==(340,340)
    assert not np.any(edges[:38]) and not np.any(edges[104:])
    assert not np.any(edges[:,:104]) and not np.any(edges[:,241:])
    assert all(104<=c["xywh"][0] and c["xywh"][1]>=38 for c in features)

def test_no_false_verified_goggles_or_generation():
    t=Path(m.__file__).read_text(encoding="utf-8")
    assert '"lens_frame_verified":False' in t
    assert '"goggle_mask_generated":False' in t
    assert '"goggle_svg_generated":False' in t
    assert "from diffusers" not in t and "import torch" not in t
