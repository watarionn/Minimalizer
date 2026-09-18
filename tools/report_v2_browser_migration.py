from __future__ import annotations

import argparse
import json
from pathlib import Path

from minimalize_engine.v2 import (
    build_browser_migration_contract,
    build_migration_readiness,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report V2 browser migration/rollback contract and readiness."
    )
    parser.add_argument("--contract-output", type=Path, required=True)
    parser.add_argument("--readiness-output", type=Path, required=True)
    args = parser.parse_args()
    contract = build_browser_migration_contract().to_dict()
    readiness = build_migration_readiness().to_dict()
    for path, payload in (
        (args.contract_output, contract),
        (args.readiness_output, readiness),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(args.contract_output.resolve())
    print(args.readiness_output.resolve())
    print(readiness["blocker_count"], readiness["blocker_ids"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
