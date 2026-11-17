"""Cross-lane final-release binding for MinimalizerLocal.

This gate consumes source-free receipts only.  It does not inspect or copy
private images, masks, SVGs, device screenshots, or secrets.  A release is
admitted only when A quality, frozen Phase4/Phase5 evidence, B delivery, and
current-device acceptance all refer to the same candidate and Worker baseline.
Stale readiness summaries remain HOLD.
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
REQUIRED_OBSERVER_CAPABILITIES = (
    "arm",
    "instance_grouping",
    "occlusion_garment_body",
    "occlusion_outerwear_underlayer",
    "occlusion_sleeve_arm",
    "outerwear",
    "sleeve",
    "underlayer",
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


def _require_true(
    failures: list[str], payload: Mapping[str, Any], names: tuple[str, ...], scope: str
) -> None:
    for name in names:
        if payload.get(name) is not True:
            failures.append(f"{scope} {name} is not PASS")


def _require_observer_capabilities(
    failures: list[str], payload: Mapping[str, Any]
) -> None:
    """Require the exact A-lane capability contract, not only a summary flag."""
    value = payload.get("observer_capabilities")
    if not isinstance(value, (list, tuple)):
        failures.append("A observer_capabilities contract is missing")
        return
    observed = tuple(sorted(item for item in value if isinstance(item, str)))
    if observed != REQUIRED_OBSERVER_CAPABILITIES:
        failures.append("A observer_capabilities contract mismatch")


def _bind(
    failures: list[str], payload: Mapping[str, Any], scope: str, *, require_worker: bool
) -> None:
    if payload.get("status") != "PASS":
        failures.append(f"{scope} status is not PASS")
    if payload.get("candidate_receipt_sha256") != EXPECTED_CANDIDATE_RECEIPT_SHA256:
        failures.append(f"{scope} candidate binding mismatch")
    if require_worker and payload.get("production_worker_commit") != EXPECTED_PRODUCTION_WORKER_COMMIT:
        failures.append(f"{scope} Worker binding mismatch")


def assess_release_binding(
    *,
    candidate_receipt_sha256: str,
    production_worker_commit: str,
    a: Mapping[str, Any],
    phase4: Mapping[str, Any],
    phase5: Mapping[str, Any],
    l04: Mapping[str, Any],
    l05: Mapping[str, Any],
    l07: Mapping[str, Any],
    acceptance: Mapping[str, Any],
    regression: Mapping[str, Any],
    preservation: Mapping[str, Any],
    owner_action_required: bool,
) -> ReleaseBindingAssessment:
    """Return PASS only for the complete A/B release evidence chain."""
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
    if l04.get("candidate_receipt_sha256") != EXPECTED_CANDIDATE_RECEIPT_SHA256:
        failures.append("L04 candidate binding mismatch")
    _require_true(
        failures,
        l04,
        (
            "triple_case_delivery_verified",
            "source_sha_bound",
            "stage8_json_sha_bound",
            "expanded_svg_sha_bound",
        ),
        "L04",
    )

    _bind(failures, a, "A", require_worker=False)
    _require_true(
        failures,
        a,
        (
            "six_capabilities",
            "same_config_three_cases",
            "source_only_inference",
            "unknown_preserved",
            "h04_pass",
            "h06_pass",
            "h08_pass",
        ),
        "A",
    )
    _require_observer_capabilities(failures, a)
    if a.get("human_labels_used_for_inference") is not False:
        failures.append("A human_labels_used_for_inference is not false")

    _bind(failures, phase4, "Phase4", require_worker=False)
    _require_true(
        failures,
        phase4,
        (
            "independent_evaluator",
            "unseen_data",
            "labels_unavailable_before_inference",
            "output_frozen_before_scoring",
            "semantic_review_complete",
            "unknown_not_negative",
            "source_alpha_bounds_pass",
            "owner_exclusivity_pass",
            "components4_pass",
            "components8_pass",
            "holes4_pass",
            "holes8_pass",
            "occlusion_and_critical_parts_pass",
        ),
        "Phase4",
    )
    if phase4.get("review_json_used_in_inference") is not False:
        failures.append("Phase4 review_json_used_in_inference is not false")

    _bind(failures, phase5, "Phase5", require_worker=False)
    _require_true(
        failures,
        phase5,
        (
            "exact_replay",
            "same_config_three_cases",
            "source_sha_match",
            "output_sha_match",
        ),
        "Phase5",
    )

    for lane, payload in (("L05", l05), ("L07", l07)):
        _bind(failures, payload, lane, require_worker=True)
    _require_true(
        failures,
        l07,
        (
            "generation_pinned",
            "rollback_available",
            "runtime_sw_audit_pass",
            "runtime_generation_bound",
        ),
        "L07",
    )

    _bind(failures, acceptance, "device acceptance", require_worker=True)
    _require_true(
        failures,
        acceptance,
        (
            "pc",
            "iphone_safari",
            "iphone_pwa",
            "png",
            "svg",
            "offline_recovery",
            "failure_paths",
            "fallback",
            "rollback",
        ),
        "device acceptance",
    )

    _bind(failures, regression, "regression", require_worker=False)
    _require_true(
        failures,
        regression,
        (
            "l06_golden_pass",
            "approved18_to_78_pass",
            "browser_render_pass",
            "performance_pass",
        ),
        "regression",
    )

    _bind(failures, preservation, "preservation", require_worker=False)
    _require_true(
        failures,
        preservation,
        (
            "release_sha_bound",
            "artifact_sha_bound",
            "private_drive_saved",
            "private_drive_readback",
            "source_free_ledger",
        ),
        "preservation",
    )
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
    "REQUIRED_OBSERVER_CAPABILITIES",
    "ReleaseBindingAssessment",
    "assess_release_binding",
]
