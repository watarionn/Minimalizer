"""Source-only goggles candidate diagnostics regression."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_source_observer as m

def test_candidates_stay_inside_manually_defined_diagnostic_window():
    a=np.zeros((340,340,3),dtype=np.uint8)
    a[:]=(240,120,32)
    roi,p=m.observe(Image.fromarray(a,"RGB"))
    assert int(roi.sum())==137*66
    assert p
    assert all(not np.any(mask&~roi) for mask in p.values())

def test_goggles_are_not_claimed_verified():
    code=Path(m.__file__).read_text(encoding="utf-8")
    assert '"verified_goggles_segmentation":False' in code
    assert '"goggles_svg_generated":False' in code
    assert "from diffusers" not in code
    assert "import torch" not in code
