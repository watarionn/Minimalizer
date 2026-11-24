from io import BytesIO
from pathlib import Path
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

def test_browser_standard_route_is_rolled_back_to_v2():
    javascript = client.get("/static/app.js").text
    assert "const compute = window.MinimalizerComputeRoute" in javascript
    assert "compute.minimalize(state.file, setStatus, outputFormat)" in javascript
    assert 'fetch("/api/zerobase/minimalize"' not in javascript

    root = Path(__file__).resolve().parents[1]
    local_route = (root / "local_worker" / "frontend" / "local-route.js").read_text(encoding="utf-8")
    assert 'fetch("/api/zerobase2/minimalize"' in local_route
    assert 'fetch("/api/v2/minimalize"' in local_route
    assert 'if (outputFormat === "svg")' in local_route
    assert "Browserへは切り替えません" in local_route


def test_local_service_worker_is_generation_pinned_and_keeps_rollback_cache():
    root = Path(__file__).resolve().parents[1]
    route = (root / "local_worker" / "frontend" / "local-route.js").read_text(encoding="utf-8")
    worker = (root / "local_worker" / "frontend" / "sw.js").read_text(encoding="utf-8")
    route_generation = route.split('const SERVICE_WORKER_GENERATION = "', 1)[1].split('"', 1)[0]
    worker_generation = worker.split('const GENERATION = "', 1)[1].split('"', 1)[0]
    assert route_generation == worker_generation
    assert "updateViaCache: \"none\"" in route
    assert "skipWaiting" not in worker
    assert "clients.claim" not in worker
    assert "caches.delete" not in worker
