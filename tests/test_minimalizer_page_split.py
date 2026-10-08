from pathlib import Path
from scripts.build_shin_static import build

ROOT = Path(__file__).resolve().parents[1]

def test_public_page_has_browser_only_route():
    page = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    route = (ROOT / "web/static/public-route.js").read_text(encoding="utf-8")
    core = (ROOT / "web/static/app.js").read_text(encoding="utf-8")
    assert "public-route.js" in page and "local-route.js" not in page
    assert "127.0.0.1" not in route + core
    assert "Tailscale" not in route + core
    assert "probeLocalWorker" not in route + core
    assert "/api/zerobase2/" not in route + core
    assert "MinimalizerBrowserFallback" in route

def test_public_bundle_excludes_private_frontend(tmp_path, monkeypatch):
    import scripts.build_shin_static as builder
    monkeypatch.setattr(builder, "DESTINATION", tmp_path / "public")
    path = build()
    assert (path / "index.html").is_file()
    assert (path / "static/public-route.js").is_file()
    assert not (path / "static/local-route.js").exists()
    assert not (path / "manifest.webmanifest").exists()

def test_local_page_has_local_only_route():
    root = ROOT / "local_worker/frontend"
    html = (root / "index.html").read_text(encoding="utf-8")
    route = (root / "local-route.js").read_text(encoding="utf-8")
    assert 'href="/manifest.webmanifest"' in html
    assert "/local-static/local-route.js" in html
    assert "/static/app.js" in html
    assert "public-route.js" not in html
    assert "browser-fallback.js" not in html
    assert 'fetch("/api/zerobase2/minimalize"' in route
    assert 'fetch("/api/v2/minimalize"' in route
    assert 'fetch("/health"' in route
    assert "MinimalizerBrowserFallback" not in route
