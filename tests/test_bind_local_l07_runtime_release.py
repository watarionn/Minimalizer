import hashlib
import json
from pathlib import Path

import pytest

from tools.research.bind_local_l07_runtime_release import (
    HEALTH_SCHEMA,
    RUNTIME_SCHEMA,
    SCHEMA,
    L07RuntimeHold,
    audit_l07_runtime_release,
)
from tools.research.local_completion_release_gate import (
    EXPECTED_CANDIDATE_RECEIPT_SHA256,
    EXPECTED_PRODUCTION_WORKER_COMMIT,
)


def _write(path: Path, value: dict) -> str:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _runtime() -> dict:
    return {
        "schema": RUNTIME_SCHEMA,
        "status": "PASS",
        "production_worker_commit": EXPECTED_PRODUCTION_WORKER_COMMIT,
        "runtime_sw_audit_pass": True,
        "runtime_generation_bound": True,
        "generation_pinned": True,
        "rollback_available": True,
        "old_generation_retained_for_rollback": True,
        "api_and_images_not_cached": True,
        "generation": "minimalizer-local-20261117-2",
        "source_generation": "minimalizer-local-20261117-2",
    }


def _health() -> dict:
    return {
        "schema": HEALTH_SCHEMA,
        "status": "ready",
        "http_status": 200,
        "runtime_error": None,
        "zerobase2_authorized": True,
    }


def _case(tmp_path: Path):
    runtime_path = tmp_path / "runtime.json"
    health_path = tmp_path / "health.json"
    runtime_sha = _write(runtime_path, _runtime())
    health_sha = _write(health_path, _health())
    binding = {
        "schema": SCHEMA,
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "production_worker_commit": EXPECTED_PRODUCTION_WORKER_COMMIT,
        "owner_runtime_action_confirmed": True,
        "runtime_sha256": runtime_sha,
        "health_sha256": health_sha,
    }
    return runtime_path, health_path, binding


def test_current_runtime_binding_passes(tmp_path: Path):
    runtime_path, health_path, binding = _case(tmp_path)
    result = audit_l07_runtime_release(
        runtime=json.loads(runtime_path.read_text()),
        health=json.loads(health_path.read_text()),
        binding=binding,
        runtime_path=runtime_path,
        health_path=health_path,
    )
    assert result["status"] == "PASS"
    assert result["release_authorized"] is False


def test_current_hold_runtime_cannot_bind(tmp_path: Path):
    runtime_path, health_path, binding = _case(tmp_path)
    runtime = _runtime()
    runtime["runtime_sw_audit_pass"] = False
    with pytest.raises(L07RuntimeHold, match="RUNTIME_RUNTIME_SW_AUDIT_PASS_REQUIRED"):
        audit_l07_runtime_release(
            runtime=runtime,
            health=json.loads(health_path.read_text()),
            binding=binding,
            runtime_path=runtime_path,
            health_path=health_path,
        )


def test_worker_mismatch_is_rejected(tmp_path: Path):
    runtime_path, health_path, binding = _case(tmp_path)
    binding["production_worker_commit"] = "0" * 40
    with pytest.raises(L07RuntimeHold, match="BINDING_WORKER_COMMIT_MISMATCH"):
        audit_l07_runtime_release(
            runtime=json.loads(runtime_path.read_text()),
            health=json.loads(health_path.read_text()),
            binding=binding,
            runtime_path=runtime_path,
            health_path=health_path,
        )


def test_health_error_is_rejected(tmp_path: Path):
    runtime_path, health_path, binding = _case(tmp_path)
    health = _health()
    health["runtime_error"] = "worker unavailable"
    with pytest.raises(L07RuntimeHold, match="HEALTH_RUNTIME_ERROR"):
        audit_l07_runtime_release(
            runtime=json.loads(runtime_path.read_text()),
            health=health,
            binding=binding,
            runtime_path=runtime_path,
            health_path=health_path,
        )
