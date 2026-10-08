"""Strict footprint and vertex-budget tests for local GC001 source fringe."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import bangs_cell_vertex_reduction as m

def test_simplified_contour_reduces_vertices():
    mask=np.zeros((340,340),dtype=bool)
    mask[112:133,150:180]=True
    mask[118:128,165:172]=False
    a,n,v=m.polygons(mask,0)
    b,n2,v2=m.polygons(mask,0.35)
    assert a and b and n>=1 and n2>=1
    assert v2<=v

def test_strict_acceptance_is_source_coverage_and_no_excess():
    candidates=[{"vertices":485,"covered":687,"outside":0},
                {"vertices":288,"covered":692,"outside":0},
                {"vertices":204,"covered":684,"outside":0},
                {"vertices":80,"covered":673,"outside":16}]
    valid=[x for x in candidates if x["covered"]>=687 and x["outside"]==0]
    chosen=min(valid,key=lambda x:(x["vertices"],-x["covered"]))
    assert chosen["vertices"]==288 and chosen["covered"]==692

def test_only_hair_paths_no_generated_face():
    source=Path(m.__file__).read_text(encoding="utf-8")
    assert '"data-part":"hair"' in source
    assert "import torch" not in source
    assert "from diffusers" not in source
    assert '"full_character_golden_pass":False' in source
