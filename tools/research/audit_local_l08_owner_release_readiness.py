"""Fail-closed final readiness audit for the current A/B candidate.

This command binds the current A L04 receipt to the already completed B
private-HTTPS and physical-iPhone receipts.  It only produces an owner-action
readiness result; it never authorizes, deploys, or changes production.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

try:
    from .local_l05_owner_run_receipt import L05Hold, audit_receipt
    from .local_l07_pwa_privacy_audit import PrivacyHold, audit as audit_l07
except ImportError:  # pragma: no cover - direct CLI execution
    from local_l05_owner_run_receipt import L05Hold, audit_receipt  # type: ignore
    from local_l07_pwa_privacy_audit import PrivacyHold, audit as audit_l07  # type: ignore


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


def _sha256_file(path: Path, field: str) -> str:
    if not path.is_file():
        raise L08Hold(f"MISSING_FILE:{field}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _audit_l04_manifest(manifest_path: Path, candidate_sha: str) -> dict[str, Any]:
    """Verify that the L04 manifest and every Stage8 JSON say the same thing.

    The top-level manifest is not authoritative by itself.  A stale or
    hand-edited manifest must not turn per-case HOLD/NO_GO Stage8 artifacts
    into a release-ready result.
    """

    manifest = _json(manifest_path)
    if manifest.get("schema") != "minimalizer/local-l04/production-bundle/v1":
        raise L08Hold("L04_MANIFEST_SCHEMA")
    if _sha(manifest.get("candidate_receipt_sha256"), "l04.candidate_receipt_sha256") != candidate_sha:
        raise L08Hold("L04_CANDIDATE_BINDING")
    if manifest.get("L04_formal") != "PASS" or manifest.get("Golden") != "PASS":
        raise L08Hold("L04_MANIFEST_GATE")
    production = manifest.get("production")
    if production not in {"GO", "NO_GO"}:
        raise L08Hold("L04_MANIFEST_PRODUCTION")
    cases = manifest.get("cases")
    if not isinstance(cases, Mapping) or set(cases) != {"H04", "H06", "H08"}:
        raise L08Hold("L04_CASE_SET")

    base = manifest_path.parent.resolve()
    for case in ("H04", "H06", "H08"):
        entry = cases[case]
        if not isinstance(entry, Mapping):
            raise L08Hold(f"L04_CASE_ENTRY:{case}")
        source = entry.get("source")
        stage8_ref = entry.get("stage8_json")
        svg_ref = entry.get("expanded_svg")
        if not isinstance(source, Mapping) or not isinstance(stage8_ref, Mapping) or not isinstance(svg_ref, Mapping):
            raise L08Hold(f"L04_CASE_ARTIFACTS:{case}")
        source_sha = _sha(source.get("sha256"), f"l04.{case}.source.sha256")
        stage8_path_value = stage8_ref.get("path")
        svg_path_value = svg_ref.get("path")
        if not isinstance(stage8_path_value, str) or not isinstance(svg_path_value, str):
            raise L08Hold(f"L04_CASE_PATHS:{case}")
        stage8_path = (base / stage8_path_value).resolve()
        svg_path = (base / svg_path_value).resolve()
        if base not in stage8_path.parents or base not in svg_path.parents:
            raise L08Hold(f"L04_CASE_PATH_ESCAPE:{case}")
        if _sha256_file(stage8_path, f"l04.{case}.stage8") != _sha(stage8_ref.get("sha256"), f"l04.{case}.stage8.sha256"):
            raise L08Hold(f"L04_STAGE8_FILE_SHA:{case}")
        if _sha256_file(svg_path, f"l04.{case}.expanded_svg") != _sha(svg_ref.get("sha256"), f"l04.{case}.expanded_svg.sha256"):
            raise L08Hold(f"L04_SVG_FILE_SHA:{case}")
        stage8 = _json(stage8_path)
        if stage8.get("signed_source_sha256") != source_sha:
            raise L08Hold(f"L04_STAGE8_SOURCE_BINDING:{case}")
        if stage8.get("expanded_svg_sha256") != svg_ref.get("sha256"):
            raise L08Hold(f"L04_STAGE8_SVG_BINDING:{case}")
        if stage8.get("formal_status") != "PASS":
            raise L08Hold(f"L04_CASE_FORMAL_STATUS:{case}")
        expected_release = "GO" if production == "GO" else "NO_GO"
        if stage8.get("production_release") != expected_release:
            raise L08Hold(f"L04_CASE_RELEASE_STATUS:{case}")
        if stage8.get("source_only_inference") is not True:
            raise L08Hold(f"L04_SOURCE_ONLY:{case}")
        if stage8.get("human_labels_used_for_inference") is not False:
            raise L08Hold(f"L04_LABEL_LEAK:{case}")
        if stage8.get("unknown_pixels_treated_as_negative") is not False:
            raise L08Hold(f"L04_UNKNOWN_POLICY:{case}")

    return {
        "manifest_sha256": _sha256_file(manifest_path, "l04.manifest"),
        "production": production,
        "cases": "H04,H06,H08",
    }


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
    l04_manifest_path: Path,
    production_commit: str,
    repository_root: Path,
) -> dict[str, Any]:
    if _COMMIT.fullmatch(production_commit) is None:
        raise L08Hold("EXPECTED_PRODUCTION_COMMIT_INVALID")
    a = _audit_a(_json(a_receipt_path))
    l04 = _audit_l04_manifest(l04_manifest_path, a["candidate_receipt_sha256"])
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
    try:
        l07 = audit_l07(repository_root)
    except (OSError, PrivacyHold) as exc:
        raise L08Hold(f"B_L07_STATIC:{exc}") from exc
    if l07.get("serviceworker", {}).get("status") != "STATIC_SW_PRIVACY_CONTRACT_PASS":
        raise L08Hold("B_L07_STATIC_SW")
    if l07.get("route", {}).get("status") != "STATIC_LOCAL_ROUTE_ISOLATED":
        raise L08Hold("B_L07_STATIC_ROUTE")
    iphone = _audit_iphone(_json(iphone_receipt_path), production_commit)
    return {
        "schema": "minimalizer/local-l08/owner-release-readiness/v1",
        "ready_for_owner_release": True,
        "A_L04_formal": a["L04_formal"],
        "A_Golden": a["Golden"],
        "candidate_receipt_sha256": a["candidate_receipt_sha256"],
        "L04_manifest_sha256": l04["manifest_sha256"],
        "L04_manifest_production": l04["production"],
        "B_L05_pc_e2e": "PASS",
        "B_L07_static": "PASS",
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
    parser.add_argument("--l04-manifest", type=Path, required=True)
    parser.add_argument("--production-commit", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit_owner_release_readiness(
            args.a_receipt,
            args.pc_receipt,
            args.iphone_receipt,
            l04_manifest_path=args.l04_manifest,
            production_commit=args.production_commit,
            repository_root=args.repository_root,
        )
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"L08_OWNER_RELEASE_READINESS_PASS {args.output}")
        return 0
    except (OSError, L08Hold) as exc:
        print(f"HOLD {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
