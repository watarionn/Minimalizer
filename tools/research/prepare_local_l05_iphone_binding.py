"""Prepare a source-free current-Worker binding from a fresh iPhone receipt.

The raw receipt remains private.  The generated JSON contains only the fixed
candidate/Worker SHAs and the raw receipt SHA.  A stale iPhone receipt is
rejected before a binding file is written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.research.audit_local_l05_current_worker_binding import (  # noqa: E402
    BINDING_SCHEMA,
    CurrentWorkerBindingHold,
    audit_current_worker_binding,
)
from tools.research.local_completion_release_gate import (  # noqa: E402
    EXPECTED_CANDIDATE_RECEIPT_SHA256,
    EXPECTED_PRODUCTION_WORKER_COMMIT,
)


def prepare_iphone_binding(receipt: Mapping[str, Any], raw: bytes) -> dict[str, str]:
    """Validate a fresh iPhone receipt and return its source-free binding."""
    source_sha = hashlib.sha256(raw).hexdigest()
    binding = {
        "schema": BINDING_SCHEMA,
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "production_worker_commit": EXPECTED_PRODUCTION_WORKER_COMMIT,
        "source_receipt_sha256": source_sha,
    }
    result = audit_current_worker_binding(receipt, binding, source_sha)
    if result.get("device") != "iphone" or result.get("status") != "PASS":
        raise CurrentWorkerBindingHold("IPHONE_BINDING_NOT_PASS")
    return binding


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Prepare current-Worker iPhone receipt binding")
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        raw = args.receipt.read_bytes()
        receipt = json.loads(raw.decode("utf-8"))
        if not isinstance(receipt, Mapping):
            raise CurrentWorkerBindingHold("RECEIPT_ROOT_NOT_OBJECT")
        binding = prepare_iphone_binding(receipt, raw)
        args.output.write_text(json.dumps(binding, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "source_receipt_sha256": binding["source_receipt_sha256"]}))
        return 0
    except (CurrentWorkerBindingHold, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "HOLD", "failure": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
