"""Prepare and strictly materialize a candidate-bound L02 Phase4 receipt.

The workflow is deliberately human-first:

* ``init`` creates a plain-text review form from the current freeze receipt.
* A reviewer fills the form after inspecting the frozen candidate.
* ``materialize`` emits JSON only when every required answer is present and the
  existing Phase4 verifier accepts the exact candidate hashes.

This module never opens source images, masks, labels, previews, or NPZ files.
It cannot invent a reviewer signature and cannot promote Phase5, Golden, or
production.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

try:  # Works both as a package import and as a direct research script.
    from .verify_local_l02_phase4_receipt import (
        CASES,
        SOURCE_SHA256,
        Phase4ReceiptHold,
        verify_phase4_receipt,
    )
except ImportError:  # pragma: no cover - exercised by direct CLI execution.
    from verify_local_l02_phase4_receipt import (  # type: ignore
        CASES,
        SOURCE_SHA256,
        Phase4ReceiptHold,
        verify_phase4_receipt,
    )


FORM_SCHEMA = "minimalizer/local-l02/phase4-review-form/v1"
RECEIPT_SCHEMA = "minimalizer/l02/phase4-independent-review/v1"
UNANSWERED = "UNANSWERED"
GLOBAL_FIELDS = (
    "signature_verified",
    "unseen_data",
    "labels_unavailable_before_inference",
    "evaluator_independent",
    "semantic_review_complete",
    "unknown_mask_is_unknown",
    "human_masks_used_in_inference",
    "review_json_used_in_inference",
    "output_frozen_before_scoring",
)
CASE_FIELDS = (
    "source_sha_verified",
    "candidate_sha_verified",
    "correct_garment_preserved",
    "wrong_owner_removed_only_where_justified",
    "sleeve_recovery_owner_exclusive",
    "occlusion_and_critical_parts_preserved",
    "visual_regression_acceptable",
    "change_visibility_sufficient",
    "unknown_not_negative",
)


class Phase4PreparationHold(ValueError):
    """The form cannot be safely materialized into a Phase4 receipt."""


def _load_json(path: Path) -> Mapping[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise Phase4PreparationHold("FREEZE_ROOT_NOT_OBJECT")
    return value


def _candidate_hashes(freeze_receipt: Mapping[str, object]) -> dict[str, str]:
    cases = freeze_receipt.get("cases")
    if not isinstance(cases, Mapping):
        raise Phase4PreparationHold("FREEZE_CASES_MISSING")
    result: dict[str, str] = {}
    for case in CASES:
        item = cases.get(case)
        if not isinstance(item, Mapping):
            raise Phase4PreparationHold(f"FREEZE_CASE_MISSING:{case}")
        value = item.get("candidate_array_sha256")
        if not isinstance(value, str) or len(value) != 64:
            raise Phase4PreparationHold(f"FREEZE_CANDIDATE_SHA_INVALID:{case}")
        result[case] = value.lower()
    return result


def render_review_form(freeze_receipt: Mapping[str, object]) -> str:
    """Return a plain-text form whose candidate hashes come from ``freeze``."""
    hashes = _candidate_hashes(freeze_receipt)
    lines = [
        "L02 candidate-specific Phase4 independent review form",
        f"form_schema: {FORM_SCHEMA}",
        "",
        "# Reviewer fills the blank fields after inspecting the frozen candidate.",
        "# Use YES or NO for boolean fields. Do not use labels as inference input.",
        "# Keep visual regression and change visibility as separate decisions.",
        "reviewer_id:",
        "reviewed_at_utc:",
        "signature_record:",
    ]
    for field in GLOBAL_FIELDS:
        lines.append(f"{field}: {UNANSWERED}")
    for case in CASES:
        lines.extend(
            [
                "",
                f"[{case}]",
                f"source_sha256: {SOURCE_SHA256[case]}",
                f"candidate_sha256: {hashes[case]}",
            ]
        )
        for field in CASE_FIELDS:
            lines.append(f"{field}: {UNANSWERED}")
        lines.append("reviewer_comment:")
    lines.extend(
        [
            "",
            "# The materializer computes phase4=PASS only after every required field is YES",
            "# and the candidate hashes match this freeze receipt exactly.",
        ]
    )
    return "\n".join(lines) + "\n"


def _parse_lines(form_text: str) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    global_values: dict[str, str] = {}
    case_values: dict[str, dict[str, str]] = {}
    current_case: str | None = None
    for raw_line in form_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("L02 "):
            continue
        if line.startswith("form_schema:"):
            if line.split(":", 1)[1].strip() != FORM_SCHEMA:
                raise Phase4PreparationHold("FORM_SCHEMA_MISMATCH")
            continue
        if line.startswith("[") and line.endswith("]"):
            current_case = line[1:-1]
            if current_case not in CASES:
                raise Phase4PreparationHold(f"UNKNOWN_CASE:{current_case}")
            case_values[current_case] = {}
            continue
        if ":" not in line:
            raise Phase4PreparationHold("MALFORMED_FORM_LINE")
        key, value = (part.strip() for part in line.split(":", 1))
        target = case_values[current_case] if current_case else global_values
        target[key] = value
    return global_values, case_values


def _flag(value: str | None, field: str) -> bool:
    if value == "YES":
        return True
    if value == "NO":
        return False
    raise Phase4PreparationHold(f"UNANSWERED_OR_INVALID:{field}")


def materialize_receipt(
    form_text: str, freeze_receipt: Mapping[str, object]
) -> dict[str, object]:
    """Build and verify a Phase4 receipt; never return a failed receipt."""
    global_values, case_values = _parse_lines(form_text)
    reviewer_id = global_values.get("reviewer_id", "").strip()
    reviewed_at_utc = global_values.get("reviewed_at_utc", "").strip()
    signature_record = global_values.get("signature_record", "").strip()
    if not reviewer_id:
        raise Phase4PreparationHold("REVIEWER_ID_MISSING")
    if not reviewed_at_utc:
        raise Phase4PreparationHold("REVIEW_TIMESTAMP_MISSING")
    if not signature_record:
        raise Phase4PreparationHold("SIGNATURE_RECORD_MISSING")

    expected_hashes = _candidate_hashes(freeze_receipt)
    receipt: dict[str, object] = {
        "schema": RECEIPT_SCHEMA,
        "phase4": "PASS",
        "reviewer_id": reviewer_id,
        "reviewed_at_utc": reviewed_at_utc,
        "signature_record": signature_record,
        "signature_verified": _flag(global_values.get("signature_verified"), "signature_verified"),
        "unseen_data": _flag(global_values.get("unseen_data"), "unseen_data"),
        "labels_unavailable_before_inference": _flag(
            global_values.get("labels_unavailable_before_inference"),
            "labels_unavailable_before_inference",
        ),
        "evaluator_independent": _flag(
            global_values.get("evaluator_independent"), "evaluator_independent"
        ),
        "semantic_review_complete": _flag(
            global_values.get("semantic_review_complete"), "semantic_review_complete"
        ),
        "unknown_mask_is_unknown": _flag(
            global_values.get("unknown_mask_is_unknown"), "unknown_mask_is_unknown"
        ),
        "human_masks_used_in_inference": _flag(
            global_values.get("human_masks_used_in_inference"),
            "human_masks_used_in_inference",
        ),
        "review_json_used_in_inference": _flag(
            global_values.get("review_json_used_in_inference"),
            "review_json_used_in_inference",
        ),
        "output_frozen_before_scoring": _flag(
            global_values.get("output_frozen_before_scoring"),
            "output_frozen_before_scoring",
        ),
        "cases": {},
    }
    for case in CASES:
        values = case_values.get(case)
        if values is None:
            raise Phase4PreparationHold(f"CASE_MISSING:{case}")
        candidate_hash = values.get("candidate_sha256", "").lower()
        if candidate_hash != expected_hashes[case]:
            raise Phase4PreparationHold(f"CANDIDATE_SHA_MISMATCH:{case}")
        case_receipt: dict[str, object] = {
            "source_sha256": SOURCE_SHA256[case],
            "candidate_sha256": candidate_hash,
        }
        for field in CASE_FIELDS:
            case_receipt[field] = _flag(values.get(field), f"{case}:{field}")
        receipt["cases"][case] = case_receipt  # type: ignore[index]

    try:
        verification = verify_phase4_receipt(receipt, freeze_receipt)
    except Phase4ReceiptHold as exc:
        raise Phase4PreparationHold("VERIFIER_HOLD:" + ",".join(exc.failures)) from exc
    receipt["phase5"] = verification["phase5"]
    receipt["golden"] = verification["golden"]
    receipt["production"] = verification["production"]
    receipt["verification"] = verification
    return receipt


def _cli() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a human-readable form")
    init.add_argument("--freeze", type=Path, required=True)
    init.add_argument("--output", type=Path, required=True)

    materialize = sub.add_parser("materialize", help="emit JSON after a passing review")
    materialize.add_argument("--freeze", type=Path, required=True)
    materialize.add_argument("--form", type=Path, required=True)
    materialize.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        freeze = _load_json(args.freeze)
        if args.command == "init":
            args.output.write_text(render_review_form(freeze), encoding="utf-8")
            print(f"FORM_CREATED {args.output}")
            return 0
        receipt = materialize_receipt(args.form.read_text(encoding="utf-8"), freeze)
        args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"PHASE4_RECEIPT_CREATED {args.output}")
        return 0
    except (OSError, json.JSONDecodeError, Phase4PreparationHold) as exc:
        print(f"HOLD {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
