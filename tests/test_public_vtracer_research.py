from pathlib import Path
import shutil
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[1]

def test_public_optin_and_no_local_route():
    route=(ROOT/"web/static/public-route.js").read_text(encoding="utf-8")
    core=(ROOT/"web/static/browser-fallback.js").read_text(encoding="utf-8")
    local=(ROOT/"local_worker/frontend/local-route.js").read_text(encoding="utf-8")
    public=(ROOT/"web/static/index.html").read_text(encoding="utf-8")
    assert 'get("publicVTracerResearch") === "1"' in route
    assert 'import(new URL("static/public-vtracer-research.mjs", document.baseURI).href)' in route
    assert "publicVTracerObserver: vtracerObserver" in route
    assert "config.publicVTracerResearch === true" in core
    assert "observer.auditCanvas(outputCanvas)" in core
    assert "X-Minimalizer-Public-VTracer-Audit" in core
    assert "publicVTracerAudit," in core
    assert "publicVTracerResearch" not in local
    assert "public-vtracer-research" not in public

def test_exact_official_wasm_package_licenses_and_provenance():
    p=ROOT/"web/static/vendor/vtracer-wasm"
    assert (p/"vtracer.wasm").stat().st_size>100000
    assert (p/"vtracer.mjs").stat().st_size>10000
    assert "MIT License" in (p/"LICENSE").read_text(encoding="utf-8")
    assert "Copyright (c) 2024" in (p/"LICENSE-VTRACER-UPSTREAM").read_text(encoding="utf-8")
    assert "vtracer-wasm@0.1.0" in (p/"THIRD_PARTY.md").read_text(encoding="utf-8")

def test_actual_vendor_tracing_with_node():
    if not shutil.which("node"):pytest.skip("Node unavailable")
    p=subprocess.run(["node","tests/js/test_public_vtracer_research.mjs"],
                     cwd=ROOT,check=True,capture_output=True,text=True)
    assert "8 scenarios PASS" in p.stdout

def test_static_release_contains_public_only_wasm(tmp_path,monkeypatch):
    import scripts.build_shin_static as builder
    monkeypatch.setattr(builder,"DESTINATION",tmp_path/"public")
    out=builder.build()
    assert (out/"static/vendor/vtracer-wasm/vtracer.wasm").is_file()
    assert (out/"static/public-vtracer-research.mjs").is_file()
    assert not (out/"static/local-route.js").exists()
    assert "AddType application/wasm .wasm" in (
        out/"static/.htaccess").read_text(encoding="utf-8")
