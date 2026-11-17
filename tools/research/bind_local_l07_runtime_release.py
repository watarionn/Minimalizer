"""Bind an owner-collected L07 runtime audit to the adopted release.

The adapter reads JSON receipts only.  It never changes the runtime, service
worker, cache, or deployment state.  Static source PASS and runtime PASS are
kept separate; the latter is accepted only when the runtime receipt itself
binds the expected worker commit and generation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.research.local_completion_release_gate import (  # noqa: E402
    EXPECTED_CANDIDATE_RECEIPT_SHA256,
    EXPECTED_PRODUCTION_WORKER_COMMIT,
)


SCHEMA = "minimalizer/local-l07/runtime-binding/v1"
RUNTIME_SCHEMA = "minimalizer/local-l07/runtime/v1"
HEALTH_SCHEMA = "minimalizer/local-l07/health/v1"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
GENERATION = re.compile(r"minimalizer-local-[0-9]{8}-[0-9]+\Z")


class L07RuntimeHold(ValueError):
    """The owner runtime evidence is not sufficient for L07."""


def _object(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise L07RuntimeHold(f"INVALID_OBJECT:{field}")
    return value


def _sha(value: object, field: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise L07RuntimeHold(f"INVALID_SHA:{field}")
    return value


def _load(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise L07RuntimeHold(f"READ_FAILED:{label}:{type(exc).__name__}") from exc
    return _object(value, label)


def _file_sha(path: Path, label: str) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, UnicodeError) as exc:
        raise L07RuntimeHold(f"READ_FAILED:{label}:{type(exc).__name__}") from exc


def _true(value: object, field: str) -> None:
    if value is not True:
        raise L07RuntimeHold(f"{field}_REQUIRED")


def _audit_runtime(runtime: Mapping[str, Any]) -> str:
    if runtime.get("schema") != RUNTIME_SCHEMA or runtime.get("status") != "PASS":
        raise L07RuntimeHold("RUNTIME_AUDIT_NOT_PASS")
    if runtime.get("production_worker_commit") != EXPECTED_PRODUCTION_WORKER_COMMIT:
        raise L07RuntimeHold("RUNTIME_WORKER_COMMIT_MISMATCH")
    for field in (
        "runtime_sw_audit_pass",
        "runtime_generation_bound",
        "generation_pinned",
        "rollback_available",
        "old_generation_retained_for_rollback",
        "api_and_images_not_cached",
    ):
        _true(runtime.get(field), f"RUNTIME_{field.upper()}")
    generation = runtime.get("generation")
    if not isinstance(generation, str) or GENERATION.fullmatch(generation) is None:
        raise L07RuntimeHold("RUNTIME_GENERATION_INVALID")
    if runtime.get("source_generation") != generation:
        raise L07RuntimeHold("RUNTIME_SOURCE_GENERATION_MISMATCH")
    return generation


def _audit_health(health: Mapping[str, Any]) -> None:
    if health.get("schema") != HEALTH_SCHEMA or health.get("status") != "ready":
        raise L07RuntimeHold("HEALTH_NOT_READY")
    if health.get("runtime_error") is not None:
        raise L07RuntimeHold("HEALTH_RUNTIME_ERROR")
    _true(health.get("zerobase2_authorized"), "HEALTH_ZEROBASE2_AUTHORIZED")
    if health.get("http_status") != 200:
        raise L07RuntimeHold("HEALTH_HTTP_STATUS")


def audit_l07_runtime_release(
    *, runtime: Mapping[str, Any], health: Mapping[str, Any], binding: Mapping[str, Any],
    runtime_path: Path, health_path: Path,
) -> dict[str, object]:
    """Return a candidate-bound L07 receipt, or raise a fail-closed hold."""
    if binding.get("schema") != SCHEMA:
        raise L07RuntimeHold("INVALID_BINDING_SCHEMA")
    if binding.get("candidate_receipt_sha256") != EXPECTED_CANDIDATE_RECEIPT_SHA256:
        raise L07RuntimeHold("CANDIDATE_RECEIPT_MISMATCH")
    if binding.get("production_worker_commit") != EXPECTED_PRODUCTION_WORKER_COMMIT:
        raise L07RuntimeHold("BINDING_WORKER_COMMIT_MISMATCH")
    if binding.get("owner_runtime_action_confirmed") is not True:
        raise L07RuntimeHold("OWNER_RUNTIME_ACTION_NOT_CONFIRMED")
    generation = _audit_runtime(runtime)
    _audit_health(health)
    if _file_sha(runtime_path, "runtime") != _sha(binding.get("runtime_sha256"), "runtime_sha256"):
        raise L07RuntimeHold("RUNTIME_SHA_MISMATCH")
    if _file_sha(health_path, "health") != _sha(binding.get("health_sha256"), "health_sha256"):
        raise L07RuntimeHold("HEALTH_SHA_MISMATCH")
    return {
        "schema": "minimalizer/local-l07/runtime-release/v1",
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "production_worker_commit": EXPECTED_PRODUCTION_WORKER_COMMIT,
        "generation_pinned": True,
        "rollback_available": True,
        "runtime_sw_audit_pass": True,
        "runtime_generation_bound": True,
        "generation": generation,
        "health_http_200": True,
        "runtime_error_null": True,
        "zerobase2_authorized": True,
        "owner_runtime_action_confirmed": True,
        "runtime_receipt_sha256": binding["runtime_sha256"],
        "health_receipt_sha256": binding["health_sha256"],
        "release_authorized": False,
        "private_artifacts_opened": False,
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Bind owner L07 runtime evidence")
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--health", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        runtime = _load(args.runtime, "runtime")
        health = _load(args.health, "health")
        binding = _load(args.binding, "binding")
        result = audit_l07_runtime_release(
            runtime=runtime,
            health=health,
            binding=binding,
            runtime_path=args.runtime,
            health_path=args.health,
        )
        exit_code = 0
    except L07RuntimeHold as exc:
        result = {
            "schema": "minimalizer/local-l07/runtime-release/v1",
            "status": "HOLD",
            "failures": (str(exc),),
            "private_artifacts_opened": False,
            "release_authorized": False,
        }
        exit_code = 2
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(_cli())
