from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_public_only_opt_in_and_local_isolation():
    route = (ROOT / "web/static/public-route.js").read_text(encoding="utf-8")
    core = (ROOT / "web/static/browser-fallback.js").read_text(encoding="utf-8")
    local = (ROOT / "local_worker/frontend/local-route.js").read_text(encoding="utf-8")
    public = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    assert 'get("publicClipper2Research") === "1"' in route
    assert 'import(new URL("static/public-clipper2-research.mjs", document.baseURI).href)' in route
    assert "publicClipper2Research: clipper2Research" in route
    assert "publicClipper2Observer: clipper2Observer" in route
    assert "config.publicClipper2Research === true" in core
    assert "root.MinimalizerOpenCvRaster" in core
    assert "X-Minimalizer-Public-Clipper2-Audit" in core
    assert "publicClipper2Audit," in core
    assert "publicClipper2Research" not in local
    assert "clipper2" not in public  # default mode lazy: no page <script> import


def test_real_vendor_license_and_provenance():
    vendor = ROOT / "web/static/vendor/clipper2-wasm"
    assert (vendor / "clipper2z.wasm").stat().st_size > 200000
    assert (vendor / "clipper2z.mjs").stat().st_size > 50000
    assert "Boost Software License" in (vendor / "LICENSE").read_text(encoding="utf-8")
    assert "clipper2-wasm@0.4.0" in (vendor / "THIRD_PARTY.md").read_text(encoding="utf-8")


def test_official_wasm_and_source_mask_gates_run():
    if shutil.which("node") is None:
        pytest.skip("Node not installed")
    p = subprocess.run(["node", "tests/js/test_public_clipper2_research.mjs"],
                       cwd=ROOT, check=True, capture_output=True, text=True)
    assert "9 scenarios PASS" in p.stdout


def test_public_builder_includes_wasm_excludes_local(tmp_path, monkeypatch):
    import scripts.build_shin_static as builder
    monkeypatch.setattr(builder, "DESTINATION", tmp_path / "public")
    out = builder.build()
    assert (out / "static/vendor/clipper2-wasm/clipper2z.wasm").is_file()
    assert (out / "static/public-clipper2-research.mjs").is_file()
    assert not (out / "static/local-route.js").exists()
    assert "AddType application/wasm .wasm" in (
        out / "static/.htaccess").read_text(encoding="utf-8")
