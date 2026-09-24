import os
from types import SimpleNamespace

os.environ["MINIMALIZER_LOCAL_WORKER_EAGER"] = "0"

from fastapi.testclient import TestClient

import local_worker.app as worker
from minimalize_engine.v2.export import V2PngExport, V2PngMetadata


def _fake_export():
    metadata = V2PngMetadata(
        contract_version="minimalizer-v2-png-v1",
        preset="minimal",
        source_width=64,
        source_height=48,
        width=64,
        height=48,
        visible_shape_count=12,
        palette_count=4,
        scene_facet_count=0,
        rendered_facet_count=0,
        include_facets=True,
        pixel_sha256="a" * 64,
        png_sha256="b" * 64,
    )
    return V2PngExport(
        content=b"fake-png",
        media_type="image/png",
        filename="minimalized-v2-minimal.png",
        metadata=metadata,
    )
def test_health_reports_cold_runtime_without_eager_warmup():
    worker._rembg_session = None
    worker._rtmlib_model = None
    worker._runtime_error = None
    with TestClient(worker.app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["worker"] == "local-compute-v1"
    assert response.json()["status"] == "cold"
    assert response.json()["ready"] is False


def test_local_worker_rejects_untrusted_browser_origin():
    with TestClient(worker.app) as client:
        response = client.post(
            "/api/v2/minimalize",
            headers={"Origin": "https://example.invalid"},
            files={"file": ("sample.png", b"x", "image/png")},
            data={"preset": "minimal", "include_facets": "true"},
        )
    assert response.status_code == 403


def test_local_worker_allows_production_origin_cors():
    origin = "https://minimalizer-web-production-a2bc.up.railway.app"
    with TestClient(worker.app) as client:
        response = client.get("/health", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_local_worker_returns_high_quality_headers(monkeypatch):
    def fake_run(*args, **kwargs):
        return _fake_export(), SimpleNamespace(score=1.0)

    monkeypatch.setattr(worker, "_run_high_quality", fake_run)
    with TestClient(worker.app) as client:
        response = client.post(
            "/api/v2/minimalize",
            headers={
                "Origin": "https://minimalizer-web-production-a2bc.up.railway.app"
            },
            files={"file": ("sample.png", b"not-empty", "image/png")},
            data={"preset": "minimal", "include_facets": "true"},
        )

    assert response.status_code == 200
    assert response.content == b"fake-png"
    assert response.headers["x-minimalizer-compute"] == "local-worker"
    assert response.headers["x-minimalizer-analysis"] == "rembg+rtmlib"
    assert response.headers["x-minimalizer-layered-person"] == "true"
    assert response.headers["x-minimalizer-rtmlib-selected"] == "true"
    assert response.headers["x-minimalizer-v2-png-sha256"] == "b" * 64
