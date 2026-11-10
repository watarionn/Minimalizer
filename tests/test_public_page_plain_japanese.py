from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_HTML = ROOT / "web" / "static" / "index.html"
PUBLIC_CSS = ROOT / "web" / "static" / "styles.css"
SHARED_APP = ROOT / "web" / "static" / "app.js"


def test_public_page_has_no_advertising_hero():
    html = PUBLIC_HTML.read_text(encoding="utf-8")
    for banned in (
        "画像を、必要なかたちだけに。",
        "IMAGE → MINIMAL GRAPHIC",
        "画像を選んで「ミニマル化」を押すだけ。",
        'class="hero"',
        'class="hero-copy"',
        "Minimalizer Public · Browser",
    ):
        assert banned not in html, f"Unwanted promotional text: {banned}"
    assert '<h1 class="public-page__title">画像簡略化ツール</h1>' in html
    assert '<body class="public-page">' in html
    assert 'href="static/styles.css?v=20261023-public-copy"' in html


def test_public_controls_and_browser_route_are_unchanged():
    html = PUBLIC_HTML.read_text(encoding="utf-8")
    app = SHARED_APP.read_text(encoding="utf-8")
    for marker in (
        'id="file-input"',
        'id="drop-zone"',
        'id="source-preview"',
        'id="result-preview"',
        'id="minimalize-button"',
        'id="engine-badge" hidden',
        'name="mode" value="color_strip"',
        'static/public-route.js?v=20261008-local-public',
        'static/app.js?v=20261008-local-public',
    ):
        assert marker in html, f"Required UI identifier lost: {marker}"
    assert 'elements.engineBadge.textContent = compute.label' in app
    assert 'id="engine-badge" hidden' in html


def test_public_mobile_css_is_isolated_from_local_ui():
    css = PUBLIC_CSS.read_text(encoding="utf-8")
    for selector in (
        ".public-page .page-shell",
        ".public-page__title",
        ".public-page .drop-zone",
        ".public-page .result-stage",
        ".public-page #source-preview",
    ):
        assert selector in css, f"Missing Public-only CSS: {selector}"
    assert '@media (max-width: 520px)' in css
    assert "min-height: 250px" in css
