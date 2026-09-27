from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from minimalizer_zerobase.evaluation import MigrationGate

def main() -> int:
    docs = ROOT / "docs" / "zerobase"
    capture = json.loads((docs / "MIGRATION_APPROVED78_CAPTURE.json").read_text(encoding="utf-8"))
    comparison = json.loads((docs / "MIGRATION_APPROVED78_COMPARISON.json").read_text(encoding="utf-8"))
    result = MigrationGate().evaluate(capture, comparison)
    out = docs / "MIGRATION_GATE.json"
    out.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0 if result.switch_authorized else 2

if __name__ == "__main__":
    raise SystemExit(main())
