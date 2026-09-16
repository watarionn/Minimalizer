from __future__ import annotations

import argparse
import json
from pathlib import Path

from minimalize_engine.v2 import build_migration_readiness


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report Minimalizer V2 default-migration readiness."
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_migration_readiness().to_dict()
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(text, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
