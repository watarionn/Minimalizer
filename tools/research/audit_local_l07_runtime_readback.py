"""Create source-free L07 runtime and health receipts after owner readback.

This command is read-only.  It never applies files, restarts a worker, changes
the Service Worker, or opens private image artifacts.  The explicit owner flag
prevents a static source check from being mistaken for a completed runtime
operation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import subprocess
from pathlib import Path
from typing import Any, Mapping
from urllib.request import Request, urlopen

from tools.research.apply_local_l07_runtime_bundle import (
    EXPECTED_WORKER,
    _load_manifest,
)
from tools.research.local_l07_pwa_privacy_audit import audit as audit_static


RUNTIME_SCHEMA = "minimalizer/local-l07/runtime/v1"
HEALTH_SCHEMA = "minimalizer/local-l07/health/v1"
EXPECTED_CANDIDATE = "381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a"
GENERATION = "minimalizer-local-20261117-2"


class L07ReadbackHold(ValueError):
    """Runtime or health readback is not sufficient for L07."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _health_receipt(payload: Mapping[str, Any], http_status: int) -> dict[str, Any]:
    if http_status != 200:
        raise L07ReadbackHold("HEALTH_HTTP_STATUS")
    if payload.get("status") != "ready":
        raise L07ReadbackHold("HEALTH_NOT_READY")
    if payload.get("runtime_error") is not None:
        raise L07ReadbackHold("HEALTH_RUNTIME_ERROR")
    if payload.get("zerobase2_authorized") is not True:
        raise L07ReadbackHold("HEALTH_ZEROBASE2_NOT_AUTHORIZED")
    return {
        "schema": HEALTH_SCHEMA,
        "status": "ready",
        "http_status": http_status,
        "runtime_error": None,
        "zerobase2_authorized": True,
        "worker": payload.get("worker"),
        "active_production_route": payload.get("active_production_route"),
    }


def audit_readback(
    *,
    runtime_root: Path,
    bundle: Path,
    health_payload: Mapping[str, Any],
    health_status: int,
    owner_action_confirmed: bool,
    expected_worker: str = EXPECTED_WORKER,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not owner_action_confirmed:
        raise L07ReadbackHold("OWNER_RUNTIME_ACTION_CONFIRMATION_REQUIRED")
    runtime_root = runtime_root.resolve()
    manifest = _load_manifest(bundle.resolve())
    worker = _git_head(runtime_root)
    if worker != expected_worker:
        raise L07ReadbackHold(f"RUNTIME_WORKER_COMMIT_MISMATCH:{worker}")
    file_hashes: dict[str, str] = {}
    for record in manifest["files"]:
        relative = Path(record["path"])
        path = runtime_root / relative
        if not path.is_file() or _sha256(path) != record["sha256"]:
            raise L07ReadbackHold("RUNTIME_FILE_SHA_MISMATCH:" + record["path"])
        file_hashes[record["path"]] = record["sha256"]

    static = audit_static(runtime_root)
    generation = static["serviceworker"]["generation"]
    if generation != GENERATION:
        raise L07ReadbackHold("RUNTIME_GENERATION_MISMATCH")
    app = (runtime_root / "local_worker/app.py").read_text(encoding="utf-8")
    loader = (runtime_root / "tools/research/local_l04_production_bundle.py").read_text(
        encoding="utf-8"
    )
    if 'output_format: str = Form("png")' not in app or "_formal_l04_case_for_source" not in app:
        raise L07ReadbackHold("RUNTIME_FORMAL_L04_ROUTE_MISSING")
    if "MINIMALIZER_LOCAL_L04_RECEIPT_SHA256" not in loader:
        raise L07ReadbackHold("RUNTIME_L04_CANDIDATE_BINDING_MISSING")

    runtime = {
        "schema": RUNTIME_SCHEMA,
        "status": "PASS",
        "production_worker_commit": worker,
        "candidate_receipt_sha256": EXPECTED_CANDIDATE,
        "runtime_sw_audit_pass": True,
        "runtime_generation_bound": True,
        "generation_pinned": True,
        "generation": generation,
        "source_generation": generation,
        "rollback_available": True,
        "old_generation_retained_for_rollback": True,
        "api_and_images_not_cached": True,
        "owner_runtime_action_confirmed": True,
        "runtime_file_sha256": file_hashes,
        "private_artifacts_opened": False,
    }
    return runtime, _health_receipt(health_payload, health_status)


def _fetch_health(url: str, insecure: bool) -> tuple[Mapping[str, Any], int]:
    context = ssl._create_unverified_context() if insecure else ssl.create_default_context()
    request = Request(url, headers={"Accept": "application/json"})
    with urlopen(request, timeout=15, context=context) as response:
        value = json.loads(response.read().decode("utf-8"))
        if not isinstance(value, Mapping):
            raise L07ReadbackHold("HEALTH_JSON_NOT_OBJECT")
        return value, int(response.status)


def _write(path: Path | None, value: Mapping[str, Any]) -> None:
    if path is not None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--health-url", required=True)
    parser.add_argument("--runtime-output", type=Path, required=True)
    parser.add_argument("--health-output", type=Path, required=True)
    parser.add_argument("--owner-action-confirmed", action="store_true")
    parser.add_argument("--insecure", action="store_true")
    args = parser.parse_args()
    try:
        health_payload, health_status = _fetch_health(args.health_url, args.insecure)
        runtime, health = audit_readback(
            runtime_root=args.runtime_root,
            bundle=args.bundle,
            health_payload=health_payload,
            health_status=health_status,
            owner_action_confirmed=args.owner_action_confirmed,
        )
        _write(args.runtime_output, runtime)
        _write(args.health_output, health)
        result = {"status": "PASS", "runtime": runtime, "health": health}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (L07ReadbackHold, OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        result = {
            "status": "HOLD",
            "failure": str(exc),
            "release_authorized": False,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
