from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from minimalizer_zerobase.evaluation.cross_case_regression_matrix import (
    build_cross_case_matrix,
)
from minimalizer_zerobase.simplification.structural_source_repair import (
    apply_structural_source_repair,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "benchmarks" / "regression" / "sa10"
EVIDENCE = DATA / "evidence"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _group(part: str, mask: np.ndarray, order: int = 0) -> dict:
    return {
        "part": part,
        "color": (80, 90, 100),
        "mask": mask.copy(),
        "source_ids": [f"{part}-source"],
        "source_actions": {"keep"},
        "first_order": order,
    }


def test_structural_source_repair_is_noop_when_structure_is_aligned():
    shape = (40, 40)
    source = np.zeros((*shape, 3), dtype=np.uint8)
    head = np.zeros(shape, bool)
    head[4:16, 12:28] = True
    torso = np.zeros(shape, bool)
    torso[16:32, 14:26] = True
    left = np.zeros(shape, bool)
    left[17:31, 8:14] = True
    right = np.zeros(shape, bool)
    right[17:31, 26:32] = True
    lower = np.zeros(shape, bool)
    lower[31:39, 15:25] = True
    face = np.zeros(shape, bool)
    face[7:14, 16:24] = True
    masks = {
        "head": head,
        "torso": torso,
        "left_arm": left,
        "right_arm": right,
        "lower_body": lower,
        "face": face,
    }
    groups = [_group(part, mask, i) for i, (part, mask) in enumerate(masks.items())]
    repaired, report = apply_structural_source_repair(
        groups,
        source_rgba=source,
        source_part_masks=masks,
        shape=shape,
    )
    assert report["applied"] is False
    assert report["repaired_parts"] == []
    assert len(repaired) == len(groups)


def test_structural_source_repair_recovers_missing_support_head():
    shape = (40, 40)
    source = np.zeros((*shape, 3), dtype=np.uint8)
    head = np.zeros(shape, bool)
    head[4:17, 10:30] = True
    face = np.zeros(shape, bool)
    face[8:15, 16:24] = True
    torso = np.zeros(shape, bool)
    torso[17:33, 13:27] = True
    masks = {"head": head, "face": face, "torso": torso}
    groups = [_group("face", face, 1), _group("torso", torso, 2)]
    repaired, report = apply_structural_source_repair(
        groups,
        source_rgba=source,
        source_part_masks=masks,
        shape=shape,
    )
    assert report["applied"] is True
    assert "head" in report["repaired_parts"]
    assert report["missing_required_relations_after"] == []
    repaired_head = next(row for row in repaired if row["part"] == "head")
    assert np.array_equal(repaired_head["mask"], head)
    assert repaired_head["source_evidence_refs"] == ("phase04:part_masks/head.png",)


def test_sa1011_real_case_evidence_closes_structural_hard_failures():
    cases = [
        ("Hyakuto-Kyoko", 0.7552631073534017, "294a77a025656391a76b35cbb2fdb7f8f59c0e176e8433a1da0ca1fa5299065b"),
        ("Juufuutei-Raden_stylecal_source", 0.9313136511266809, "a31acc69a055e4144484939a510f06dee61379e426dc0b39751f4a5cf90dd07f"),
    ]
    for name, score, candidate_sha in cases:
        case = _load(DATA / f"{name}.sa10.11.json")
        dino = _load(EVIDENCE / f"{name}.sa10.11-semantic-retention.json")
        hard = _load(EVIDENCE / f"{name}.sa10.11-hard-evidence.json")
        assert case["hard_evidence"]["source_authority"] == {"status": "AVAILABLE", "passed": True}
        assert case["hard_evidence"]["anatomy"] == {"status": "AVAILABLE", "passed": True}
        assert case["hard_evidence"]["topology"] == {"status": "AVAILABLE", "passed": True}
        assert hard["hard_evidence"]["source_authority"]["passed"] is True
        assert hard["hard_evidence"]["anatomy"]["passed"] is True
        assert hard["hard_evidence"]["topology"]["passed"] is True
        assert hard["structural_hard_evidence"]["topology"]["missing_required_relations"] == []
        assert dino["candidate"]["sha256"] == candidate_sha
        assert dino["semantic_retention"]["semantic_retention_score"] == pytest.approx(score)


def test_sa1011_matrix_keeps_unavailable_visual_baseline_gates_visible():
    artifact = build_cross_case_matrix([
        _load(DATA / "Hyakuto-Kyoko.sa10.11.json"),
        _load(DATA / "Juufuutei-Raden_stylecal_source.sa10.11.json"),
    ])
    for case in artifact["cases"]:
        hard = {row["name"]: row for row in case["hard_evidence"]}
        assert hard["anatomy"]["passed"] is True
        assert hard["topology"]["passed"] is True
        assert hard["source_authority"]["passed"] is True
        assert hard["feature_survival"]["status"] == "UNAVAILABLE"
        assert hard["forbidden_face_detail"]["status"] == "UNAVAILABLE"
    assert artifact["boundary"]["aggregate_quality_score"] is False
    assert artifact["boundary"]["calibrated_thresholds"] is False
