"""R4 independent cross-engine Golden comparison and source-layer split safety."""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from verify_public_r4_cross_engine import compare_rgba
from verify_public_r4_component_split import split_source

def test_r4_rgba_alpha_and_mismatch_bbox_are_strict():
    a=bytes([0,0,0,255,40,50,60,255,200,100,50,0,10,20,30,255])
    b=bytes([0,0,0,255,40,50,60,254,200,100,50,1,10,20,30,255])
    d=compare_rgba(a,b)
    assert d["differentPixels"]==2 and d["alphaDifferentPixels"]==2
    assert d["maxChannelDelta"]==1
    assert d["boundingBox"]==[0,0,2,2]
    assert compare_rgba(a,a)["exact"]
    with pytest.raises(ValueError):compare_rgba(b,b[:8])

def test_component_split_contains_only_real_source_paths_and_raster():
    prefix=('<svg xmlns="http://www.w3.org/2000/svg" width="340" height="340">'
            '<image x="0" y="0" width="340" height="340" href="data:image/png;base64,eA=="/>')
    shape='<path fill="#ab12ff" fill-rule="evenodd" d="M2 2L8 2L8 8Z"/>'
    parts=split_source(prefix+shape+'</svg>')
    assert "data:image/png;base64,eA==" in parts["facet"]
    assert "<path " not in parts["facet"]
    assert "<path " in parts["paths"]
    assert "<image " not in parts["paths"]
    assert parts["paths"].count("#ab12ff")==1

def test_malformed_or_ambiguous_xml_is_rejected():
    prefix='<svg><image href="data:image/png;base64,eA=="/>'
    shape='<path fill="#ab12ff" fill-rule="evenodd" d="M2 2L8 2L8 8Z"/>'
    for bad in ("<svg>"+shape+"</svg>",prefix+shape+"more</svg>",
                prefix+shape+shape.replace("fill=","evil=")+"</svg>",
                prefix.replace("<image","<image /><image")+shape+"</svg>"):
        with pytest.raises(ValueError):split_source(bad)

def test_production_and_local_roots_unchanged_by_probe():
    files=("web/static/public-route.js","web/static/browser-fallback.js",
           "local_worker/frontend/local-route.js")
    for name in files:
        source=(ROOT/name).read_text(encoding="utf-8")
        assert "verify_public_r4_cross_engine" not in source
        assert "verify_public_r4_component_split" not in source
        assert "public_r4_resvg_full_scene" not in source
    a=(ROOT/"scripts/verify_public_r4_cross_engine.py").read_text(encoding="utf-8")
    assert '"productionPromoted":False' in a
    assert '"resvgLicenseReleaseApproved":False' in a
    assert '"protectedArmTieStaffVisualApproved":False' in a
    assert '"releaseGatePass"]=False' in a
