"""Run the source-free MinimalizerLocal completion gate from receipt files.

This adapter reads JSON receipts only.  It never opens images, masks, NPZs,
SVGs, device captures, or private Drive files.  Missing, malformed, or
non-object receipts are converted into a fail-closed HOLD result so the owner
can use the same command before and after the missing A-lane inputs arrive.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Mapping

from tools.research.local_completion_release_gate import (
    EXPECTED_CANDIDATE_RECEIPT_SHA256,
    EXPECTED_PRODUCTION_WORKER_COMMIT,
    assess_release_binding,
)


RECEIPT_NAMES = (
    "a",
    "phase4",
    "phase5",
    "l04",
    "l05",
    "l07",
    "acceptance",
    "regression",
    "preservation",
)


class CompletionReceiptHold(ValueError):
    """A receipt file could not be read as a source-free object."""


def _load_mapping(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CompletionReceiptHold(f"{label} receipt read failed:{type(exc).__name__}") from exc
    if not isinstance(value, Mapping):
        raise CompletionReceiptHold(f"{label} receipt root is not an object")
    return value


def audit_receipt_paths(
    *,
    candidate_receipt_sha256: str,
    production_worker_commit: str,
    receipt_paths: Mapping[str, str | Path],
    owner_action_required: bool,
) -> dict[str, Any]:
    """Load nine source-free receipts and return the fail-closed assessment."""
    missing = tuple(name for name in RECEIPT_NAMES if name not in receipt_paths)
    if missing:
        return {
            "status": "HOLD",
            "release_authorized": False,
            "failures": tuple(f"missing receipt path:{name}" for name in missing),
        }
    try:
        payloads = {
            name: _load_mapping(Path(receipt_paths[name]), name)
            for name in RECEIPT_NAMES
        }
    except CompletionReceiptHold as exc:
        return {
            "status": "HOLD",
            "release_authorized": False,
            "failures": (str(exc),),
        }
    result = assess_release_binding(
        candidate_receipt_sha256=candidate_receipt_sha256,
        production_worker_commit=production_worker_commit,
        a=payloads["a"],
        phase4=payloads["phase4"],
        phase5=payloads["phase5"],
        l04=payloads["l04"],
        l05=payloads["l05"],
        l07=payloads["l07"],
        acceptance=payloads["acceptance"],
        regression=payloads["regression"],
        preservation=payloads["preservation"],
        owner_action_required=owner_action_required,
    )
    return asdict(result)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit MinimalizerLocal completion from source-free receipts."
    )
    parser.add_argument("--candidate", default=EXPECTED_CANDIDATE_RECEIPT_SHA256)
    parser.add_argument("--worker", default=EXPECTED_PRODUCTION_WORKER_COMMIT)
    parser.add_argument("--owner-action-required", action="store_true")
    for name in RECEIPT_NAMES:
        parser.add_argument(f"--{name}", dest=name, type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    receipt_paths = {name: getattr(args, name) for name in RECEIPT_NAMES}
    result = audit_receipt_paths(
        candidate_receipt_sha256=args.candidate,
        production_worker_commit=args.worker,
        receipt_paths=receipt_paths,
        owner_action_required=args.owner_action_required,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
