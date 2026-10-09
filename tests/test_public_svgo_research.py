from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_public_svgo_optin_and_local_isolation():
    route = (ROOT / "web/static/public-route.js").read_text(encoding="utf-8")
    engine = (ROOT / "web/static/browser-fallback.js").read_text(encoding="utf-8")
    html = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    local_route = (ROOT / "local_worker/frontend/local-route.js").read_text(encoding="utf-8")
    assert 'get("publicSvgoResearch") === "1"' in route
    assert 'import(new URL("static/public-svgo-research.mjs", document.baseURI).href)' in route
    assert "publicSvgoResearch: svgoResearch" in route
    assert "config.publicSvgoResearch === true" in engine
    assert "await observer.auditShapes" in engine
    assert "X-Minimalizer-Public-SVGO-Exact" in engine
    assert "publicSvgoAudit," in engine
    assert "publicSvgoResearch" not in local_route
    assert "svgo.browser" not in html  # no default-mode dependency


def test_self_hosted_real_svgo_with_license():
    source = ROOT / "web/static/vendor/svgo"
    assert (source / "svgo.browser.js").stat().st_size > 100000
    assert "MIT License" in (source / "LICENSE").read_text(encoding="utf-8")
    assert "SVGO" in (source / "THIRD_PARTY.md").read_text(encoding="utf-8")


def test_real_svgo_module_node_scenarios():
    if not shutil.which("node"):
        pytest.skip("Node.js unavailable")
    result = subprocess.run(["node", "tests/js/test_public_svgo_research.mjs"],
                            check=True, capture_output=True, text=True, cwd=ROOT)
    assert "8 scenarios PASS" in result.stdout


def test_public_static_package_contains_only_public_svgo(tmp_path, monkeypatch):
    import scripts.build_shin_static as builder
    monkeypatch.setattr(builder, "DESTINATION", tmp_path / "public")
    out = builder.build()
    assert (out / "static/vendor/svgo/svgo.browser.js").is_file()
    assert (out / "static/public-svgo-research.mjs").is_file()
    assert not (out / "static/local-route.js").exists()
    assert not (ROOT / "local_worker/frontend/vendor/svgo").exists()
    assert "AddType application/javascript .mjs" in (
        out / "static/.htaccess").read_text(encoding="utf-8")
