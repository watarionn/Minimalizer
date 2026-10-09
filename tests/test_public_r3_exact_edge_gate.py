"""R3 non-generative exact-collinear gate and Public/Local separation."""
from __future__ import annotations
import ast
import subprocess
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=ROOT/"scripts/public_r3_exact_collinear.cjs"
VERIFY=ROOT/"scripts/verify_public_r3_chrome.py"

def test_r3_scripts_are_valid_and_research_only():
    ast.parse(VERIFY.read_text(encoding="utf-8"))
    js=CANDIDATE.read_text(encoding="utf-8")
    code=VERIFY.read_text(encoding="utf-8")
    assert "edgeMultiset" in js and "sameMultiset(edges,after)" in js
    assert "sameMask(sourceMask,proposedMask)" in js
    assert "sourceSemanticOwnershipCertified" in code
    assert '"productionPromoted":False' in code
    assert '"stage8OriginalVertexBudgetPass":False' in code
    assert "340" in code or "SIZE" in code
    assert "render_2x" in code

def test_r3_new_scripts_not_in_public_or_local_production_paths():
    for path in ("web/static/public-route.js",
                 "web/static/browser-fallback.js",
                 "local_worker/frontend/local-route.js"):
        content=(ROOT/path).read_text(encoding="utf-8")
        assert "public_r3_exact_collinear" not in content
        assert "verify_public_r3_chrome" not in content

def test_genuine_js_vendor_and_exact_lattice_synthetic_fixtures():
    p=subprocess.run(["node",str(ROOT/"tests/js/test_public_r3_exact_collinear.cjs")],
                     cwd=ROOT,capture_output=True,text=True,timeout=45)
    assert p.returncode==0,p.stderr
    assert "5 safety scenarios PASS" in p.stdout

def test_overwrite_and_missing_manifest_always_fail_closed(tmp_path):
    import sys
    import importlib.util
    sys.path.insert(0,str(ROOT/"scripts"))
    spec=importlib.util.spec_from_file_location("r3",VERIFY)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    existing=tmp_path/"exists"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        m.run(tmp_path,tmp_path,existing)
    with pytest.raises(FileNotFoundError):
        m.run(tmp_path,tmp_path,tmp_path/"new")
    assert not (tmp_path/"new").exists()
