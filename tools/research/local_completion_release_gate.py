"""Cross-lane final-release binding for MinimalizerLocal.

This gate consumes source-free receipts only.  It does not inspect or copy
private images, masks, SVGs, device screenshots, or secrets.  A release is
admitted only when every receipt refers to the same candidate and the current
production Worker baseline; stale readiness summaries remain HOLD.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


EXPECTED_CANDIDATE_RECEIPT_SHA256 = (
    "381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a"
)
EXPECTED_PRODUCTION_WORKER_COMMIT = (
    "64cfeb76e5f8ff4e93b6810880c68f1996348ede"
)


@dataclass(frozen=True)
class ReleaseBindingAssessment:
    status: str
    release_authorized: bool
    failures: tuple[str, ...]


def _require_equal(
    failures: list[str], payload: Mapping[str, Any], key: str, expected: Any
) -> None:
    if payload.get(key) != expected:
        failures.append(f"{key} mismatch")


def assess_release_binding(
    *,
    candidate_receipt_sha256: str,
    production_worker_commit: str,
    l04: Mapping[str, Any],
    l05: Mapping[str, Any],
    l07: Mapping[str, Any],
    owner_action_required: bool,
) -> ReleaseBindingAssessment:
    """Return PASS only for one exact candidate and complete release evidence."""
    failures: list[str] = []
    if candidate_receipt_sha256 != EXPECTED_CANDIDATE_RECEIPT_SHA256:
        failures.append("candidate receipt mismatch")
    if production_worker_commit != EXPECTED_PRODUCTION_WORKER_COMMIT:
        failures.append("production Worker commit mismatch")
    for key, expected in (
        ("L04_formal", "PASS"),
        ("Golden", "PASS"),
        ("production", "GO"),
        ("release_authorized", True),
    ):
        _require_equal(failures, l04, key, expected)
    for lane, payload in (("L05", l05), ("L07", l07)):
        if payload.get("status") != "PASS":
            failures.append(f"{lane} status is not PASS")
        if payload.get("candidate_receipt_sha256") != EXPECTED_CANDIDATE_RECEIPT_SHA256:
            failures.append(f"{lane} candidate binding mismatch")
        if payload.get("production_worker_commit") != EXPECTED_PRODUCTION_WORKER_COMMIT:
            failures.append(f"{lane} Worker binding mismatch")
    if owner_action_required:
        failures.append("owner action required")
    return ReleaseBindingAssessment(
        status="PASS" if not failures else "HOLD",
        release_authorized=not failures,
        failures=tuple(failures),
    )


__all__ = [
    "EXPECTED_CANDIDATE_RECEIPT_SHA256",
    "EXPECTED_PRODUCTION_WORKER_COMMIT",
    "ReleaseBindingAssessment",
    "assess_release_binding",
]
