"""Prepare a candidate-bound H08 owner-authority receipt.

This is a source-free governance receipt.  It binds the explicit owner
approval to the exact H08 signed source, frozen owner, candidate owner, and
observer output.  It never opens images, masks, labels, or NPZ arrays and it
never authorizes production or Golden promotion.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Mapping


FORM_SCHEMA = "minimalizer/local-l02/h08-owner-authority-form/v1"
RECEIPT_SCHEMA = "minimalizer/local-l02/h08-owner-authority/v1"
SOURCE_SHA256 = "759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e"
FROZEN_OWNER_SHA256 = "43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52"
CANDIDATE_SHA256 = "8daafac9aabac48635d73b393a8220dd64f88b3a2ef6d7c06ae76b52b049f091"
OBSERVER_SHA256 = "e3d54bea29d1569e16b2aa18e4a6bd34c37d76530449c73114e5511b3b3e4423"
BOOLEAN_FIELDS = (
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


class H08AuthorityHold(ValueError):
    """The owner-authority form is incomplete or not candidate-bound."""


def _timestamp(value: str) -> bool:
    try:
        return bool(value) and datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def render_authority_form() -> str:
    lines = [
        "H08 candidate-bound owner-authority form",
        f"form_schema: {FORM_SCHEMA}",
        "",
        "# 人間はJSONを書かない。このフォームだけを記入する。",
        "# owner_id / approved_at_utc / approval_record は文字列、それ以外は YES または NO。",
        "case: H08",
        f"source_sha256: {SOURCE_SHA256}",
        f"frozen_owner_sha256: {FROZEN_OWNER_SHA256}",
        f"candidate_sha256: {CANDIDATE_SHA256}",
        f"observer_sha256: {OBSERVER_SHA256}",
        "owner_id:",
        "approved_at_utc:",
        "approval_record:",
    ]
    lines.extend(f"{field}: UNANSWERED" for field in BOOLEAN_FIELDS)
    lines.extend(
        [
            "",
            "# このreceiptはH08候補のowner遷移だけを認可する。Production/Goldenは認可しない。",
        ]
    )
    return "\n".join(lines) + "\n"


def _parse(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("H08 "):
            continue
        if ":" not in line:
            raise H08AuthorityHold("MALFORMED_FORM_LINE")
        key, value = (part.strip() for part in line.split(":", 1))
        values[key] = value
    return values


def _flag(values: Mapping[str, str], field: str) -> bool:
    value = values.get(field)
    if value == "YES":
        return True
    if value == "NO":
        return False
    raise H08AuthorityHold(f"UNANSWERED_OR_INVALID:{field}")


def materialize_authority_receipt(form_text: str) -> dict[str, object]:
    values = _parse(form_text)
    if values.get("case") != "H08":
        raise H08AuthorityHold("CASE_MISMATCH")
    if values.get("source_sha256") != SOURCE_SHA256:
        raise H08AuthorityHold("SOURCE_SHA_MISMATCH")
    if values.get("frozen_owner_sha256") != FROZEN_OWNER_SHA256:
        raise H08AuthorityHold("FROZEN_OWNER_SHA_MISMATCH")
    if values.get("candidate_sha256") != CANDIDATE_SHA256:
        raise H08AuthorityHold("CANDIDATE_SHA_MISMATCH")
    if values.get("observer_sha256") != OBSERVER_SHA256:
        raise H08AuthorityHold("OBSERVER_SHA_MISMATCH")
    for field in ("owner_id", "approved_at_utc", "approval_record"):
        if not values.get(field):
            raise H08AuthorityHold(f"{field.upper()}_MISSING")
    if not _timestamp(values["approved_at_utc"]):
        raise H08AuthorityHold("APPROVAL_TIMESTAMP_INVALID")
    flags = {field: _flag(values, field) for field in BOOLEAN_FIELDS}
    if not all(flags.values()):
        failed = [field for field, value in flags.items() if not value]
        raise H08AuthorityHold("AUTHORITY_HOLD:" + ",".join(failed))
    return {
        "schema": RECEIPT_SCHEMA,
        "case": "H08",
        "owner_id": values["owner_id"],
        "approved_at_utc": values["approved_at_utc"],
        "approval_record": values["approval_record"],
        "source_sha256": SOURCE_SHA256,
        "frozen_owner_sha256": FROZEN_OWNER_SHA256,
        "prediction_sha256": CANDIDATE_SHA256,
        "observer_sha256": OBSERVER_SHA256,
        "owner_promotion_authorized": True,
        **flags,
        "golden": "HOLD",
        "production": "NO_GO",
    }


def _cli() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--output", type=Path, required=True)
    materialize = sub.add_parser("materialize")
    materialize.add_argument("--form", type=Path, required=True)
    materialize.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            args.output.write_text(render_authority_form(), encoding="utf-8")
            print(f"FORM_CREATED {args.output}")
        else:
            receipt = materialize_authority_receipt(args.form.read_text(encoding="utf-8"))
            args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"H08_AUTHORITY_RECEIPT_CREATED {args.output}")
        return 0
    except (OSError, H08AuthorityHold) as exc:
        print(f"HOLD {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
