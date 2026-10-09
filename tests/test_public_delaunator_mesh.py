from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_delaunator_public_only_routes_and_assets():
    public = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    public_route = (ROOT / "web/static/public-route.js").read_text(encoding="utf-8")
    browser_fallback = (ROOT / "web/static/browser-fallback.js").read_text(encoding="utf-8")
    local = (ROOT / "local_worker/frontend/index.html").read_text(encoding="utf-8")
    local_route = (ROOT / "local_worker/frontend/local-route.js").read_text(encoding="utf-8")
    assert "static/vendor/delaunator/delaunator.min.js" in public
    assert "static/public-mesh-research.js" in public
    assert public.index("static/vendor/delaunator/delaunator.min.js") < public.index("static/public-mesh-research.js")
    assert public.index("static/public-mesh-research.js") < public.index("static/browser-fallback.js")
    assert 'get("publicMeshResearch") === "1"' in public_route
    assert "publicMeshResearch: meshResearch" in public_route
    assert "config.publicMeshResearch === true" in browser_fallback
    assert "X-Minimalizer-Public-Mesh-Audit" in browser_fallback
    assert "delaunator" not in local + local_route
    assert "publicMeshResearch" not in local_route
    # Repair old literal slash-n separators instead of silently shipping invalid markup.
    assert r'\n  <script' not in public


def test_delaunator_isc_license_present():
    assert (ROOT / "web/static/vendor/delaunator/LICENSE").is_file()
    assert (ROOT / "web/static/vendor/delaunator/delaunator.min.js").is_file()


def test_delaunator_browser_adapter_node():
    if shutil.which("node") is None:
        pytest.skip("node missing")
    result = subprocess.run(
        ["node", str(ROOT / "tests/js/test_public_delaunator_mesh.cjs")],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert "7 scenarios PASS" in result.stdout


def test_delaunator_static_builder(tmp_path, monkeypatch):
    import scripts.build_shin_static as builder
    monkeypatch.setattr(builder, "DESTINATION", tmp_path / "public")
    output = builder.build()
    assert (output / "static/vendor/delaunator/delaunator.min.js").is_file()
    assert (output / "static/vendor/delaunator/LICENSE").is_file()
    assert (output / "static/public-mesh-research.js").is_file()
    assert not (output / "static/local-route.js").exists()
