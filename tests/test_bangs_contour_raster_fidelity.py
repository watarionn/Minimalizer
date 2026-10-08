"""Regression for source-locked fringe rasterization parameter study."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import bangs_contour_raster_fidelity as m

def test_alpha_resampling_shape_and_threshold(tmp_path):
    path=tmp_path/"rgba.png"
    img=Image.new("RGBA",(680,680),(0,0,0,0))
    img.putpixel((300,300),(255,80,10,255))
    img.save(path)
    assert m.alpha_mask(path,(340,340),Image.Resampling.NEAREST).shape==(340,340)
    assert m.alpha_mask(path,(340,340),Image.Resampling.LANCZOS).dtype==bool

def test_svg_uses_original_hair_only(tmp_path):
    mask=np.zeros((340,340),dtype=bool)
    mask[106:130,150:185]=True
    path=tmp_path/"fringe.svg"
    verts=m.make_svg([(mask,(230,110,45),"base")],path,0.5)
    svg=path.read_text(encoding="utf-8")
    assert verts>0
    assert 'translate(0.5 0.5)' in svg
    assert 'data-part="hair"' in svg
    assert "data-part=\"face\"" not in svg
    assert "<image" not in svg

def test_no_production_or_generator_imports():
    source=Path(m.__file__).read_text(encoding="utf-8")
    assert "import torch" not in source
    assert "from diffusers" not in source
    assert "import local_worker" not in source
    assert 'golden_pass":False' in source
