from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_public_only_svgpath_route_is_opt_in():
    html = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    route = (ROOT / "web/static/public-route.js").read_text(encoding="utf-8")
    engine = (ROOT / "web/static/browser-fallback.js").read_text(encoding="utf-8")
    local_html = (ROOT / "local_worker/frontend/index.html").read_text(encoding="utf-8")
    local_route = (ROOT / "local_worker/frontend/local-route.js").read_text(encoding="utf-8")
    a = 'static/vendor/svg-path-commander/index.min.js'
    b = 'static/public-svgpath-research.js'
    assert a in html and b in html
    assert html.index(a) < html.index(b) < html.index('static/browser-fallback.js')
    assert 'get("publicSvgPathResearch") === "1"' in route
    assert "publicSvgPathResearch: svgPathResearch" in route
    assert "config.publicSvgPathResearch === true" in engine
    assert "X-Minimalizer-Public-SVGPath-Audit" in engine
    assert "svg-path-commander" not in local_html + local_route
    assert "publicSvgPathResearch" not in local_route


def test_vendor_source_and_attribution():
    assert (ROOT / "web/static/vendor/svg-path-commander/index.min.js").is_file()
    license_file = ROOT / "web/static/vendor/svg-path-commander/LICENSE"
    assert "MIT License" in license_file.read_text(encoding="utf-8")
    assert (ROOT / "web/static/vendor/svg-path-commander/THIRD_PARTY.md").is_file()


def test_svgpath_js_runs_against_real_browser_vendor():
    if shutil.which("node") is None:
        pytest.skip("Node.js is unavailable")
    result = subprocess.run(
        ["node", str(ROOT / "tests/js/test_public_svgpath_research.cjs")],
        check=True, capture_output=True, text=True, cwd=ROOT,
    )
    assert "7 scenarios PASS" in result.stdout


def test_public_static_build_copies_vendor(tmp_path, monkeypatch):
    import scripts.build_shin_static as builder
    monkeypatch.setattr(builder, "DESTINATION", tmp_path / "public")
    out = builder.build()
    assert (out / "static/vendor/svg-path-commander/index.min.js").is_file()
    assert (out / "static/vendor/svg-path-commander/LICENSE").is_file()
    assert (out / "static/public-svgpath-research.js").is_file()
    assert not (out / "static/local-route.js").exists()
