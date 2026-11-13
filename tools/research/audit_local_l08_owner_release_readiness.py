"""Fail-closed final readiness audit for the current A/B candidate.

This command binds the current A L04 receipt to the already completed B
private-HTTPS and physical-iPhone receipts.  It only produces an owner-action
readiness result; it never authorizes, deploys, or changes production.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

try:
    from .local_l05_owner_run_receipt import L05Hold, audit_receipt
except ImportError:  # pragma: no cover - direct CLI execution
    from local_l05_owner_run_receipt import L05Hold, audit_receipt  # type: ignore


class L08Hold(ValueError):
    """The A/B evidence is incomplete or is not bound to owner release."""


_SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")
_COMMIT = re.compile(r"[0-9a-fA-F]{40}\Z")
_A_SCHEMA = "minimalizer/local-l04/independent-visual-delta-review-receipt/v1"
_IPHONE_SCHEMA = "minimalizer/local-l05-l07/iphone-acceptance/v1"


def _json(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise L08Hold(f"MISSING_FILE:{path.name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise L08Hold(f"INVALID_JSON:{path.name}") from exc
    if not isinstance(value, Mapping):
        raise L08Hold(f"JSON_ROOT_NOT_OBJECT:{path.name}")
    return value


def _sha(value: object, field: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise L08Hold(f"INVALID_SHA:{field}")
    return value.lower()


def _audit_a(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if receipt.get("schema") != _A_SCHEMA:
        raise L08Hold("A_RECEIPT_SCHEMA")
    if receipt.get("receipt_created") is not True:
        raise L08Hold("A_RECEIPT_NOT_CREATED")
    if receipt.get("L04_formal") != "PASS" or receipt.get("Golden") != "PASS":
        raise L08Hold("A_GOLDEN_NOT_PASS")
    if receipt.get("production") != "NO_GO" or receipt.get("release_authorized") is not False:
        raise L08Hold("A_RELEASE_BOUNDARY_CHANGED")

    candidate_sha = _sha(receipt.get("candidate_receipt_sha256"), "candidate_receipt_sha256")
    review = receipt.get("review_readback")
    if not isinstance(review, Mapping):
        raise L08Hold("A_REVIEW_READBACK_MISSING")
    if review.get("review_gate") != "PASS":
        raise L08Hold("A_REVIEW_GATE")
    if review.get("L04_formal") != "PASS" or review.get("Golden") != "PASS":
        raise L08Hold("A_REVIEW_GOLDEN")
    if review.get("production") != "NO_GO" or review.get("release_authorized") is not False:
        raise L08Hold("A_REVIEW_RELEASE_BOUNDARY")
    if _sha(review.get("review_binding_receipt_sha256"), "review_binding_receipt_sha256") != candidate_sha:
        raise L08Hold("A_REVIEW_CANDIDATE_BINDING")
    if review.get("candidate_numerical_audit") != "PASS" or review.get("b_delivery_audit") != "PASS":
        raise L08Hold("A_HANDOFF_AUDIT")
    return {
        "candidate_receipt_sha256": candidate_sha,
        "L04_formal": "PASS",
        "Golden": "PASS",
        "release_authorized": False,
    }


def _audit_iphone(receipt: Mapping[str, Any], expected_commit: str) -> dict[str, Any]:
    if receipt.get("schema") != _IPHONE_SCHEMA:
        raise L08Hold("IPHONE_RECEIPT_SCHEMA")
    if receipt.get("transport") != "private_https" or receipt.get("device") != "iphone":
        raise L08Hold("IPHONE_TRANSPORT_DEVICE")
    production_commit = receipt.get("production_commit")
    if not isinstance(production_commit, str) or _COMMIT.fullmatch(production_commit) is None:
        raise L08Hold("IPHONE_PRODUCTION_COMMIT")
    if production_commit.lower() != expected_commit.lower():
        raise L08Hold("IPHONE_PRODUCTION_COMMIT_MISMATCH")
    if receipt.get("owner_attestation") is not True or receipt.get("private_drive_readback") is not True:
        raise L08Hold("IPHONE_OWNER_READBACK")

    for name in ("safari", "pwa"):
        block = receipt.get(name)
        if not isinstance(block, Mapping) or block.get("png_result_visible") is not True or block.get("zerobase2_success_visible") is not True:
            raise L08Hold(f"IPHONE_{name.upper()}_RESULT")
        _sha(block.get("evidence_sha256"), f"{name}.evidence_sha256")
    offline = receipt.get("offline_restore")
    if not isinstance(offline, Mapping) or offline.get("airplane_mode_round_trip_passed") is not True:
        raise L08Hold("IPHONE_OFFLINE_RESTORE")
    fallback = receipt.get("fallback")
    if not isinstance(fallback, Mapping) or fallback.get("zerobase2_503_visible") is not True or fallback.get("local_v2_success_visible") is not True:
        raise L08Hold("IPHONE_FALLBACK")
    _sha(fallback.get("evidence_sha256"), "fallback.evidence_sha256")
    return {
        "production_commit": production_commit.lower(),
        "safari": "PASS",
        "pwa": "PASS",
        "offline_restore": "PASS",
        "fallback": "PASS",
    }


def audit_owner_release_readiness(
    a_receipt_path: Path,
    pc_receipt_path: Path,
    iphone_receipt_path: Path,
    *,
    production_commit: str,
) -> dict[str, Any]:
    if _COMMIT.fullmatch(production_commit) is None:
        raise L08Hold("EXPECTED_PRODUCTION_COMMIT_INVALID")
    a = _audit_a(_json(a_receipt_path))
    pc = _json(pc_receipt_path)
    try:
        pc_audit = audit_receipt(dict(pc))
    except L05Hold as exc:
        raise L08Hold(f"B_PC_RECEIPT:{exc}") from exc
    if pc.get("production") is not True or pc.get("device") != "pc":
        raise L08Hold("B_PC_PRODUCTION_DEVICE")
    if not all(pc_audit.get(field) is True for field in (
        "owner_pc_e2e_verified", "v2_png_verified", "failure_paths_verified", "file_readback_verified"
    )):
        raise L08Hold("B_PC_E2E_INCOMPLETE")
    iphone = _audit_iphone(_json(iphone_receipt_path), production_commit)
    return {
        "schema": "minimalizer/local-l08/owner-release-readiness/v1",
        "ready_for_owner_release": True,
        "A_L04_formal": a["L04_formal"],
        "A_Golden": a["Golden"],
        "candidate_receipt_sha256": a["candidate_receipt_sha256"],
        "B_L05_pc_e2e": "PASS",
        "B_L05_L07_iphone": iphone,
        "production": "NO_GO",
        "release_authorized": False,
        "owner_action_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="A/B現行候補のowner本番採用直前readinessを監査する")
    parser.add_argument("a_receipt", type=Path)
    parser.add_argument("pc_receipt", type=Path)
    parser.add_argument("iphone_receipt", type=Path)
    parser.add_argument("--production-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit_owner_release_readiness(
            args.a_receipt,
            args.pc_receipt,
            args.iphone_receipt,
            production_commit=args.production_commit,
        )
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"L08_OWNER_RELEASE_READINESS_PASS {args.output}")
        return 0
    except (OSError, L08Hold) as exc:
        print(f"HOLD {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
