from __future__ import annotations

import json
from pathlib import Path

from minimalizer_zerobase.semantic_abstraction.semantic_golden_teacher import (
    GoldenDecisionLabel,
    GoldenTeacherAnnotation,
    build_semantic_golden_teacher_report,
)


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "benchmarks" / "golden" / "cases" / "GC001_IMG_1205.sa9-teacher.json"


def test_gc001_sa9_teacher_audit_is_evaluation_only_and_partial_by_design():
    payload = json.loads(AUDIT.read_text(encoding="utf-8"))

    assert payload["production_authority"] is False
    assert payload["mapping_policy"]["golden_pixels_used"] is False
    assert payload["mapping_policy"]["golden_coordinates_used"] is False
    assert payload["mapping_policy"]["golden_masks_used"] is False
    assert payload["mapping_policy"]["golden_colors_used"] is False
    assert payload["mapping_policy"]["golden_geometry_used"] is False

    annotations = {
        row["role"]: row["decision"] for row in payload["annotations"]
    }
    assert annotations == {
        "hair": "REAUTHORED",
        "major_clothing": "REAUTHORED",
    }
    assert set(payload["unresolved_roles"]) == {
        "accessory_or_held_object",
        "face_skin",
        "left_arm",
        "left_leg",
        "right_arm",
        "right_leg",
    }


def test_gc001_sa9_teacher_audit_builds_without_inventing_unresolved_labels():
    payload = json.loads(AUDIT.read_text(encoding="utf-8"))
    annotations = tuple(
        GoldenTeacherAnnotation(
            role=row["role"],
            decision=GoldenDecisionLabel(row["decision"]),
            rationale=row["rationale"],
        )
        for row in payload["annotations"]
    )

    report = build_semantic_golden_teacher_report(
        production_roles=payload["production_roles"],
        golden_annotations=annotations,
        case_id=payload["case_id"],
    )

    decisions = {row.role: row.golden_decision for row in report.roles}
    assert decisions["hair"] is GoldenDecisionLabel.REAUTHORED
    assert decisions["major_clothing"] is GoldenDecisionLabel.REAUTHORED
    for role in payload["unresolved_roles"]:
        assert decisions[role] is None

    assert report.production_input_allowed is False
    assert report.production_output_changed is False
    assert report.authoritative is False
