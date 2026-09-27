from io import BytesIO
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from web.app import app

client = TestClient(app)

def transparent_subject_png():
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 8, 47, 55), fill=(50, 100, 180, 255))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()

def test_zerobase_endpoint_uses_source_alpha_and_returns_png():
    response = client.post(
        "/api/zerobase/minimalize",
        files={"file": ("subject.png", transparent_subject_png(), "image/png")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert response.headers["x-minimalizer-route"] == "zerobase"
    assert response.headers["x-minimalizer-foreground-evidence"] == "source-alpha"
    assert int(response.headers["x-minimalizer-shape-count"]) > 0
    assert response.content.startswith(b"\x89PNG")

def test_browser_standard_route_targets_zerobase():
    javascript = client.get("/static/app.js").text
    assert 'fetch("/api/zerobase/minimalize"' in javascript
    standard = javascript.split("async function requestStandardV2()", 1)[1].split("async function responseError", 1)[0]
    assert 'fetchLocalWorker("/api/v2/minimalize"' not in standard
