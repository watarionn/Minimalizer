"""Materialize the final L04 delta-review receipt after an independent PASS.

The reviewer still supplies only the plain-text answer.  This command binds
that answer to the current candidate triple, the numerical/B audits, and the
H08 owner-authority receipt.  It never authorizes production or changes any
private image artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

try:
    from .verify_local_l04_visual_delta_review import (
        VisualReviewHold,
        readback_delta_review,
    )
except ImportError:  # pragma: no cover - direct CLI execution
    from verify_local_l04_visual_delta_review import (  # type: ignore
        VisualReviewHold,
        readback_delta_review,
    )


CASES = ("H04", "H06", "H08")
EXPECTED_FROZEN_H08_OWNER_SHA = (
    "43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52"
)


class DeltaReceiptHold(ValueError):
    """The independent delta review cannot be promoted to a formal receipt."""


def _json(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise DeltaReceiptHold(f"MISSING_FILE:{path.name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise DeltaReceiptHold(f"JSON_ROOT_NOT_OBJECT:{path.name}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate_binding(package: Path) -> tuple[Mapping[str, Any], dict[str, Any]]:
    receipt = _json(package / "L04_CANDIDATE_TRIPLE_RECEIPT.json")
    if receipt.get("schema") != "minimalizer/local-l04/candidate-triple-receipt/v1":
        raise DeltaReceiptHold("CANDIDATE_RECEIPT_SCHEMA")
    receipt_cases = receipt.get("cases")
    if not isinstance(receipt_cases, list) or tuple(item.get("case") for item in receipt_cases) != CASES:
        raise DeltaReceiptHold("CANDIDATE_RECEIPT_CASES")
    audit = _json(package / "L04_CANDIDATE_TRIPLE_AUDIT.json")
    audit_cases = audit.get("cases")
    if not isinstance(audit_cases, Mapping):
        raise DeltaReceiptHold("CANDIDATE_AUDIT_CASES")
    receipt_by_case = {str(item["case"]): item for item in receipt_cases}
    for case in CASES:
        receipt_item = receipt_by_case[case]
        audit_item = audit_cases.get(case)
        if not isinstance(audit_item, Mapping) or audit_item.get("failures") != []:
            raise DeltaReceiptHold(f"CANDIDATE_AUDIT_HOLD:{case}")
        for field in ("source_sha256", "stage8_json_sha256", "expanded_svg_sha256"):
            if receipt_item.get(field) != audit_item.get(field):
                raise DeltaReceiptHold(f"CANDIDATE_BINDING_MISMATCH:{case}:{field}")
    actual_receipt_sha = _sha256(package / "L04_CANDIDATE_TRIPLE_RECEIPT.json")
    return receipt, {
        "receipt_sha256": actual_receipt_sha,
        "cases": receipt_by_case,
        "audit_schema": audit.get("schema"),
    }


def _verify_h08_authority(package: Path, h08: Mapping[str, Any]) -> dict[str, Any]:
    authority = _json(package / "authority" / "H08_OWNER_AUTHORITY_RECEIPT.json")
    if authority.get("schema") != "minimalizer/local-l02/h08-owner-authority/v1":
        raise DeltaReceiptHold("H08_AUTHORITY_SCHEMA")
    if authority.get("case") != "H08":
        raise DeltaReceiptHold("H08_AUTHORITY_CASE")
    if authority.get("frozen_owner_sha256") != EXPECTED_FROZEN_H08_OWNER_SHA:
        raise DeltaReceiptHold("H08_AUTHORITY_OWNER_SHA")
    if authority.get("source_sha256") != h08.get("source_sha256"):
        raise DeltaReceiptHold("H08_AUTHORITY_SOURCE_SHA")
    if authority.get("prediction_sha256") != h08.get("candidate_sha256"):
        raise DeltaReceiptHold("H08_AUTHORITY_CANDIDATE_SHA")
    required = (
        "owner_promotion_authorized",
        "authority_receipt_verified",
        "bound_to_case",
        "bound_to_source_sha",
        "bound_to_prediction_sha",
        "bound_to_observer_sha",
        "owner_promotion_explicitly_approved",
        "unknown_not_promoted",
        "human_labels_not_used_for_inference",
        "production_not_authorized",
    )
    if any(authority.get(field) is not True for field in required):
        raise DeltaReceiptHold("H08_AUTHORITY_BOOLEAN_GATE")
    if authority.get("golden") != "HOLD" or authority.get("production") != "NO_GO":
        raise DeltaReceiptHold("H08_AUTHORITY_RELEASE_GATE")
    return {
        "receipt_sha256": _sha256(package / "authority" / "H08_OWNER_AUTHORITY_RECEIPT.json"),
        "frozen_owner_sha256": authority["frozen_owner_sha256"],
        "source_sha256": authority["source_sha256"],
        "prediction_sha256": authority["prediction_sha256"],
        "owner_promotion_authorized": True,
        "production_not_authorized": True,
    }


def materialize_delta_receipt(review_path: Path, package: Path) -> dict[str, Any]:
    try:
        review = readback_delta_review(review_path, package)
    except VisualReviewHold as exc:
        raise DeltaReceiptHold(f"REVIEW_HOLD:{exc}") from exc
    if review.get("review_gate") != "PASS":
        raise DeltaReceiptHold("REVIEW_GATE_NOT_PASS")
    candidate_receipt, binding = _candidate_binding(package)
    authority = _verify_h08_authority(package, binding["cases"]["H08"])
    return {
        "schema": "minimalizer/local-l04/independent-visual-delta-review-receipt/v1",
        "receipt_created": True,
        "candidate_receipt_sha256": binding["receipt_sha256"],
        "candidate_receipt": candidate_receipt,
        "review_readback": review,
        "authority": authority,
        "L04_formal": "PASS",
        "Golden": "PASS",
        "production": "NO_GO",
        "release_authorized": False,
        "phase5_promotion": "NOT_AUTHORIZED_BY_THIS_RECEIPT",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="L04差分PASSを正式readback receiptへ固定する")
    parser.add_argument("review", type=Path)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = materialize_delta_receipt(args.review, args.package)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"L04_DELTA_RECEIPT_CREATED {args.output}")
        return 0
    except (OSError, json.JSONDecodeError, DeltaReceiptHold) as exc:
        print(f"HOLD {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
