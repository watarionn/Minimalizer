"""R67 production preview is opt-in and cannot mutate normal conversion."""
from pathlib import Path
import re
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/"web/static/public-r67-review-20261010.html"

class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images=[]
        self.links=[]
        self.buttons=[]
        self.canvases=[]
    def handle_starttag(self,tag,attrs):
        props=dict(attrs)
        if tag=="img":self.images.append(props)
        if tag=="a":self.links.append(props)
        if tag=="button":self.buttons.append(props)
        if tag=="canvas":self.canvases.append(props)

def test_opt_in_page_has_exactly_six_r67_derived_images():
    text=HTML.read_text(encoding="utf8")
    doc=Images();doc.feed(text)
    assert len(doc.images)==6
    expected={f"public-r67-review-20261010/{case}-{mode}.png"
        for case in ("gc001","raden") for mode in ("before","after","diff")}
    assert {x["src"] for x in doc.images}==expected
    assert len(doc.canvases)==4
    assert len(doc.buttons)==4

def test_normal_browser_converter_not_modified_or_injected():
    text=HTML.read_text(encoding="utf8")
    assert "通常の画像変換処理は変更していません" in text
    assert "Stage8" in text and "研究候補" in text
    assert "R67〜R73" in text
    assert 'action="' not in text and "<form" not in text
    assert "type=\"file\"" not in text
    for dangerous in ("local_worker", "127.0.0.1", "localhost", "fetch(",
                      "XMLHttpRequest", "FormData(", "postMessage(", "serviceWorker.register"):
        assert dangerous not in text

def test_source_photo_pixels_are_not_a_page_asset():
    html=HTML.read_text(encoding="utf8")
    assert ".source.png" not in html
    assert "original_inputs" not in html
    assert "phase8_adaptive_source_contour_research.json" not in html
    assert "PRIVATE_" not in html
    assert "元写真ではなく" in html

def test_review_has_functional_delta_zoom_and_navigation():
    text=HTML.read_text(encoding="utf8")
    assert "getImageData(" in text
    assert "imageSmoothingEnabled=false" in text
    assert 'data-move="-1"' in text and 'data-move="1"' in text
    assert 'data-stage="before"' in text and 'data-stage="after"' in text

def test_original_product_entry_and_local_worker_stay_separate():
    doc=Images();doc.feed(HTML.read_text(encoding="utf8"))
    assert any(x.get("href")=="../" for x in doc.links)
    assert any("facet" in x.get("href","") for x in doc.links)
    assert (ROOT/"web/static/index.html").is_file()
    assert (ROOT/"web/static/public-route.js").is_file()
