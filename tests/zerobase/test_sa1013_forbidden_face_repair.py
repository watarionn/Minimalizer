from __future__ import annotations

import json
from pathlib import Path

import pytest

from minimalizer_zerobase.evaluation.cross_case_regression_matrix import (
    build_cross_case_matrix,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "benchmarks" / "regression" / "sa10"
EVIDENCE = DATA / "evidence"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "name,face_pixels,fill_rgb,semantic_score,candidate_sha",
    [
        (
            "Hyakuto-Kyoko",
            4808,
            [251, 226, 220],
            0.7637557534622893,
            "84022e48e13ed7a80f8e3425d085d311e3ab7c86fcb28278ba079e182a33646a",
        ),
        (
            "Juufuutei-Raden_stylecal_source",
            1413,
            [194, 178, 175],
            0.9295234636673059,
            "576a7baa1cf2dcf1a3254fb7daecefb1f5520dc8833294924077ba8ef98ab4b5",
        ),
    ],
)
def test_sa1013_face_guard_repairs_only_authorized_face_pixels(
    name: str,
    face_pixels: int,
    fill_rgb: list[int],
    semantic_score: float,
    candidate_sha: str,
):
    guard = _load(EVIDENCE / f"{name}.sa10.13-face-raster-guard.json")
    visual = _load(EVIDENCE / f"{name}.sa10.13-visual-hard-gate.json")
    dino = _load(EVIDENCE / f"{name}.sa10.13-semantic-retention.json")
    hard = _load(EVIDENCE / f"{name}.sa10.13-hard-evidence.json")

    assert guard["source_only"] is True
    assert guard["generated_or_inpainted_pixel_count"] == 0
    assert guard["golden_used_for_inference"] is False
    assert guard["browser_v12_used_for_inference"] is False
    assert guard["production_candidate_sha256"] == candidate_sha
    assert guard["face_raster_guard"]["face_pixels"] == face_pixels
    assert guard["face_raster_guard"]["changed_face_pixels"] == face_pixels
    assert guard["face_raster_guard"]["changed_outside_face_pixels"] == 0
    assert guard["face_raster_guard"]["fill_rgb"] == fill_rgb

    assert visual["binding"]["binding_passed"] is True
    assert visual["binding"]["same_transaction"] is False
    assert visual["binding"]["candidate_bytes_equal_baseline"] is False
    assert visual["feature_survival"]["passed"] is True
    assert visual["feature_survival"]["missing_count"] == 0
    assert visual["forbidden_face_detail"] == {
        "passed": True,
        "ratio": 0.0,
        "status": "AVAILABLE",
    }
    assert visual["canonical_hard_gate"]["pass_gate"] is True

    for gate in (
        "feature_survival",
        "forbidden_face_detail",
        "anatomy",
        "topology",
        "source_authority",
    ):
        assert hard["hard_evidence"][gate]["status"] == "AVAILABLE"
        assert hard["hard_evidence"][gate]["passed"] is True

    assert dino["candidate"]["sha256"] == candidate_sha
    assert dino["semantic_retention"]["semantic_retention_score"] == pytest.approx(
        semantic_score
    )
    assert dino["semantic_retention"]["authoritative"] is False
    assert dino["semantic_retention"]["can_override_hard_fail"] is False


def test_sa1013_baseline_adoption_remains_immutable_and_older_than_candidate():
    kyoko_visual = _load(
        EVIDENCE / "Hyakuto-Kyoko.sa10.13-visual-hard-gate.json"
    )
    raden_visual = _load(
        EVIDENCE / "Juufuutei-Raden_stylecal_source.sa10.13-visual-hard-gate.json"
    )
    assert (
        kyoko_visual["binding"]["baseline_artifact_sha256"]
        == "294a77a025656391a76b35cbb2fdb7f8f59c0e176e8433a1da0ca1fa5299065b"
    )
    assert (
        raden_visual["binding"]["baseline_artifact_sha256"]
        == "a31acc69a055e4144484939a510f06dee61379e426dc0b39751f4a5cf90dd07f"
    )
    assert kyoko_visual["binding"]["candidate_artifact_sha256"] != kyoko_visual["binding"]["baseline_artifact_sha256"]
    assert raden_visual["binding"]["candidate_artifact_sha256"] != raden_visual["binding"]["baseline_artifact_sha256"]


def test_sa1013_cross_case_matrix_has_all_available_hard_evidence_passing():
    artifact = build_cross_case_matrix([
        _load(DATA / "Hyakuto-Kyoko.sa10.13.json"),
        _load(DATA / "Juufuutei-Raden_stylecal_source.sa10.13.json"),
    ])
    for case in artifact["cases"]:
        hard = {row["name"]: row for row in case["hard_evidence"]}
        for gate in (
            "feature_survival",
            "forbidden_face_detail",
            "anatomy",
            "topology",
            "source_authority",
            "phase14_machine",
            "phase14_human_visual",
            "determinism",
        ):
            assert hard[gate]["status"] == "AVAILABLE"
            assert hard[gate]["passed"] is True
    assert artifact["boundary"]["aggregate_quality_score"] is False
    assert artifact["boundary"]["calibrated_thresholds"] is False


def test_sa1013_teacher_evidence_stays_unavailable():
    for name in ("Hyakuto-Kyoko", "Juufuutei-Raden_stylecal_source"):
        case = _load(DATA / f"{name}.sa10.13.json")
        assert case["diagnostics"]["teacher_coverage"]["status"] == "UNAVAILABLE"
        assert case["diagnostics"]["teacher_primitive_disagreements"]["status"] == "UNAVAILABLE"
