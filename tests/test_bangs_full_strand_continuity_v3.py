"""Whole source strand continuity and fail-closed vector test."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import bangs_full_strand_continuity_v3 as m

def test_row_coverage_calculated_on_actual_source_only():
    src=np.zeros((340,340),dtype=bool)
    src[107:128,154:178]=True
    src[128:135,161:170]=True
    render=src.copy()
    render[120,160:164]=False
    rows=m.verify_continuity(src,render)
    assert any(row["source_coverage"]<1 for row in rows)
    assert rows[0]["source_coverage"]==1
    assert rows[-1]["y"]==134

def test_refuse_lost_reference_rows():
    src=np.zeros((340,340),dtype=bool)
    src[111:118,152:175]=True
    with pytest.raises(ValueError,match="Missing row"):
        m.verify_continuity(src,src)

def test_source_tonal_colors_are_input_pixels():
    src=np.full((340,340,3),(250,229,210),dtype=np.uint8)
    src[106:133,150:179]=(227,100,32)
    src[109:123,159:170]=(167,61,24)
    region=np.zeros((340,340),bool);region[106:133,150:179]=True
    paths,counts=m.compose_layers(Image.fromarray(src),region)
    assert paths
    observed={tuple(v) for v in src[region]}
    assert all(tuple(color) in observed for _,color,_,_,_,_ in paths)

def test_only_source_hair_no_skin_plate():
    s=Path(m.__file__).read_text(encoding="utf-8")
    assert "data-part" in s and '"hair"' in s
    assert 'data-part=\'subject\'' in s
    assert 'data-part=\'face\'' in s
    assert "from diffusers" not in s and "import torch" not in s
    assert "core_golden_pass" in s
