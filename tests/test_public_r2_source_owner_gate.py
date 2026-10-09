"""Public-only R2 safety: group-level Chrome rollback, protected source XML, alpha."""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/verify_public_r2_chrome.py"

def module():
    sys.path.insert(0,str(ROOT/"scripts"))
    spec=importlib.util.spec_from_file_location("r2_gate",SCRIPT)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

HEAD='<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/png;base64,eA=="/>'
P1='<path fill="#ffaa00" fill-rule="evenodd" d="M2 2L4 2L4 4Z"/>'
P2='<path fill="#ffaa00" fill-rule="evenodd" d="M2 2L4 2Z"/>'
TAIL="</svg>"
ROW=[{"removedVertices":1}]
REFERENCE=bytes([10,20,30,255,30,40,50,255])

def test_unsafe_chrome_candidate_is_rolled_back_without_mutating_source():
    g=module()
    base=HEAD+P1+TAIL
    candidate=HEAD+P2+TAIL
    def native(svg):
        return REFERENCE if P1 in svg else bytes([10,20,30,254,30,40,50,255])
    result,accepted,rejected=g.rollback_checked_candidates(
        base,candidate,ROW,REFERENCE,REFERENCE,native,native)
    assert result==base and not accepted and len(rejected)==1
    assert rejected[0]["nativeDifferentPixels"]==1
    assert rejected[0]["twoXDifferentPixels"]==1
    assert g.mismatched_pixels(REFERENCE,native(result))==0

def test_safe_candidate_requires_both_native_and_2x_oracles():
    g=module()
    base=HEAD+P1+TAIL
    candidate=HEAD+P2+TAIL
    pass_native=lambda svg:REFERENCE
    bad_2x=lambda svg: REFERENCE if P1 in svg else bytes([10,20,30,255,31,40,50,255])
    output,a,r=g.rollback_checked_candidates(
        base,candidate,ROW,REFERENCE,REFERENCE,pass_native,bad_2x)
    assert output==base and not a and len(r)==1
    output,a,r=g.rollback_checked_candidates(
        base,candidate,ROW,REFERENCE,REFERENCE,pass_native,pass_native)
    assert output==candidate and len(a)==1 and not r

def test_reject_unknown_changes_to_source_rgb_and_embedded_background():
    g=module()
    base=HEAD+P1+TAIL
    reference=lambda svg:REFERENCE
    for changed in (HEAD.replace("eA==","eB==")+P2+TAIL,
                    HEAD+P2.replace("#ffaa00","#ff0000")+TAIL,
                    HEAD+P2+TAIL.replace("</svg>","<rect/></svg>")):
        with pytest.raises(ValueError):
            g.rollback_checked_candidates(base,changed,ROW,REFERENCE,REFERENCE,
                                          reference,reference)

def test_no_public_or_local_production_imports():
    code=SCRIPT.read_text(encoding="utf-8")
    assert '"productionPromoted":False' in code
    assert '"semanticOwnerAuthorized":False' in code
    assert "chromeRolledBackGroups" in code
    for file in ("web/static/public-route.js",
                 "web/static/browser-fallback.js",
                 "local_worker/frontend/local-route.js"):
        assert "public_r2_owner_geometry" not in (ROOT/file).read_text(encoding="utf-8")
        assert "verify_public_r2_chrome" not in (ROOT/file).read_text(encoding="utf-8")
