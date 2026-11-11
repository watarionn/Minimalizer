"""Fail-closed preflight for candidate-bound L02 Phase5 inputs.

The current Phase4 receipt is not enough to run Phase5.  Phase5 needs a
complete, source-bound Phase4 part-mask bundle for each case.  This audit
refuses to reuse an old L04/Stage8 directory unless its stage metadata binds
the exact current candidate SHA.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping


CASES = ("H04", "H06", "H08")
PARTS = (
    "head",
    "hair",
    "face",
    "neck",
    "torso",
    "left_arm",
    "right_arm",
    "lower_body",
    "major_clothing",
    "accessory_or_held_object",
    "unknown",
)


class Phase5InputHold(ValueError):
    """The current candidate lacks a safe Phase5 input bundle."""


def _json(path: Path) -> Mapping[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise Phase5InputHold(f"JSON_ROOT_NOT_OBJECT:{path.name}")
    return value


def _receipt_cases(receipt: Mapping[str, object]) -> Mapping[str, object]:
    if receipt.get("phase4") != "PASS":
        raise Phase5InputHold("PHASE4_NOT_PASS")
    cases = receipt.get("cases")
    if not isinstance(cases, Mapping):
        raise Phase5InputHold("PHASE4_CASES_MISSING")
    return cases


def audit_phase5_input(receipt: Mapping[str, object], root: Path) -> dict[str, object]:
    cases = _receipt_cases(receipt)
    failures: list[str] = []
    reports: dict[str, dict[str, object]] = {}
    for case in CASES:
        review_case = cases.get(case)
        if not isinstance(review_case, Mapping):
            failures.append(f"{case}:PHASE4_CASE_MISSING")
            continue
        candidate_sha = review_case.get("candidate_sha256")
        source_sha = review_case.get("source_sha256")
        phase4_dir = root / case / "phase_04"
        part_dir = phase4_dir / "part_masks"
        missing = [
            str(path.relative_to(root))
            for path in (phase4_dir / "stage.json", phase4_dir / "metrics.json")
            if not path.is_file()
        ]
        missing.extend(
            str((part_dir / f"{part}.png").relative_to(root))
            for part in PARTS
            if not (part_dir / f"{part}.png").is_file()
        )
        case_failures: list[str] = []
        if missing:
            case_failures.append("PHASE4_PART_MASK_BUNDLE_MISSING")
        stage: Mapping[str, object] = {}
        if (phase4_dir / "stage.json").is_file():
            stage = _json(phase4_dir / "stage.json")
            source = stage.get("source")
            if not isinstance(source, Mapping) or source.get("sha256") != source_sha:
                case_failures.append("SOURCE_SHA_NOT_BOUND_IN_PHASE4_STAGE")
            binding = stage.get("l02_candidate")
            if not isinstance(binding, Mapping) or binding.get("candidate_sha256") != candidate_sha:
                case_failures.append("CURRENT_CANDIDATE_NOT_BOUND_IN_PHASE4_STAGE")
        failures.extend(f"{case}:{failure}" for failure in case_failures)
        reports[case] = {
            "phase4_dir": str(phase4_dir),
            "candidate_sha256": candidate_sha,
            "source_sha256": source_sha,
            "missing": missing,
            "failures": case_failures,
        }
    return {
        "schema": "minimalizer/local-l02/phase5-input-audit/v1",
        "phase4": "PASS",
        "phase5_input": "READY" if not failures else "HOLD",
        "phase5": "READY" if not failures else "NO_GO",
        "failures": failures,
        "cases": reports,
        "old_stage8_reuse": False,
    }


def _cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase4-receipt", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit_phase5_input(_json(args.phase4_receipt), args.root)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"phase5_input": result["phase5_input"], "failures": result["failures"]}, ensure_ascii=False))
        return 0 if result["phase5_input"] == "READY" else 1
    except (OSError, json.JSONDecodeError, Phase5InputHold) as exc:
        print(f"HOLD {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
