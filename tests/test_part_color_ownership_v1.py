"""Source-palette distance regression: avoid signed int16 RGB squared overflow."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import face_parts_vector_scene_color_fixed as fixed


def test_opposite_source_colors_do_not_overflow_distance():
    # RGB difference 255 squared must be 65025, never negative/wrapped int16.
    a=np.array([255, 130, 8],dtype=np.uint8)
    b=np.array([255, 244, 237],dtype=np.uint8)
    delta=a.astype(np.int32)-b.astype(np.int32)
    assert int(np.sum(delta*delta,dtype=np.int64)) == 114**2+229**2
    assert int(np.sum(delta*delta,dtype=np.int64)) > 32767


def test_orange_region_stays_orange_in_source_palette_classification():
    rgb=np.full((340,340,3),(251,251,249),dtype=np.uint8)
    rgb[55:275,55:277]=(243,116,27)
    rgb[112:153,80:115]=(179,71,20)
    region=np.zeros((340,340),dtype=bool);region[50:280,50:280]=True
    output=fixed.region_colormasks(Image.fromarray(rgb,"RGB"),region,3)
    assert output
    # Dominant part base must be orange, not the gray/white background.
    base=[c for _,c,k in output if k=="base"]
    assert len(base)==1 and base[0][0]>base[0][1]*1.5
    # All segment colors must be observed in source region.
    observed={tuple(p) for p in rgb[region]}
    assert all(tuple(c) in observed for _,c,_ in output)


def test_no_production_or_neural_renderer_dependencies():
    code=Path(fixed.__file__).read_text(encoding="utf-8")
    assert "import torch" not in code
    assert "from diffusers" not in code
    assert "import local_worker" not in code
    assert "delta*delta" in code
    assert "np.int64" in code
