from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.evaluation import write_phase14_corpus_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate Phase 14 case evaluations into a corpus Gate summary."
    )
    parser.add_argument(
        "--case-dir",
        action="append",
        required=True,
        type=Path,
        dest="case_dirs",
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--corpus-name", required=True)
    parser.add_argument("--required-case-count", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = write_phase14_corpus_summary(
        args.case_dirs,
        args.output,
        corpus_name=args.corpus_name,
        required_case_count=args.required_case_count,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
