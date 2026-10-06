from __future__ import annotations

import argparse
import json
from pathlib import Path

from minimalizer_zerobase.semantic_abstraction.semantic_golden_teacher import (
    GoldenDecisionLabel,
    GoldenTeacherAnnotation,
    build_semantic_golden_teacher_report,
)
from minimalizer_zerobase.semantic_abstraction.teacher_coverage_diagnostic import (
    build_teacher_coverage_diagnostic,
)


def build_gc001_artifact(audit: dict) -> dict:
    annotations = tuple(
        GoldenTeacherAnnotation(
            role=row["role"],
            decision=GoldenDecisionLabel(row["decision"]),
            rationale=row.get("rationale", ""),
        )
        for row in audit["annotations"]
    )
    report = build_semantic_golden_teacher_report(
        production_roles=audit["production_roles"],
        golden_annotations=annotations,
        case_id=audit["case_id"],
    )
    coverage = build_teacher_coverage_diagnostic(report)
    return {
        "artifact_version": "sa9.4-v1",
        "case_id": audit["case_id"],
        "reviewed_annotations": audit["annotations"],
        "unresolved_roles": audit["unresolved_roles"],
        "teacher_report": report.to_dict(),
        "coverage_diagnostic": coverage.to_dict(),
        "authority": {
            "evaluation_only": True,
            "production_input_allowed": False,
            "production_output_changed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    artifact = build_gc001_artifact(audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
