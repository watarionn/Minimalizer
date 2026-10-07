from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.evaluation.regression_transaction import (
    build_regression_transaction,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transaction-id", required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--adoption-record", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--visual-hard-gate", type=Path, required=True)
    parser.add_argument("--hard-evidence", type=Path, required=True)
    parser.add_argument("--phase14", type=Path, required=True)
    parser.add_argument("--semantic-retention", type=Path, required=True)
    parser.add_argument("--face-raster-guard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = build_regression_transaction(
        transaction_id=args.transaction_id,
        case=_load(args.case),
        adoption_record=_load(args.adoption_record),
        actual_source_sha256=_sha256(args.source),
        actual_candidate_sha256=_sha256(args.candidate),
        visual_hard_gate=_load(args.visual_hard_gate),
        hard_evidence=_load(args.hard_evidence),
        phase14=_load(args.phase14),
        semantic_retention=_load(args.semantic_retention),
        face_raster_guard=_load(args.face_raster_guard),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    args.output.write_bytes(payload)
    print(hashlib.sha256(payload).hexdigest())
    return 0 if report.pass_transaction else 2


if __name__ == "__main__":
    raise SystemExit(main())
