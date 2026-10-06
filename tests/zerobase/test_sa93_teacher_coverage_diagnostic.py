from __future__ import annotations

import json
from pathlib import Path

import pytest

from minimalizer_zerobase.semantic_abstraction.semantic_golden_teacher import (
    GoldenDecisionLabel,
    GoldenTeacherAnnotation,
    build_semantic_golden_teacher_report,
)
from minimalizer_zerobase.semantic_abstraction.teacher_coverage_diagnostic import (
    build_teacher_coverage_diagnostic,
)


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "benchmarks" / "golden" / "cases" / "GC001_IMG_1205.sa9-teacher.json"


def _gc001_report():
    payload = json.loads(AUDIT.read_text(encoding="utf-8"))
    annotations = tuple(
        GoldenTeacherAnnotation(
            role=row["role"],
            decision=GoldenDecisionLabel(row["decision"]),
            rationale=row["rationale"],
        )
        for row in payload["annotations"]
    )
    return build_semantic_golden_teacher_report(
        production_roles=payload["production_roles"],
        golden_annotations=annotations,
        case_id=payload["case_id"],
    )


def test_gc001_teacher_coverage_is_exactly_two_of_eight():
    diagnostic = build_teacher_coverage_diagnostic(_gc001_report())

    assert diagnostic.total_roles == 8
    assert diagnostic.labeled_roles == 2
    assert diagnostic.unresolved_roles == 6
    assert diagnostic.coverage_ratio == pytest.approx(0.25)
    assert diagnostic.decision_histogram == {
        "SURVIVED": 0,
        "SIMPLIFIED": 0,
        "REMOVED": 0,
        "REAUTHORED": 2,
    }


def test_coverage_is_diagnostic_not_quality_or_gate():
    payload = build_teacher_coverage_diagnostic(_gc001_report()).to_dict()

    assert payload["authoritative"] is False
    assert payload["can_override_hard_fail"] is False
    assert payload["production_input_allowed"] is False
    assert payload["production_output_changed"] is False
    assert payload["interpretation"]["coverage_is_quality_score"] is False
    assert payload["interpretation"]["coverage_is_gate"] is False
    assert payload["interpretation"]["disagreement_is_gate"] is False


def test_optional_disagreement_counts_only_comparable_labeled_roles():
    report = build_semantic_golden_teacher_report(
        production_roles=("hair", "major_clothing", "right_arm"),
        golden_annotations=(
            GoldenTeacherAnnotation(
                "hair", GoldenDecisionLabel.REAUTHORED, primitive_family="polygon"
            ),
            GoldenTeacherAnnotation(
                "major_clothing",
                GoldenDecisionLabel.REAUTHORED,
                primitive_family="polygon",
            ),
        ),
        semantic_retention={
            "authoritative": False,
            "can_override_hard_fail": False,
            "role_similarity": {"hair": 0.9, "right_arm": 0.8},
        },
        primitive_advisor={
            "authoritative": False,
            "production_output_changed": False,
            "audits": [
                {
                    "role": "hair",
                    "suggestion": {"primitive_family": "polygon"},
                    "geometry": {"deterministic_family": "polygon"},
                    "family_agreement": True,
                },
                {
                    "role": "major_clothing",
                    "suggestion": {"primitive_family": "ellipse"},
                    "geometry": {"deterministic_family": "polygon"},
                    "family_agreement": False,
                },
                {
                    "role": "right_arm",
                    "suggestion": {"primitive_family": "polygon"},
                    "geometry": {"deterministic_family": "polygon"},
                    "family_agreement": True,
                },
            ],
        },
    )

    diagnostic = build_teacher_coverage_diagnostic(report)
    assert diagnostic.comparable_primitive_roles == 2
    assert diagnostic.primitive_disagreements == 1
    assert diagnostic.semantic_retention_observed_roles == 2
