"""Fail-closed preflight for candidate-bound L02 Phase5 inputs.

The current Phase4 receipt is not enough to run Phase5.  Phase5 needs a
complete, source-bound Phase4 part-mask bundle for each case.  This audit
refuses to reuse an old L04/Stage8 directory unless its stage metadata binds
the exact current candidate SHA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _png_size(path: Path) -> tuple[int, int]:
    """Read the PNG signature/IHDR without trusting a filename or decoder."""
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise Phase5InputHold(f"PART_MASK_NOT_PNG:{path.name}")
    if header[12:16] != b"IHDR":
        raise Phase5InputHold(f"PART_MASK_IHDR_MISSING:{path.name}")
    width, height = struct.unpack(">II", header[16:24])
    if width == 0 or height == 0:
        raise Phase5InputHold(f"PART_MASK_EMPTY_DIMENSION:{path.name}")
    return width, height


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
        metrics: Mapping[str, object] = {}
        if (phase4_dir / "stage.json").is_file():
            stage = _json(phase4_dir / "stage.json")
            source = stage.get("source")
            if not isinstance(source, Mapping) or source.get("sha256") != source_sha:
                case_failures.append("SOURCE_SHA_NOT_BOUND_IN_PHASE4_STAGE")
            binding = stage.get("l02_candidate")
            if not isinstance(binding, Mapping) or binding.get("candidate_sha256") != candidate_sha:
                case_failures.append("CURRENT_CANDIDATE_NOT_BOUND_IN_PHASE4_STAGE")
            source_width = source.get("width") if isinstance(source, Mapping) else None
            source_height = source.get("height") if isinstance(source, Mapping) else None
            if not isinstance(source_width, int) or not isinstance(source_height, int):
                case_failures.append("SOURCE_DIMENSIONS_MISSING")
            outputs = stage.get("outputs")
            if not isinstance(outputs, Mapping):
                case_failures.append("PHASE4_OUTPUT_MANIFEST_MISSING")
            else:
                metrics_path = phase4_dir / "metrics.json"
                recorded_metrics_sha = outputs.get("metrics.json")
                if not isinstance(recorded_metrics_sha, str) or not metrics_path.is_file():
                    case_failures.append("METRICS_OUTPUT_NOT_BOUND")
                elif _sha256(metrics_path) != recorded_metrics_sha:
                    case_failures.append("METRICS_SHA_MISMATCH")
                for part in PARTS:
                    relative = f"part_masks/{part}.png"
                    path = part_dir / f"{part}.png"
                    recorded_sha = outputs.get(relative)
                    if not isinstance(recorded_sha, str):
                        case_failures.append(f"PART_MASK_SHA_MISSING:{part}")
                        continue
                    if not path.is_file():
                        continue
                    try:
                        width, height = _png_size(path)
                    except (OSError, Phase5InputHold) as exc:
                        case_failures.append(str(exc))
                        continue
                    if (width, height) != (source_width, source_height):
                        case_failures.append(f"PART_MASK_DIMENSION_MISMATCH:{part}")
                    if _sha256(path) != recorded_sha:
                        case_failures.append(f"PART_MASK_SHA_MISMATCH:{part}")
        metrics_path = phase4_dir / "metrics.json"
        if metrics_path.is_file():
            try:
                metrics = _json(metrics_path)
            except (OSError, json.JSONDecodeError, Phase5InputHold):
                case_failures.append("METRICS_NOT_OBJECT")
        failures.extend(f"{case}:{failure}" for failure in case_failures)
        reports[case] = {
            "phase4_dir": str(phase4_dir),
            "candidate_sha256": candidate_sha,
            "source_sha256": source_sha,
            "missing": missing,
            "failures": case_failures,
            "metrics_keys": sorted(metrics),
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
