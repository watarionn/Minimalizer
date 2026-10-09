from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_public_only_earcut_and_explicit_opt_in():
    public = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    route = (ROOT / "web/static/public-route.js").read_text(encoding="utf-8")
    fallback = (ROOT / "web/static/browser-fallback.js").read_text(encoding="utf-8")
    local = (ROOT / "local_worker/frontend/index.html").read_text(encoding="utf-8")
    local_route = (ROOT / "local_worker/frontend/local-route.js").read_text(encoding="utf-8")
    assert "static/vendor/earcut/earcut.min.js" in public
    assert "static/public-earcut-research.js" in public
    assert public.index("static/vendor/earcut/earcut.min.js") < public.index("static/public-earcut-research.js")
    assert public.index("static/public-earcut-research.js") < public.index("static/browser-fallback.js")
    assert 'get("publicEarcutResearch") === "1"' in route
    assert "publicEarcutResearch: earcutResearch" in route
    assert "config.publicEarcutResearch === true" in fallback
    assert "X-Minimalizer-Public-Earcut-Exact-Shapes" in fallback
    assert "earcut" not in local.lower() + local_route.lower()
    assert "publicEarcutResearch" not in local_route


def test_isc_vendor_notice_and_no_external_cdn():
    assert (ROOT / "web/static/vendor/earcut/LICENSE").is_file()
    assert (ROOT / "web/static/vendor/earcut/earcut.min.js").is_file()
    assert (ROOT / "web/static/vendor/earcut/THIRD_PARTY.md").is_file()
    assert (ROOT / "web/static/vendor/earcut/LICENSE").read_text(encoding="utf-8").startswith("ISC License")
    public = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    assert "cdn.jsdelivr.net/npm/earcut" not in public


def test_real_earcut_node_regression():
    if shutil.which("node") is None:
        pytest.skip("Node unavailable")
    p = subprocess.run(
        ["node", str(ROOT / "tests/js/test_public_earcut_research.cjs")],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert "8 scenarios PASS" in p.stdout


def test_public_static_builder_includes_earcut(tmp_path, monkeypatch):
    import scripts.build_shin_static as builder
    monkeypatch.setattr(builder, "DESTINATION", tmp_path / "public")
    output = builder.build()
    assert (output / "static/vendor/earcut/earcut.min.js").is_file()
    assert (output / "static/vendor/earcut/LICENSE").is_file()
    assert (output / "static/public-earcut-research.js").is_file()
    assert not (output / "static/local-route.js").exists()
