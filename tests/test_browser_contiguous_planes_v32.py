"""V32 SLIC source-plane research contracts. Synthetic sources, no model inference."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"tools/analyze_browser_contiguous_planes_v32.py"

def module():
    spec=importlib.util.spec_from_file_location("v32",SCRIPT)
    out=importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(out)
    return out

def fixture():
    h=w=80
    yy,xx=np.indices((h,w))
    source=np.empty((h,w,4),dtype=np.uint8)
    source[:,:,0]=(xx*3)%256
    source[:,:,1]=(yy*2)%256
    source[:,:,2]=((xx+yy)*2)%256
    source[:,:,3]=255
    base=np.empty_like(source)
    base[:,:,:3]=(64,64,64)
    base[:,:,3]=255
    eligible=(xx>=12)&(xx<68)&(yy>=12)&(yy<68)
    # Entirely nonopaque regions are protected from color replacement.
    source[:10,:,3]=0
    return source,base,eligible

def test_connected_planes_are_source_owned_bounded_and_deterministic():
    m=module()
    src,base,mask=fixture()
    out,a=m.reconstruct(src,base,mask,nseg=110,compact=2.0)
    repeated,b=m.reconstruct(src,base,mask,nseg=110,compact=2.0)
    assert a==b
    assert np.array_equal(out,repeated)
    changed=np.any(out!=base,axis=-1)
    assert changed.any() and not np.any(changed & ~mask)
    assert np.array_equal(out[:,:,3],base[:,:,3])
    assert a["changedOutsideGarment"]==a["alphaChanges"]==0
    assert a["acceptedRegions"]>0 and a["regions"]>=a["acceptedRegions"]
    src_colors={tuple(c) for c in src[:,:,:3][mask]}
    assert {tuple(c) for c in out[:,:,:3][changed]} <= src_colors
    assert m.measure(src,base,out,mask)<m.measure(src,base,base,mask)

def test_deny_all_when_no_source_gain():
    m=module()
    src,base,mask=fixture()
    baseline=src.copy()
    result,stat=m.reconstruct(src,baseline,mask,nseg=120,compact=3.0)
    assert np.array_equal(result,baseline)
    assert stat["changedPixels"]==0
    assert stat["changedOutsideGarment"]==0

def test_empty_garment_fails_closed():
    m=module()
    src,base,mask=fixture()
    result,stat=m.reconstruct(src,base,np.zeros_like(mask),nseg=100,compact=3.0)
    assert np.array_equal(result,base)
    assert stat["acceptedRegions"]==stat["changedPixels"]==0

def test_no_production_output_route_was_added():
    src=SCRIPT.read_text(encoding="utf-8")
    assert "source_color_set" in src
    assert 'productionAuthority":False' in src
    assert "changedOutsideGarment" in src
    app=(ROOT/"web/static/app.js").read_text(encoding="utf-8")
    html=(ROOT/"web/static/index.html").read_text(encoding="utf-8")
    assert "browser-contiguous-planes-v32" not in app
    assert "browser-contiguous-planes-v32" not in html


def test_reserved_signature_color_cannot_become_new_plane():
    m=module()
    src,base,mask=fixture()
    src[:,:,:3]=(149,211,27)
    result,stat=m.reconstruct(src,base,mask,nseg=95,compact=2.0,
        protected_colors=((149,211,27),))
    assert np.array_equal(result,base)
    assert stat["changedPixels"]==0

def test_offline_real_corpus_runner_contains_identity_guards():
    src=SCRIPT.read_text(encoding="utf-8")
    assert "PROTECTED_COLORS" in src
    assert "reserved[263:290,90:112]" in src
    assert "protectedColorMassExact" in src
    assert "sha(source_path)==item" in src
    assert "sha(mask_path)==item" in src
