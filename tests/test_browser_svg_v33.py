"""v33 non-generative SVG geometry and source-provenance contracts."""
from __future__ import annotations
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"tools/vectorize_browser_planes_v33.py"
AUDIT=ROOT/"tools/audit_browser_svg_v33_chrome.py"

def load():
    s=importlib.util.spec_from_file_location("v33",MODULE)
    v=importlib.util.module_from_spec(s)
    assert s.loader
    s.loader.exec_module(v)
    return v

def signed_area(loop):
    return sum(x*y2-x2*y for (x,y),(x2,y2)
      in zip(loop,loop[1:]+loop[:1]))/2

def test_pixel_rectangle_exact_geometry_area_and_path():
    v=load()
    m=np.zeros((12,12),dtype=bool)
    m[1:10,2:9]=True
    loops=v.boundaries(m)
    assert len(loops)==1
    assert len(loops[0])==4
    assert abs(signed_area(loops[0]))==int(m.sum())
    p,n=v.path_for(loops[0],0)
    assert p.startswith("M") and p.endswith("Z")
    assert n==4

def test_hole_has_even_odd_traced_opposite_area():
    v=load()
    m=np.zeros((12,12),dtype=bool)
    m[1:11,1:11]=True
    m[4:8,4:8]=False
    loops=v.boundaries(m)
    assert len(loops)==2
    assert sum(signed_area(c) for c in loops)==int(m.sum())
    assert {1 if signed_area(c)>0 else -1 for c in loops}=={-1,1}

def test_diagonal_touch_does_not_merge_four_connected_shapes():
    v=load()
    m=np.zeros((7,7),dtype=bool)
    m[2,2]=True;m[3,3]=True
    loops=v.boundaries(m)
    assert len(loops)==2
    assert all(len(c)==4 for c in loops)
    assert sum(signed_area(c) for c in loops)==2

def test_empty_mask_and_hollow_nested_shapes():
    v=load()
    assert v.boundaries(np.zeros((7,7),dtype=bool))==[]
    m=np.zeros((20,20),dtype=bool)
    m[1:19,1:19]=True
    m[3:17,3:17]=False
    m[6:14,6:14]=True
    m[8:12,8:12]=False
    loops=v.boundaries(m)
    assert len(loops)==4
    assert sum(signed_area(c) for c in loops)==int(m.sum())

def test_simplified_candidate_must_not_be_granted_authority():
    v=load()
    m=np.zeros((14,14),dtype=bool)
    m[2:8,2:12]=True
    m[8:12,4:10]=True
    loop=max(v.boundaries(m),key=len)
    exact,n=v.path_for(loop,0)
    reduced,nr=v.path_for(loop,1.1)
    assert nr<=n
    assert exact.startswith("M") and reduced.startswith("M")
    assert not "production" in exact.lower()
    assert 'outputAuthority":False' in MODULE.read_text(encoding="utf-8")
    assert '"candidateAcceptance":"RESEARCH_ONLY"' in AUDIT.read_text(encoding="utf-8") or (
      "REJECT_UNSAFE" in AUDIT.read_text(encoding="utf-8"))
    assert "pixelsDifferentFromV32" in AUDIT.read_text(encoding="utf-8")
    assert "newRasterRGBCount" in AUDIT.read_text(encoding="utf-8")

def test_no_production_path_or_external_image_inference():
    index=(ROOT/"web/static/index.html").read_text(encoding="utf-8")
    app=(ROOT/"web/static/app.js").read_text(encoding="utf-8")
    for name in ("vectorize_browser_planes_v33","audit_browser_svg_v33_chrome"):
        assert name not in index and name not in app
    assert 'containsRasterFacetAsBackground":True' in MODULE.read_text(encoding="utf-8")
    assert "base64.b64encode(base_path.read_bytes())" in MODULE.read_text(encoding="utf-8")

def test_bad_source_mask_throws_in_source_dimension_gate(tmp_path,monkeypatch):
    v=load()
    monkeypatch.setattr(v,"ROOT",tmp_path)
    with pytest.raises(FileNotFoundError):
        v.vectorize("Kyoko","connected_fine",0.0,tmp_path/"should_not_exist.svg")
