"""Source-only fringe tonal safety and geometry checks."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import bangs_source_tonal_width_v2 as m

def test_tonal_palette_and_masks_from_source_only():
    a=np.full((340,340,3),(251,231,210),dtype=np.uint8)
    a[105:131,152:179]=(233,110,40)
    a[113:126,158:169]=(177,72,26)
    a[119:127,161:167]=(250,154,58)
    mask=np.zeros((340,340),dtype=bool)
    mask[105:131,152:179]=True
    layers,counts=m.tonal_layers(Image.fromarray(a,"RGB"),mask)
    assert 1<=len(layers)<=3
    assert sum(counts)==int(mask.sum())
    colors={tuple(c) for c in a[mask]}
    assert all(tuple(rgb) in colors for _,rgb,_ in layers)
    assert np.array_equal(layers[0][0],mask)
    assert all(np.all(region<=mask) for region,_,_ in layers)

def test_isolated_research_cannot_draw_face_ellipse():
    s=Path(m.__file__).read_text(encoding="utf-8")
    assert "data-part\":\"hair" in s
    assert "data-part='subject'" in s
    assert "data-part='face'" in s
    assert "import torch" not in s
    assert "from diffusers" not in s
    assert "core_golden_pass" in s
