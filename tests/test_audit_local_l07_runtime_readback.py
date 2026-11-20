import subprocess
from pathlib import Path
import shutil

import pytest

from tools.research.audit_local_l07_runtime_readback import audit_readback
from tools.research.prepare_local_l07_runtime_bundle import FILES, prepare


ROOT = Path(__file__).parents[1]


def _git_target(source: Path, target: Path) -> str:
    for relative in FILES:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, destination)
    subprocess.run(["git", "-C", str(target), "init", "-b", "main"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(target), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(target), "config", "user.name", "Minimalizer Test"], check=True)
    subprocess.run(["git", "-C", str(target), "add", "."], check=True)
    subprocess.run(["git", "-C", str(target), "commit", "-m", "fixture"], check=True, capture_output=True)
    return subprocess.run(
        ["git", "-C", str(target), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_readback_requires_explicit_owner_confirmation(tmp_path):
    bundle = tmp_path / "bundle"
    target = tmp_path / "target"
    prepare(ROOT, bundle)
    worker = _git_target(ROOT, target)
    with pytest.raises(ValueError, match="OWNER_RUNTIME_ACTION_CONFIRMATION_REQUIRED"):
        audit_readback(
            runtime_root=target,
            bundle=bundle,
            health_payload={"status": "ready", "runtime_error": None, "zerobase2_authorized": True},
            health_status=200,
            owner_action_confirmed=False,
            expected_worker=worker,
        )


def test_readback_binds_runtime_files_generation_and_health(tmp_path):
    bundle = tmp_path / "bundle"
    target = tmp_path / "target"
    prepare(ROOT, bundle)
    worker = _git_target(ROOT, target)
    runtime, health = audit_readback(
        runtime_root=target,
        bundle=bundle,
        health_payload={
            "status": "ready",
            "worker": "local-compute-v1",
            "active_production_route": "zerobase2",
            "runtime_error": None,
            "zerobase2_authorized": True,
        },
        health_status=200,
        owner_action_confirmed=True,
        expected_worker=worker,
    )

    assert runtime["status"] == "PASS"
    assert runtime["production_worker_commit"] == worker
    assert runtime["candidate_receipt_sha256"].startswith("381b0b5a")
    assert runtime["generation"] == "minimalizer-local-20261117-2"
    assert runtime["runtime_generation_bound"] is True
    assert len(runtime["runtime_file_sha256"]) == 5
    assert health == {
        "schema": "minimalizer/local-l07/health/v1",
        "status": "ready",
        "http_status": 200,
        "runtime_error": None,
        "zerobase2_authorized": True,
        "worker": "local-compute-v1",
        "active_production_route": "zerobase2",
    }


def test_readback_holds_on_unready_health(tmp_path):
    bundle = tmp_path / "bundle"
    target = tmp_path / "target"
    prepare(ROOT, bundle)
    worker = _git_target(ROOT, target)
    with pytest.raises(ValueError, match="HEALTH_NOT_READY"):
        audit_readback(
            runtime_root=target,
            bundle=bundle,
            health_payload={"status": "degraded", "runtime_error": None, "zerobase2_authorized": True},
            health_status=200,
            owner_action_confirmed=True,
            expected_worker=worker,
        )
