from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_closure(
    diagnostic2_path: Path,
    approved18_path: Path,
    approved78_path: Path,
) -> dict[str, Any]:
    diagnostic2 = _load(diagnostic2_path)
    approved18 = _load(approved18_path)
    approved78 = _load(approved78_path)

    diagnostic2_pass = bool(
        diagnostic2.get("pass")
        and int(diagnostic2.get("case_count", 0)) == 2
        and int(diagnostic2.get("human_visual_pass_count", 0)) == 2
        and int(diagnostic2.get("determinism_pass_count", 0)) == 2
    )
    approved18_pass = bool(
        approved18.get("pass")
        and int(approved18.get("case_count", 0)) == 18
        and int(approved18.get("input_sha_pass_count", 0)) == 18
        and int(approved18.get("approved_sha_pass_count", 0)) == 18
        and int(approved18.get("structural_gate_pass_count", 0)) == 18
    )
    approved78_pass = bool(
        approved78.get("pass")
        and approved78.get("replay_complete")
        and int(
            approved78.get("binding", {}).get("reference_count", 0)
        )
        == 78
        and approved78.get("migration_gate_pass")
    )
    overall = diagnostic2_pass and approved18_pass and approved78_pass

    return {
        "schema_version": "1.0",
        "phase": 14,
        "stage": "evaluation_redesign_calibration_closure",
        "pass": overall,
        "gates": {
            "diagnostic2_zero_base_visual": {
                "pass": diagnostic2_pass,
                "case_count": diagnostic2.get("case_count"),
                "human_visual_pass_count": diagnostic2.get(
                    "human_visual_pass_count"
                ),
                "determinism_pass_count": diagnostic2.get(
                    "determinism_pass_count"
                ),
                "role": (
                    "Primary ZeroBase2 machine + human visual quality Gate."
                ),
            },
            "approved18_production_regression": {
                "pass": approved18_pass,
                "case_count": approved18.get("case_count"),
                "input_sha_pass_count": approved18.get(
                    "input_sha_pass_count"
                ),
                "approved_sha_pass_count": approved18.get(
                    "approved_sha_pass_count"
                ),
                "structural_gate_pass_count": approved18.get(
                    "structural_gate_pass_count"
                ),
                "diagnostics": approved18.get("diagnostics", {}),
                "role": (
                    "Existing production approved_reference regression Gate. "
                    "It proves the legacy production regression contract did "
                    "not break; it is not treated as visual equivalence to the "
                    "Approved images and does not replace Diagnostic-2 human QA."
                ),
            },
            "approved78_formal_migration": {
                "pass": approved78_pass,
                "reference_count": approved78.get("binding", {}).get(
                    "reference_count"
                ),
                "replay_complete": approved78.get("replay_complete"),
                "migration_gate_pass": approved78.get(
                    "migration_gate_pass"
                ),
                "migration_reasons": approved78.get(
                    "migration_gate", {}
                ).get("reasons", []),
                "calibration_diagnostic": approved78.get(
                    "calibration_diagnostic", {}
                ),
                "role": (
                    "Formal SHA-bound deterministic non-regression "
                    "MigrationGate over Approved-78."
                ),
            },
        },
        "inputs": {
            "diagnostic2": {
                "path": str(diagnostic2_path),
                "sha256": _sha(diagnostic2_path),
            },
            "approved18": {
                "path": str(approved18_path),
                "sha256": _sha(approved18_path),
            },
            "approved78": {
                "path": str(approved78_path),
                "sha256": _sha(approved78_path),
            },
        },
        "failure_policy": (
            "Phase 14 closes only if Diagnostic-2 machine/human/determinism, "
            "Approved-18 production regression, and Approved-78 formal "
            "MigrationGate all pass. Any disagreement or failure wins."
        ),
        "next_phase_authorized": 15 if overall else None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the ZeroBase 2nd Cycle Phase 14 closure Gate."
    )
    parser.add_argument(
        "--diagnostic2",
        type=Path,
        default=(
            ROOT
            / "artifacts"
            / "phase14_diagnostic2"
            / "14_corpus_summary.json"
        ),
    )
    parser.add_argument(
        "--approved18",
        type=Path,
        default=(
            ROOT
            / "artifacts"
            / "phase14_approved18"
            / "14_approved18_regression_gate.json"
        ),
    )
    parser.add_argument(
        "--approved78",
        type=Path,
        default=(
            ROOT
            / "artifacts"
            / "phase14_approved78"
            / "14_approved78_formal_gate.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "artifacts"
            / "phase14_closure"
            / "14_phase_gate_summary.json"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_closure(
        args.diagnostic2,
        args.approved18,
        args.approved78,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "pass": result["pass"],
                "next_phase_authorized": result["next_phase_authorized"],
                "gates": {
                    key: value["pass"]
                    for key, value in result["gates"].items()
                },
                "output": str(args.output),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
