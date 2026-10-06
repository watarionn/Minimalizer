from __future__ import annotations

import json
from pathlib import Path

from minimalizer_zerobase.semantic_abstraction.gc001_teacher_artifact import (
    build_gc001_artifact,
)


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "benchmarks" / "golden" / "cases" / "GC001_IMG_1205.sa9-teacher.json"


def test_gc001_sa94_artifact_is_reproducible_and_production_neutral():
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    first = build_gc001_artifact(audit)
    second = build_gc001_artifact(audit)

    assert first == second
    assert first["artifact_version"] == "sa9.4-v1"
    assert first["coverage_diagnostic"]["coverage_ratio"] == 0.25
    assert first["coverage_diagnostic"]["labeled_roles"] == 2
    assert first["coverage_diagnostic"]["unresolved_roles"] == 6
    assert first["authority"] == {
        "evaluation_only": True,
        "production_input_allowed": False,
        "production_output_changed": False,
    }
    assert first["teacher_report"]["production_output_changed"] is False
    assert first["teacher_report"]["provenance"]["golden_raster_used"] is False
    assert first["teacher_report"]["provenance"]["golden_coordinates_used"] is False
    assert first["teacher_report"]["provenance"]["golden_masks_used"] is False
    assert first["teacher_report"]["provenance"]["golden_colors_used"] is False
    assert first["teacher_report"]["provenance"]["golden_geometry_used"] is False
