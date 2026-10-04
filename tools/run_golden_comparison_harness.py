from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.golden_comparison.harness import (
    GoldenHarnessError,
    canonical_report_json,
    verify_case,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a SHA-bound Golden Comparison triplet.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--asset-dir", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = verify_case(args.manifest, args.asset_dir)
    except GoldenHarnessError as exc:
        print(json.dumps({"gate": "FAIL", "error": str(exc)}, sort_keys=True))
        return 2
    raw = canonical_report_json(report) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
