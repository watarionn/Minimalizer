"""MinimalizerPublic R5 OFF-by-default shadow observer: production and Local isolation."""
from pathlib import Path
import ast
import shutil
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[1]

def test_r5_only_lazy_loaded_when_opt_in_and_never_replaces_response():
    route=(ROOT/"web/static/public-route.js").read_text(encoding="utf-8")
    html=(ROOT/"web/static/index.html").read_text(encoding="utf-8")
    assert 'get("publicR5Shadow") === "1"' in route
    assert 'import(new URL("static/public-r5-shadow-gate.mjs", document.baseURI).href)' in route
    assert "await observer.auditResponse(result.response)" in route
    assert 'return {response: result.response, compute: "browser"' in route
    assert "public-r5-shadow-gate.mjs" not in html
    assert "publicR5Shadow" not in (ROOT/"web/static/browser-fallback.js").read_text(encoding="utf-8")

def test_r5_never_touches_local_worker_or_local_minimalizer():
    local=(ROOT/"local_worker/frontend/local-route.js").read_text(encoding="utf-8")
    assert "publicR5Shadow" not in local
    for name in ("web/static/public-r5-shadow-gate.mjs",
                 "scripts/verify_public_r5_route_chrome.py"):
        assert not name.startswith("local_worker/")
    module=(ROOT/"web/static/public-r5-shadow-gate.mjs").read_text(encoding="utf-8")
    assert "response.clone()" in module
    assert "response.body" not in module
    assert "productionPromoted:false" in module

def test_genuine_browser_js_sha_and_failure_injection():
    if not shutil.which("node"):pytest.skip("node absent")
    p=subprocess.run(["node","tests/js/test_public_r5_shadow_gate.mjs"],
        cwd=ROOT,capture_output=True,text=True,timeout=60)
    assert p.returncode==0,p.stderr
    assert "6 scenarios PASS" in p.stdout

def test_static_bundle_contains_opt_in_module_and_no_local(tmp_path,monkeypatch):
    import scripts.build_shin_static as builder
    monkeypatch.setattr(builder,"DESTINATION",tmp_path/"isolated")
    output=builder.build()
    assert (output/"static/public-r5-shadow-gate.mjs").is_file()
    assert not (output/"static/local-route.js").exists()

def test_real_chrome_canary_no_overwrite_and_source_manifest_preflight(tmp_path):
    from importlib import util
    import sys
    script=ROOT/"scripts/verify_public_r5_route_chrome.py"
    ast.parse(script.read_text(encoding="utf-8"))
    sys.path.insert(0,str(ROOT/"scripts"))
    spec=util.spec_from_file_location("r5_gate",script)
    mod=util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    prior=tmp_path/"existing"
    prior.mkdir()
    with pytest.raises(FileExistsError):mod.execute(tmp_path,prior)
    with pytest.raises(FileNotFoundError):mod.execute(tmp_path,tmp_path/"missing")
    assert not (tmp_path/"missing").exists()
