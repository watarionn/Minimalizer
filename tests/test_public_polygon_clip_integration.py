from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_public_loads_pinned_browser_library_but_local_does_not():
    public = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    local = (ROOT / "local_worker/frontend/index.html").read_text(encoding="utf-8")
    vendor = "static/vendor/polygon-clipping/polygon-clipping.umd.min.js"
    adapter = "static/public-polygon-geometry.js"
    assert vendor in public and adapter in public
    assert public.index(vendor) < public.index(adapter) < public.index("static/browser-fallback.js")
    assert vendor not in local and adapter not in local
    assert (ROOT / "web/static/vendor/polygon-clipping/LICENSE.md").is_file()
    assert (ROOT / "web/static/vendor/polygon-clipping/polygon-clipping.umd.min.js").is_file()


def test_public_only_opt_in_does_not_change_local_route():
    public_route = (ROOT / "web/static/public-route.js").read_text(encoding="utf-8")
    local_route = (ROOT / "local_worker/frontend/local-route.js").read_text(encoding="utf-8")
    fallback = (ROOT / "web/static/browser-fallback.js").read_text(encoding="utf-8")
    assert "publicPolygonDiagnostics: true" in public_route
    assert "publicPolygonDiagnostics" not in local_route
    assert "config.publicPolygonDiagnostics === true" in fallback
    assert "X-Minimalizer-Public-Polygon-Audit" in fallback


def test_browser_library_node_regression():
    if shutil.which("node") is None:
        pytest.skip("node not installed")
    subprocess.run(
        ["node", str(ROOT / "tests/js/test_public_polygon_clipping.cjs")],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_static_public_builder_copies_vendored_library(tmp_path, monkeypatch):
    import scripts.build_shin_static as builder
    monkeypatch.setattr(builder, "DESTINATION", tmp_path / "public")
    output = builder.build()
    assert (output / "static/vendor/polygon-clipping/polygon-clipping.umd.min.js").is_file()
    assert (output / "static/vendor/polygon-clipping/LICENSE.md").is_file()
    assert (output / "static/public-polygon-geometry.js").is_file()
    assert not (output / "static/local-route.js").exists()
