"""Bind an owner L05 receipt to the current candidate and Worker.

This is a source-free bridge for legacy owner receipts.  It reads only the
receipt JSON and a small binding JSON; it never opens images, screenshots,
response bodies, or private Drive files.  A raw receipt is accepted only when
its content is valid and its byte SHA is the one recorded by the binding.
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
from tools.research.local_l05_owner_run_receipt import (  # noqa: E402
    L05Hold,
    audit_receipt,
)


BINDING_SCHEMA = "minimalizer/local-l05/current-worker-binding/v1"
PC_SCHEMA = "minimalizer/local-l05/owner-run-receipt/v1"
IPHONE_SCHEMA = "minimalizer/local-l05-l07/iphone-acceptance/v1"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")


class CurrentWorkerBindingHold(ValueError):
    """Receipt content or current candidate/Worker binding is unsafe."""


def _sha(value: object, field: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise CurrentWorkerBindingHold(f"INVALID_SHA:{field}")
    return value


def _commit(value: object, field: str) -> str:
    if not isinstance(value, str) or COMMIT.fullmatch(value) is None:
        raise CurrentWorkerBindingHold(f"INVALID_COMMIT:{field}")
    return value


def _load(path: Path) -> tuple[Mapping[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CurrentWorkerBindingHold(f"RECEIPT_READ_FAILED:{type(exc).__name__}") from exc
    if not isinstance(value, Mapping):
        raise CurrentWorkerBindingHold("RECEIPT_ROOT_NOT_OBJECT")
    return value, raw


def _audit_iphone_content(receipt: Mapping[str, Any]) -> None:
    required = {
        "schema", "production_commit", "transport", "device", "owner_attestation",
        "safari", "pwa", "offline_restore", "fallback", "private_drive_readback",
    }
    if set(receipt) != required or receipt.get("schema") != IPHONE_SCHEMA:
        raise CurrentWorkerBindingHold("IPHONE_RECEIPT_SCHEMA_FAIL_CLOSED")
    if receipt.get("transport") != "private_https" or receipt.get("device") != "iphone":
        raise CurrentWorkerBindingHold("IPHONE_PRIVATE_HTTPS_REQUIRED")
    if receipt.get("production") is False:
        raise CurrentWorkerBindingHold("IPHONE_PRODUCTION_REQUIRED")
    if receipt.get("owner_attestation") is not True:
        raise CurrentWorkerBindingHold("IPHONE_OWNER_ATTESTATION_REQUIRED")
    for section, fields in {
        "safari": ("png_result_visible", "zerobase2_success_visible", "evidence_sha256"),
        "pwa": ("png_result_visible", "zerobase2_success_visible", "evidence_sha256"),
        "fallback": ("zerobase2_503_visible", "local_v2_success_visible", "evidence_sha256"),
    }.items():
        value = receipt.get(section)
        if not isinstance(value, Mapping) or any(value.get(field) is not True for field in fields[:2]):
            raise CurrentWorkerBindingHold(f"IPHONE_{section.upper()}_INCOMPLETE")
        _sha(value.get(fields[2]), f"{section}.evidence_sha256")
    offline = receipt.get("offline_restore")
    if not isinstance(offline, Mapping) or offline.get("airplane_mode_round_trip_passed") is not True:
        raise CurrentWorkerBindingHold("IPHONE_OFFLINE_RESTORE_REQUIRED")
    if receipt.get("private_drive_readback") is not True:
        raise CurrentWorkerBindingHold("IPHONE_DRIVE_READBACK_REQUIRED")
    if receipt.get("production_commit") != EXPECTED_PRODUCTION_WORKER_COMMIT:
        raise CurrentWorkerBindingHold("IPHONE_WORKER_COMMIT_MISMATCH")


def audit_current_worker_binding(
    receipt: Mapping[str, Any],
    binding: Mapping[str, Any],
    receipt_sha256: str,
) -> dict[str, object]:
    """Return PASS only when raw content and exact current binding agree."""
    if binding.get("schema") != BINDING_SCHEMA:
        raise CurrentWorkerBindingHold("INVALID_BINDING_SCHEMA")
    candidate = _sha(binding.get("candidate_receipt_sha256"), "candidate_receipt_sha256")
    worker = _commit(binding.get("production_worker_commit"), "production_worker_commit")
    source_sha = _sha(binding.get("source_receipt_sha256"), "source_receipt_sha256")
    if candidate != EXPECTED_CANDIDATE_RECEIPT_SHA256:
        raise CurrentWorkerBindingHold("CANDIDATE_RECEIPT_MISMATCH")
    if worker != EXPECTED_PRODUCTION_WORKER_COMMIT:
        raise CurrentWorkerBindingHold("PRODUCTION_WORKER_MISMATCH")
    if source_sha != receipt_sha256:
        raise CurrentWorkerBindingHold("SOURCE_RECEIPT_SHA_MISMATCH")

    schema = receipt.get("schema")
    if schema == PC_SCHEMA:
        try:
            content = audit_receipt(dict(receipt))
        except (L05Hold, TypeError) as exc:
            raise CurrentWorkerBindingHold(f"PC_RECEIPT_HOLD:{exc}") from exc
        device = "pc"
    elif schema == IPHONE_SCHEMA:
        _audit_iphone_content(receipt)
        content = {"physical_iphone_acceptance": "OWNER_RECORDED"}
        device = "iphone"
    else:
        raise CurrentWorkerBindingHold("UNSUPPORTED_RECEIPT_SCHEMA")

    return {
        "schema": "minimalizer/local-l05/current-worker-binding-audit/v1",
        "status": "PASS",
        "candidate_receipt_sha256": candidate,
        "production_worker_commit": worker,
        "source_receipt_sha256": receipt_sha256,
        "source_receipt_schema": schema,
        "device": device,
        "content_verified": True,
        "private_artifacts_opened": False,
        "release_authorized": False,
        "content_summary": content,
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Bind an L05 receipt to the current Worker")
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        receipt, raw = _load(args.receipt)
        binding = json.loads(args.binding.read_text(encoding="utf-8"))
        if not isinstance(binding, Mapping):
            raise CurrentWorkerBindingHold("BINDING_ROOT_NOT_OBJECT")
        result = audit_current_worker_binding(
            receipt,
            binding,
            hashlib.sha256(raw).hexdigest(),
        )
        exit_code = 0
    except (CurrentWorkerBindingHold, OSError, UnicodeError, json.JSONDecodeError) as exc:
        result = {
            "schema": "minimalizer/local-l05/current-worker-binding-audit/v1",
            "status": "HOLD",
            "release_authorized": False,
            "failures": (str(exc),),
            "private_artifacts_opened": False,
        }
        exit_code = 2
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(_cli())
