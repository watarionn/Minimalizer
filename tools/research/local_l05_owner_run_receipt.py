"""Fail-closed audit for an owner-collected Local L05 E2E receipt.

The receipt contains metadata and hashes only; private images and response
bodies stay on the owner PC/Drive. This validator checks that the claimed
private-HTTPS PC run covers real PNG success and failure paths plus file
readback. It never performs network requests and never authorizes release.
"""
from __future__ import annotations

import re


class L05Hold(ValueError):
    """Incomplete, contradictory, or unsafe owner-run evidence."""


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SCHEMA = "minimalizer/local-l05/owner-run-receipt/v1"


def _require_sha(value: object, field: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise L05Hold("INVALID_SHA:" + field)
    return value


def _require_bool(record: dict, field: str) -> None:
    if type(record.get(field)) is not bool:
        raise L05Hold("INVALID_BOOLEAN:" + field)


def audit_receipt(receipt: dict) -> dict:
    required = {
        "schema", "transport", "production", "device",
        "owner_identity_verified", "origin_verified", "tailnet_verified",
        "health", "success", "failures", "readback",
    }
    if not isinstance(receipt, dict) or set(receipt) != required:
        raise L05Hold("RECEIPT_SCHEMA_FAIL_CLOSED")
    if receipt["schema"] != _SCHEMA:
        raise L05Hold("RECEIPT_SCHEMA_INVALID")
    if receipt["transport"] != "private_https":
        raise L05Hold("PRIVATE_HTTPS_REQUIRED")
    if receipt["device"] not in {"pc", "iphone"}:
        raise L05Hold("UNSUPPORTED_DEVICE")
    for field in ("production", "owner_identity_verified", "origin_verified",
                  "tailnet_verified"):
        _require_bool(receipt, field)
    if receipt["device"] == "iphone" and not receipt["production"]:
        raise L05Hold("IPHONE_ACCEPTANCE_REQUIRES_PRODUCTION")
    if not all(receipt[field] for field in (
            "owner_identity_verified", "origin_verified", "tailnet_verified")):
        raise L05Hold("OWNER_NETWORK_IDENTITY_NOT_VERIFIED")

    health = receipt["health"]
    if (not isinstance(health, dict) or set(health) != {"status", "worker", "ready"}
            or health["status"] != 200
            or health["worker"] != "local-compute-v1"
            or health["ready"] is not True):
        raise L05Hold("HEALTH_READINESS_FAIL")

    successes = receipt["success"]
    if not isinstance(successes, list):
        raise L05Hold("PNG_SUCCESS_RECEIPT_REQUIRED")
    success_routes = {r.get("route") for r in successes
                      if isinstance(r, dict)}
    if "v2" not in success_routes or len(success_routes) != len(successes):
        raise L05Hold("V2_PNG_ROUTE_REQUIRED")
    for row in successes:
        if (not isinstance(row, dict) or
                set(row) != {"route", "status", "content_type",
                             "input_sha256", "output_sha256",
                             "input_readback", "output_readback"}):
            raise L05Hold("SUCCESS_RECEIPT_SCHEMA_FAIL_CLOSED")
        if row["route"] not in {"zerobase2", "v2"} or row["status"] != 200:
            raise L05Hold("PNG_SUCCESS_STATUS_INVALID")
        if row["content_type"] != "image/png":
            raise L05Hold("PNG_CONTENT_TYPE_REQUIRED")
        _require_sha(row["input_sha256"], "input_sha256")
        _require_sha(row["output_sha256"], "output_sha256")
        if row["input_readback"] is not True or row["output_readback"] is not True:
            raise L05Hold("PNG_FILE_READBACK_REQUIRED")

    failures = receipt["failures"]
    if not isinstance(failures, dict) or set(failures) != {
            "invalid_type", "busy", "unavailable"}:
        raise L05Hold("FAILURE_PATHS_INCOMPLETE")
    expected = {"invalid_type": 415, "busy": 429, "unavailable": 503}
    for name, row in failures.items():
        if not isinstance(row, dict) or "status" not in row or row["status"] != expected[name]:
            raise L05Hold("FAILURE_STATUS_INVALID:" + name)
    busy = failures["busy"]
    if busy.get("retry_after") != "2":
        raise L05Hold("RETRY_AFTER_READBACK_REQUIRED")

    readback = receipt["readback"]
    if (not isinstance(readback, dict) or
            set(readback) != {"input_hashes", "output_hashes", "failure_paths",
                              "device_file_readback"} or
            not all(readback.values())):
        raise L05Hold("READBACK_INCOMPLETE")
    return {
        "schema": "minimalizer/local-l05/owner-run-receipt-audit/v1",
        "owner_pc_e2e_verified": receipt["device"] == "pc",
        "png_routes_verified": True,
        "v2_png_verified": "v2" in success_routes,
        "zerobase2_png_verified": "zerobase2" in success_routes,
        "zerobase2_fallback_verified": (
            "zerobase2" not in success_routes and
            failures["unavailable"]["status"] == 503),
        "failure_paths_verified": True,
        "file_readback_verified": True,
        "physical_iphone_acceptance": (
            "NOT_INCLUDED" if receipt["device"] == "pc" else "OWNER_RECORDED"),
        "L05_formal": "HOLD",
        "production_release": "NO_GO",
        "release_authorized": False,
    }
