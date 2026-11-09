"""Verify the candidate-specific independent Phase4 receipt for L02.

This verifier consumes only signed hashes, a frozen-candidate receipt, and an
independent review attestation. It never opens source pixels, masks, labels, or
NPZ files, and it never authorizes Phase5, Golden, merge, or production.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Mapping


SOURCE_SHA256 = {
    "H04": "7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3",
    "H06": "c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8",
    "H08": "759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e",
}
CASES = tuple(SOURCE_SHA256)
GLOBAL_TRUE_FLAGS = (
    "signature_verified",
    "unseen_data",
    "labels_unavailable_before_inference",
    "evaluator_independent",
    "semantic_review_complete",
    "unknown_mask_is_unknown",
    "output_frozen_before_scoring",
)
GLOBAL_FALSE_FLAGS = (
    "human_masks_used_in_inference",
    "review_json_used_in_inference",
)
CASE_TRUE_FLAGS = (
    "source_sha_verified",
    "candidate_sha_verified",
    "correct_garment_preserved",
    "wrong_owner_removed_only_where_justified",
    "sleeve_recovery_owner_exclusive",
    "occlusion_and_critical_parts_preserved",
    "visual_difference_acceptable",
    "unknown_not_negative",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class Phase4ReceiptHold(ValueError):
    """The receipt is absent, malformed, stale, or does not pass Phase4."""

    def __init__(self, failures: list[str]):
        self.failures = failures
        super().__init__(";".join(failures))


def _load_json(path: Path) -> Mapping[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise Phase4ReceiptHold(["JSON_ROOT_NOT_OBJECT"])
    return value


def _check_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def verify_phase4_receipt(
    receipt: Mapping[str, object],
    freeze_receipt: Mapping[str, object],
) -> dict[str, object]:
    """Return a non-promoting PASS result or raise ``Phase4ReceiptHold``."""
    failures: list[str] = []
    if receipt.get("schema") != "minimalizer/l02/phase4-independent-review/v1":
        failures.append("RECEIPT_SCHEMA_MISMATCH")
    if receipt.get("phase4") != "PASS":
        failures.append("RECEIPT_PHASE4_NOT_PASS")
    if not isinstance(receipt.get("reviewer_id"), str) or not receipt["reviewer_id"]:
        failures.append("REVIEWER_ID_MISSING")
    if not _check_timestamp(receipt.get("reviewed_at_utc")):
        failures.append("REVIEW_TIMESTAMP_INVALID")
    for name in GLOBAL_TRUE_FLAGS:
        if receipt.get(name) is not True:
            failures.append("GLOBAL_FLAG_FAIL:" + name)
    for name in GLOBAL_FALSE_FLAGS:
        if receipt.get(name) is not False:
            failures.append("GLOBAL_FLAG_FAIL:" + name)

    freeze_cases = freeze_receipt.get("cases")
    if freeze_receipt.get("human_labels_used") is not False:
        failures.append("FREEZE_LABEL_LEAK_FLAG")
    if freeze_receipt.get("unknown_not_treated_as_negative") is not True:
        failures.append("FREEZE_UNKNOWN_POLICY_FLAG")
    if not isinstance(freeze_cases, Mapping):
        failures.append("FREEZE_CASES_MISSING")
        freeze_cases = {}
    review_cases = receipt.get("cases")
    if not isinstance(review_cases, Mapping):
        failures.append("REVIEW_CASES_MISSING")
        review_cases = {}

    verified_cases: dict[str, dict[str, str]] = {}
    for case in CASES:
        review_case = review_cases.get(case)
        freeze_case = freeze_cases.get(case)
        if not isinstance(review_case, Mapping):
            failures.append(f"CASE_MISSING:{case}")
            continue
        if not isinstance(freeze_case, Mapping):
            failures.append(f"FREEZE_CASE_MISSING:{case}")
            continue
        if review_case.get("source_sha256") != SOURCE_SHA256[case]:
            failures.append(f"SOURCE_SHA_MISMATCH:{case}")
        expected_candidate = freeze_case.get("candidate_array_sha256")
        actual_candidate = review_case.get("candidate_sha256")
        if not isinstance(expected_candidate, str) or not SHA256_RE.fullmatch(expected_candidate):
            failures.append(f"FREEZE_CANDIDATE_SHA_INVALID:{case}")
        if not isinstance(actual_candidate, str) or not SHA256_RE.fullmatch(actual_candidate):
            failures.append(f"REVIEW_CANDIDATE_SHA_INVALID:{case}")
        elif actual_candidate != expected_candidate:
            failures.append(f"CANDIDATE_SHA_MISMATCH:{case}")
        for name in CASE_TRUE_FLAGS:
            if review_case.get(name) is not True:
                failures.append(f"CASE_FLAG_FAIL:{case}:{name}")
        verified_cases[case] = {
            "source_sha256": SOURCE_SHA256[case],
            "candidate_sha256": actual_candidate if isinstance(actual_candidate, str) else "",
        }

    if failures:
        raise Phase4ReceiptHold(failures)
    return {
        "schema": "minimalizer/l02/phase4-verification/v1",
        "phase4": "PASS",
        "phase5": "NO_GO",
        "golden": "HOLD",
        "production": "NO_GO",
        "cases": verified_cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("freeze_receipt", type=Path)
    args = parser.parse_args()
    try:
        result = verify_phase4_receipt(_load_json(args.receipt), _load_json(args.freeze_receipt))
    except Phase4ReceiptHold as exc:
        print(json.dumps({"phase4": "HOLD", "phase5": "NO_GO", "failures": exc.failures}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
