from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.production import (
    ZEROBASE2_ROUTE,
    ProductionRouteSwitch,
    compare_production_output,
    load_phase14_closure,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 15 production integration gate."
    )
    parser.add_argument(
        "--phase14-closure", type=Path,
        default=ROOT / "artifacts" / "phase14_closure" / "14_phase_gate_summary.json",
    )
    parser.add_argument("--development-output", type=Path)
    parser.add_argument("--production-output", type=Path)
    parser.add_argument("--development-metadata", type=Path)
    parser.add_argument("--production-metadata", type=Path)
    parser.add_argument("--browser-smoke", type=Path)
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "artifacts" / "phase15_production" / "15_production_gate.json",
    )
    return parser.parse_args()


def _json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def main() -> int:
    args = parse_args()
    closure = load_phase14_closure(args.phase14_closure)
    switch = ProductionRouteSwitch(ZEROBASE2_ROUTE).decide(closure)
    compare = None
    compare_args = (
        args.development_output,
        args.production_output,
        args.development_metadata,
        args.production_metadata,
    )
    if any(value is not None for value in compare_args):
        if not all(value is not None for value in compare_args):
            raise ValueError("production comparison requires all four output/metadata paths")
        compare = compare_production_output(
            args.development_output,
            args.production_output,
            _json(args.development_metadata),
            _json(args.production_metadata),
        )

    browser_smoke = _json(args.browser_smoke) if args.browser_smoke else None
    browser_smoke_pass = bool(
        browser_smoke
        and browser_smoke.get("pass") is True
        and browser_smoke.get("route") == ZEROBASE2_ROUTE
    )
    final_gate_pass = bool(
        switch.active_route == ZEROBASE2_ROUTE
        and switch.zerobase_authorized
        and switch.rollback_available
        and compare is not None
        and compare["pass"]
    )

    result = {
        "schema_version": "1.0",
        "phase": 15,
        "stage": "production_integration_gate",
        "route_switch": switch.to_dict(),
        "phase14_closure_pass": bool(closure.get("pass")),
        "production_compare": compare,
        "browser_smoke": browser_smoke,
        "integration_contract_pass": bool(
            switch.active_route == ZEROBASE2_ROUTE
            and switch.zerobase_authorized
            and switch.rollback_available
        ),
        "final_gate_pass": final_gate_pass,
        "migration_closed": bool(final_gate_pass and browser_smoke_pass),
        "remaining_gate": (
            None if final_gate_pass and browser_smoke_pass
            else "real-browser production smoke is required before MIGRATION CLOSED"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["integration_contract_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
