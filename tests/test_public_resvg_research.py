from pathlib import Path
import shutil
import subprocess

import pytest

ROOT=Path(__file__).resolve().parents[1]

def test_opt_in_public_route_without_local_worker():
    route=(ROOT/"web/static/public-route.js").read_text(encoding="utf-8")
    engine=(ROOT/"web/static/browser-fallback.js").read_text(encoding="utf-8")
    local=(ROOT/"local_worker/frontend/local-route.js").read_text(encoding="utf-8")
    html=(ROOT/"web/static/index.html").read_text(encoding="utf-8")
    assert 'get("publicResvgResearch") === "1"' in route
    assert 'import(new URL("static/public-resvg-research.mjs", document.baseURI).href)' in route
    assert "publicResvgObserver: resvgObserver" in route
    assert "config.publicResvgResearch === true" in engine
    assert "X-Minimalizer-Public-RESVG-Different-Pixels" in engine
    assert "publicResvgAudit," in engine
    assert "publicResvgResearch" not in local
    assert "public-resvg-research" not in html  # lazy, not default path

def test_wasm_vendor_and_mpl_attribution():
    package=ROOT/"web/static/vendor/resvg-wasm"
    assert (package/"index_bg.wasm").stat().st_size>2000000
    assert (package/"index.mjs").is_file()
    assert "Mozilla Public License Version 2.0" in (
        package/"LICENSE").read_text(encoding="utf-8")
    assert "@resvg/resvg-wasm@2.6.2" in (
        package/"THIRD_PARTY.md").read_text(encoding="utf-8")

def test_real_wasm_in_node():
    if not shutil.which("node"):pytest.skip("Node unavailable")
    p=subprocess.run(["node","tests/js/test_public_resvg_research.mjs"],
                     cwd=ROOT,check=True,capture_output=True,text=True)
    assert "6 scenarios PASS" in p.stdout

def test_static_release_owns_wasm_and_does_not_pack_local(tmp_path,monkeypatch):
    import scripts.build_shin_static as builder
    monkeypatch.setattr(builder,"DESTINATION",tmp_path/"static-public")
    dest=builder.build()
    assert (dest/"static/vendor/resvg-wasm/index_bg.wasm").is_file()
    assert (dest/"static/public-resvg-research.mjs").is_file()
    assert not (dest/"static/local-route.js").exists()
    assert "AddType application/wasm .wasm" in (
        dest/"static/.htaccess").read_text(encoding="utf-8")
