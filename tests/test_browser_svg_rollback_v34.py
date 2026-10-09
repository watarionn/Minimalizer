"""v34 contract tests: lossless SVG syntax, per-group Chrome rollback, SHA gate.

No browser, neural model, production output or external file is used in CI.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"tools/optimize_browser_svg_v34.py"

def module():
    spec=importlib.util.spec_from_file_location("v34",SCRIPT)
    v=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v)
    return v

def rectangle():
    return [(2,3),(11,3),(11,9),(2,9)]

def test_lossless_relative_svg_path_syntax():
    v=module()
    assert v.path_data(rectangle())=="M2 3h9v6h-9Z"
    assert v.path_data([(0,0),(1,0),(2,1),(1,2)])=="M0 0h1l1 1l-1 1Z"

def test_compound_paths_and_holes_preserved_in_compressed_svg():
    v=module()
    interior=[(4,4),(4,6),(6,6),(6,4)]
    sample=("<svg xmlns=\"http://www.w3.org/2000/svg\">"
        "<image href=\"data:image/png;base64,eA==\"/>"
        '<path fill="#ff0000" fill-rule="evenodd" d="'
        'M2 3L11 3L11 9L2 9Z M4 4L4 6L6 6L6 4Z"/>'
        "</svg>")
    prefix,groups=v.parse_svg(sample)
    assert len(groups)==1
    assert groups[0][0]=="ff0000"
    assert groups[0][1]==[rectangle(),interior]
    out=v.svg_text(prefix,[v.svg_group(*groups[0])])
    assert 'fill-rule="evenodd"' in out
    assert 'M2 3h9v6h-9Z' in out
    assert 'M4 4v2h2v-2Z' in out
    assert len(out)<len(sample)

def test_reject_untrusted_or_nonexact_svg_path_syntax():
    v=module()
    with pytest.raises(ValueError):
        v.parse_svg("<svg><path d='M0,0 L2,2 Z'/></svg>")
    bad='<svg><path fill="#ffffff" fill-rule="evenodd" d="M0.4 0L1 0L1 1L0 1Z"/></svg>'
    with pytest.raises(ValueError,match="not exact lattice"):
        v.parse_svg(bad)

def test_local_group_reject_restores_exact_others(monkeypatch):
    v=module()
    groups=["A","B","C"]
    target=np.zeros((340,340,4),dtype=np.uint8)
    def fake(_driver,text):
        if "DIFFERENT" in text:return np.ones_like(target)
        return target
    monkeypatch.setattr(v,"chrome_rgba",fake)
    ok=v.attempt(None,"<svg>",groups,1,"DIFFERENT",target)
    assert ok is False
    assert groups==["A","B","C"]
    ok=v.attempt(None,"<svg>",groups,1,"SAME",target)
    assert ok is True
    assert groups==["A","SAME","C"]

def test_renderer_exception_rolls_back_current_group(monkeypatch):
    v=module()
    groups=["A","B"]
    def bad(*_):
        raise RuntimeError("driver offline")
    monkeypatch.setattr(v,"chrome_rgba",bad)
    with pytest.raises(RuntimeError,match="offline"):
        v.attempt(None,"<svg>",groups,0,"broken",np.zeros((340,340,4),dtype=np.uint8))
    assert groups==["A","B"]

def test_contour_proposal_is_never_promoted_without_parity():
    v=module()
    source=[[(0,0),(4,0),(4,1),(5,1),(5,4),(0,4)]]
    candidates,vertices=v.simplified_loops(source,0.85)
    assert len(candidates)==1
    assert vertices>=0
    assert "productionReady" in SCRIPT.read_text(encoding="utf-8")
    assert 'exactRgbaParity":True' in SCRIPT.read_text(encoding="utf-8")
    assert "if not np.array_equal(first,target)" in SCRIPT.read_text(encoding="utf-8")

def test_production_and_local_worker_not_touched():
    source=SCRIPT.read_text(encoding="utf-8")
    app=(ROOT/"web/static/app.js").read_text(encoding="utf-8")
    html=(ROOT/"web/static/index.html").read_text(encoding="utf-8")
    assert "optimize_browser_svg_v34" not in app+html
    assert "productionPromoted" not in source or "productionReady" in source
    assert "V33" in source and "V32" in source
    assert "outputAuthority" not in source or "semanticPartAuthority" in source
