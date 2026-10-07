from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

SA10_CROSS_CASE_VERSION = "sa10.8-v1"

DIAGNOSTIC_NAMES = (
    "semantic_retention",
    "adaptive_complexity",
    "component_survival",
    "primitive_economy",
    "teacher_coverage",
    "teacher_primitive_disagreements",
)

HARD_EVIDENCE_NAMES = (
    "feature_survival",
    "forbidden_face_detail",
    "anatomy",
    "topology",
    "source_authority",
    "phase14_machine",
    "phase14_human_visual",
    "determinism",
)


def _validate_diagnostic(name: str, row: Mapping[str, Any]) -> dict[str, Any]:
    status = row.get("status")
    if status not in {"AVAILABLE", "UNAVAILABLE"}:
        raise ValueError(f"{name}: invalid status")
    if status == "UNAVAILABLE":
        reason = row.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"{name}: unavailable diagnostic requires reason")
        return {"name": name, "status": status, "value": None, "reason": reason}

    value = row.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: available diagnostic requires numeric value")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name}: diagnostic value must be finite")
    if name == "teacher_primitive_disagreements":
        if value < 0:
            raise ValueError(f"{name}: disagreement count cannot be negative")
    elif not 0.0 <= value <= 1.0:
        raise ValueError(f"{name}: ratio diagnostic must be within [0, 1]")
    return {"name": name, "status": status, "value": value, "reason": None}


def _validate_hard_evidence(name: str, row: Mapping[str, Any]) -> dict[str, Any]:
    status = row.get("status")
    if status not in {"AVAILABLE", "UNAVAILABLE"}:
        raise ValueError(f"{name}: invalid hard-evidence status")
    if status == "UNAVAILABLE":
        reason = row.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"{name}: unavailable hard evidence requires reason")
        return {"name": name, "status": status, "passed": None, "reason": reason}
    passed = row.get("passed")
    if not isinstance(passed, bool):
        raise ValueError(f"{name}: available hard evidence requires bool passed")
    return {"name": name, "status": status, "passed": passed, "reason": None}


def _normalize_case(case: Mapping[str, Any]) -> dict[str, Any]:
    case_id = case.get("case_id")
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("case_id is required")

    diagnostics_in = case.get("diagnostics", {})
    if set(diagnostics_in) != set(DIAGNOSTIC_NAMES):
        raise ValueError(f"{case_id}: diagnostics must contain the six SA10 names")
    diagnostics = [
        _validate_diagnostic(name, diagnostics_in[name])
        for name in DIAGNOSTIC_NAMES
    ]

    hard_in = case.get("hard_evidence", {})
    if set(hard_in) != set(HARD_EVIDENCE_NAMES):
        raise ValueError(f"{case_id}: hard_evidence must preserve every hard category")
    hard_evidence = [
        _validate_hard_evidence(name, hard_in[name])
        for name in HARD_EVIDENCE_NAMES
    ]

    source = case.get("source", {})
    source_sha = source.get("sha256")
    if not isinstance(source_sha, str) or len(source_sha) != 64:
        raise ValueError(f"{case_id}: source sha256 is required")

    determinism_sha = case.get("determinism_sha256")
    if not isinstance(determinism_sha, str) or len(determinism_sha) != 64:
        raise ValueError(f"{case_id}: determinism sha256 is required")

    return {
        "case_id": case_id,
        "source": dict(source),
        "determinism_sha256": determinism_sha,
        "diagnostics": diagnostics,
        "hard_evidence": hard_evidence,
        "context_metrics": dict(case.get("context_metrics", {})),
        "provenance": dict(case.get("provenance", {})),
    }


def build_cross_case_matrix(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if len(cases) < 2:
        raise ValueError("cross-case matrix requires at least two cases")
    normalized = [_normalize_case(case) for case in cases]
    ids = [case["case_id"] for case in normalized]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case_id")
    normalized.sort(key=lambda row: row["case_id"])

    distributions: dict[str, Any] = {}
    for name in DIAGNOSTIC_NAMES:
        values = [
            {"case_id": case["case_id"], "value": next(
                row["value"] for row in case["diagnostics"] if row["name"] == name
            )}
            for case in normalized
            if next(row["status"] for row in case["diagnostics"] if row["name"] == name)
            == "AVAILABLE"
        ]
        numeric = [row["value"] for row in values]
        distributions[name] = {
            "available_count": len(values),
            "unavailable_count": len(normalized) - len(values),
            "min": min(numeric) if numeric else None,
            "max": max(numeric) if numeric else None,
            "values": values,
        }

    return {
        "artifact_version": SA10_CROSS_CASE_VERSION,
        "case_count": len(normalized),
        "cases": normalized,
        "distributions": distributions,
        "boundary": {
            "aggregate_quality_score": False,
            "calibrated_thresholds": False,
            "gc001_threshold_derivation": False,
            "hard_failures_individually_visible": True,
            "unavailable_evidence_preserved": True,
        },
    }


def write_cross_case_matrix(cases: Sequence[Mapping[str, Any]], output: Path) -> str:
    artifact = build_cross_case_matrix(cases)
    payload = (json.dumps(artifact, indent=2, sort_keys=True) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = [json.loads(path.read_text(encoding="utf-8")) for path in args.case]
    digest = write_cross_case_matrix(cases, args.output)
    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
