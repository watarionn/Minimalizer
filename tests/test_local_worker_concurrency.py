import threading
import time
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

import local_worker.app as worker
from test_local_worker import _fake_export


def test_second_real_request_gets_429_while_first_cpu_job_runs(monkeypatch):
    started = threading.Event()

    def slow_run(*args, **kwargs):
        started.set()
        time.sleep(0.35)
        return _fake_export(), type("Selection", (), {"score": 1.0})()

    monkeypatch.setattr(worker, "_run_high_quality", slow_run)

    def request():
        with TestClient(worker.app) as client:
            return client.post(
                "/api/v2/minimalize",
                headers={"Origin": "http://127.0.0.1:28764"},
                files={"file": ("sample.png", b"not-empty", "image/png")},
                data={"preset": "minimal", "include_facets": "true"},
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(request)
        assert started.wait(timeout=2)
        second = pool.submit(request)
        second_response = second.result(timeout=5)
        first_response = first.result(timeout=5)

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert second_response.headers["retry-after"] == "2"
