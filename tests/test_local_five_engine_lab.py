from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "local_worker" / "frontend"


def test_five_engine_lab_is_private_local_only():
    local = (LOCAL / "index.html").read_text(encoding="utf-8")
    public = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
    html = (LOCAL / "five-engine-lab.html").read_text(encoding="utf-8")
    assert 'href="/local-static/five-engine-lab.html"' in local
    assert "five-engine-lab" not in public
    assert "public-route.js" not in html
    assert 'href="/manifest.webmanifest"' in html
    assert 'href="/"' in html
    assert "/local-static/five-engine-lab.mjs" in html
    assert "/local-static/vendor/imagetracer_v1.2.6.js" in html


def test_five_engine_lab_is_opt_in_and_does_not_write_to_production():
    js = (LOCAL / "five-engine-lab.mjs").read_text(encoding="utf-8")
    html = (LOCAL / "five-engine-lab.html").read_text(encoding="utf-8")
    assert 'IDS = ["vtracer", "imagetracer", "primitive", "geometrize", "primeval"]' in js
    assert 'LOCAL_ENGINES = ["vtracer", "imagetracer"]' in js
    assert 'import("../static/vendor/vtracer-wasm/vtracer.mjs")' in js
    assert 'window.ImageTracer.imagedataToSVG' in js
    assert 'new DOMParser().parseFromString' in js
    assert "crypto.subtle.digest" in js
    assert "validatedSvg(raw)" in js
    assert "research-only-not-golden" in js
    assert 'fetch("/api/' not in js
    assert "MINIMALIZER_LOCAL_OWNER_LOGIN" not in js
    assert "source pixel" not in html.lower()  # does not claim semantic source authority
    assert "https://cdn." not in js + html
    assert "<script src=\"https://" not in html


def test_pinned_imagetracer_license_and_no_public_asset():
    vendor = (LOCAL / "vendor" / "imagetracer_v1.2.6.js").read_text(encoding="utf-8")
    assert "imagetracer.js version 1.2.6" in vendor
    assert "The Unlicense / PUBLIC DOMAIN" in vendor
    assert "imagedataToSVG" in vendor
    assert not (ROOT / "web" / "static" / "vendor" / "imagetracer_v1.2.6.js").exists()


def test_vtracer_demo_controls_are_local_only_and_match_pinned_wasm():
    local = (LOCAL / "five-engine-lab.html").read_text(encoding="utf-8")
    script = (LOCAL / "five-engine-lab.mjs").read_text(encoding="utf-8")
    settings = (LOCAL / "vtracer-demo-options.mjs").read_text(encoding="utf-8")
    public = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    for name in (
        "color-mode", "hierarchical", "mode", "filter-speckle",
        "color-precision", "gradient-step", "corner-threshold",
        "segment-length", "splice-threshold", "path-precision"
    ):
        assert f'id="vtracer-{name}"' in local
    assert 'id="vtracer-auto-update"' in local
    assert 'id="vtracer-reset"' in local
    assert 'readVTracerControls()' in script
    assert 'runVTracer(settings)' in script
    assert 'settings:value.settings' in script
    assert 'maxIterations: 10' in settings
    assert "vtracer-demo-options.mjs" not in public
    assert 'vtracer-demo-options.mjs' in script
