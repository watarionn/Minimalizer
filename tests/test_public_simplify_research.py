from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_public_only_research_assets_and_opt_in():
    public = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    route = (ROOT / "web/static/public-route.js").read_text(encoding="utf-8")
    core = (ROOT / "web/static/browser-fallback.js").read_text(encoding="utf-8")
    local = (ROOT / "local_worker/frontend/index.html").read_text(encoding="utf-8")
    local_route = (ROOT / "local_worker/frontend/local-route.js").read_text(encoding="utf-8")
    assert "static/vendor/simplify-js/simplify.js" in public
    assert "static/public-simplify-research.js" in public
    assert public.index("static/vendor/simplify-js/simplify.js") < public.index("static/public-simplify-research.js")
    assert public.index("static/public-simplify-research.js") < public.index("static/browser-fallback.js")
    assert "publicSimplifyResearch" in route
    assert 'get("publicSimplifyResearch") === "1"' in route
    assert "config.publicSimplifyResearch === true" in core
    assert "X-Minimalizer-Public-Simplify-Audit" in core
    assert "simplify-js" not in local + local_route
    assert "publicSimplifyResearch" not in local_route


def test_pinned_bsd_license_exists():
    assert (ROOT / "web/static/vendor/simplify-js/LICENSE").is_file()
    source = (ROOT / "web/static/vendor/simplify-js/simplify.js").read_text(encoding="utf-8")
    assert "Vladimir Agafonkin" in source
    assert "module.exports = simplify" in source


def test_simplify_js_unit_regression():
    if shutil.which("node") is None:
        pytest.skip("Node.js is unavailable")
    result = subprocess.run(
        ["node", str(ROOT / "tests/js/test_public_simplify_research.cjs")],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert "6 scenarios PASS" in result.stdout


def test_public_builder_includes_research_but_not_local_route(tmp_path, monkeypatch):
    import scripts.build_shin_static as builder
    monkeypatch.setattr(builder, "DESTINATION", tmp_path / "static-public")
    folder = builder.build()
    assert (folder / "static/vendor/simplify-js/simplify.js").is_file()
    assert (folder / "static/vendor/simplify-js/LICENSE").is_file()
    assert (folder / "static/public-simplify-research.js").is_file()
    assert not (folder / "static/local-route.js").exists()
