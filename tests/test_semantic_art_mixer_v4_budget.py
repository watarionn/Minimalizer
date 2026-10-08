"""Regression controls for v4 color-budget NO-GO research."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pytest
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import semantic_art_mixer_v4_budget as v4


def test_components_are_raster_proxy_not_svg_budget():
    a=np.zeros((16,16,3),dtype=np.uint8)
    a[:]=(100,120,140)
    mask=np.zeros((16,16),dtype=bool)
    mask[2:14,2:14]=True
    a[4:7,4:7]=(200,40,30)
    a[10:12,10:12]=(200,40,30)
    runs,colors=v4.component_count(a,mask)
    assert runs==3 and colors==2


def test_source_medoid_only_and_flat_palette_one_color():
    a=np.full((340,340,3),(220,140,80),dtype=np.uint8)
    a[15:35,10:32]=(80,90,150)
    a[48:70,10:38]=(140,180,80)
    area=np.zeros((340,340),dtype=bool)
    area[10:80,5:45]=True
    im=Image.fromarray(a,"RGB")
    out,palette=v4.coherent_palette(im,area,3,"flat")
    assert len(palette)==1
    assert tuple(palette[0]) in {tuple(v) for v in np.unique(a[area],axis=0)}
    assert len(np.unique(out[area],axis=0))==1


def test_regional_palette_has_only_source_colors_and_cap():
    a=np.full((340,340,3),(225,140,78),dtype=np.uint8)
    a[15:45,15:45]=(55,90,220)
    a[45:75,15:45]=(95,175,110)
    region=np.zeros((340,340),dtype=bool)
    region[10:80,10:80]=True
    out,palette=v4.coherent_palette(Image.fromarray(a,"RGB"),region,3,"regional_median")
    allowed={tuple(c) for c in np.unique(a[region],axis=0)}
    assert len(palette)<=3
    assert all(tuple(c) in allowed for c in np.unique(out[region],axis=0))


def test_reject_unknown_reduction():
    im=Image.new("RGB",(340,340),(200,190,180))
    with pytest.raises(ValueError):
        v4.coherent_palette(im,np.ones((340,340),dtype=bool),3,"generative")


def test_no_production_models_or_ui_changes():
    s=Path(v4.__file__).read_text(encoding="utf-8")
    assert "import torch" not in s
    assert "from diffusers" not in s
    assert "import local_worker" not in s
    assert v4.BUDGETS=={"E3":3,"E5":5}
