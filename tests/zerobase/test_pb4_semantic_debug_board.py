from __future__ import annotations

import copy

import numpy as np
import pytest

from minimalizer_zerobase.analyzers.contracts import Evidence, Provenance
from minimalizer_zerobase.analyzers.structured_mask_evidence import (
    build_pb2_structured_evidence,
)
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.importance import (
    ImportanceEngine,
    build_pb3_importance_diagnostic,
    evaluate_importance_omission,
)
from minimalizer_zerobase.semantic_abstraction.precedent_debug_board import (
    build_pb4_semantic_debug_board,
    canonical_pb4_debug_json,
    render_pb4_debug_image,
    render_pb4_debug_text,
)
from minimalizer_zerobase.scene.fusion import EvidenceFusion


SPACE = CoordinateSpace(80, 80)


def _mask(boxes=()):
    out = np.zeros((80, 80), bool)
    for x0, y0, x1, y1 in boxes:
        out[y0:y1, x0:x1] = True
    return out


def _retention(score=1.0, *, status="AVAILABLE"):
    return {
        "version": "sa7.45-v1",
        "observer": "synthetic",
        "status": status,
        "global_similarity": score,
        "patch_similarity": score,
        "role_similarity": {},
        "semantic_retention_score": score,
        "fidelity_score": score,
        "simplicity_score": None,
        "authoritative": False,
        "can_override_hard_fail": False,
        "reasons": [],
    }


def _fixtures():
    pb2 = build_pb2_structured_evidence(
        role_masks={
            "hair": _mask(
                (
                    (5, 5, 35, 35),
                    (50, 5, 55, 10),
                )
            ),
            "head": _mask(((20, 20, 50, 50),)),
            "major_clothing": _mask(
                (
                    (10, 50, 45, 75),
                    (55, 60, 60, 65),
                )
            ),
        },
        coordinate_space=SPACE,
    )
    pb3 = build_pb3_importance_diagnostic(
        pb2_evidence=pb2.evidence,
        context_semantic_retention=_retention(0.93),
    )
    return pb2, pb3


def _component_id(pb2, role, index=0):
    rows = [
        item.evidence_id
        for item in pb2.evidence
        if item.evidence_type == "region_component"
        and item.semantic_label == role
    ]
    return rows[index]


def test_board_is_deterministic_and_input_order_invariant():
    pb2, pb3 = _fixtures()
    a = build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
        adopted_visual_baseline="baseline-x",
    )
    b = build_pb4_semantic_debug_board(
        pb2_evidence=tuple(reversed(pb2.evidence)),
        pb3_report=pb3.to_dict(),
        adopted_visual_baseline="baseline-x",
    )

    assert a.to_dict() == b.to_dict()
    assert canonical_pb4_debug_json(a) == canonical_pb4_debug_json(b)
    assert render_pb4_debug_text(a) == render_pb4_debug_text(b)
    assert render_pb4_debug_image(a).tobytes() == render_pb4_debug_image(b).tobytes()


def test_every_pb3_component_is_present_exactly_once():
    pb2, pb3 = _fixtures()
    board = build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
    )

    expected = {
        item.evidence_id
        for item in pb2.evidence
        if item.evidence_type == "region_component"
    }
    actual = [row.component_id for row in board.component_rows]

    assert set(actual) == expected
    assert len(actual) == len(set(actual)) == len(expected)


def test_unavailable_component_observers_are_visible():
    pb2, pb3 = _fixtures()
    board = build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
    )
    text = render_pb4_debug_text(board)

    assert board.observer_availability["removal_available"] == 0
    assert board.observer_availability["merge_available"] == 0
    assert board.observer_availability["removal_unavailable"] == len(
        board.component_rows
    )
    assert "removal unavailable:" in text
    assert "UNAVAILABLE:NA" in text


def test_advisor_unavailable_is_visible():
    pb2, pb3 = _fixtures()
    board = build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
    )
    text = render_pb4_debug_text(board)

    assert board.advisor_context_count == 0
    assert all(
        row.primitive_advisor_status == "UNAVAILABLE"
        for row in board.component_rows
    )
    assert "advisor=UNAVAILABLE" in text


def test_recommendation_reasons_are_preserved():
    pb2, pb3 = _fixtures()
    board = build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
    )

    pb3_by_id = {
        row.component_id: row
        for row in pb3.components
    }
    for row in board.component_rows:
        assert row.reasons == pb3_by_id[row.component_id].reasons


def test_high_quality_context_cannot_hide_hard_failure():
    pb2, _ = _fixtures()
    pb3 = build_pb3_importance_diagnostic(
        pb2_evidence=pb2.evidence,
        context_semantic_retention=_retention(1.0),
        hard_failures=("feature_survival_missing",),
    )
    board = build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
    )
    text = render_pb4_debug_text(board)

    assert board.semantic_context_score == pytest.approx(1.0)
    assert board.hard_failures == ("feature_survival_missing",)
    assert "HARD FAIL: feature_survival_missing" in text
    assert "hard-fail override allowed: false" in text


def test_authority_categories_are_explicit_and_promoted_zero():
    pb2, pb3 = _fixtures()
    board = build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
    )
    text = render_pb4_debug_text(board)

    assert board.authority_counts["observed"] == len(pb2.evidence)
    assert board.authority_counts["advisor"] == 0
    assert board.authority_counts["promoted"] == 0
    assert "OBSERVED EVIDENCE:" in text
    assert "ADVISOR EVIDENCE: 0" in text
    assert "PROMOTED PRODUCTION AUTHORITY: 0" in text


def test_production_action_must_remain_null():
    pb2, pb3 = _fixtures()
    payload = pb3.to_dict()
    payload["components"][0]["production_action"] = "prune"

    with pytest.raises(ValueError, match="production action"):
        build_pb4_semantic_debug_board(
            pb2_evidence=pb2.evidence,
            pb3_report=payload,
        )


def test_pb2_pb3_component_mismatch_fails_closed():
    pb2, pb3 = _fixtures()
    payload = pb3.to_dict()
    payload["components"] = payload["components"][:-1]

    with pytest.raises(ValueError, match="component mismatch"):
        build_pb4_semantic_debug_board(
            pb2_evidence=pb2.evidence,
            pb3_report=payload,
        )


def test_board_generation_does_not_mutate_pb2_or_pb3_inputs():
    pb2, pb3 = _fixtures()
    pb2_before = [item.to_json() for item in pb2.evidence]
    pb3_before = copy.deepcopy(pb3.to_dict())

    build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
        adopted_visual_baseline="a60aaa12",
    )

    assert pb2_before == [item.to_json() for item in pb2.evidence]
    assert pb3_before == pb3.to_dict()


def _phase8_fixture():
    height = width = 16
    labels = np.full((height, width), 65535, dtype=np.uint16)
    labels[2:10, 2:10] = 0
    labels[11:12, 5:6] = 1

    def runs(mask):
        encoded = []
        for y in np.flatnonzero(np.any(mask, axis=1)):
            xs = np.flatnonzero(mask[y])
            start = previous = int(xs[0])
            for raw_x in xs[1:]:
                x = int(raw_x)
                if x != previous + 1:
                    encoded.append([int(y), start, previous + 1])
                    start = x
                previous = x
            encoded.append([int(y), start, previous + 1])
        return encoded

    masses = []
    for index in range(2):
        mask = labels == index
        ys, xs = np.where(mask)
        masses.append(
            {
                "mass_id": f"mass-{index:04d}",
                "semantic_part_id": "torso",
                "binding_status": "bound",
                "region_ids": [f"region-{index:04d}"],
                "pixel_count": int(xs.size),
                "bbox_xywh": [
                    int(xs.min()),
                    int(ys.min()),
                    int(xs.max() - xs.min() + 1),
                    int(ys.max() - ys.min() + 1),
                ],
                "centroid_xy": [float(xs.mean()), float(ys.mean())],
                "mean_rgb": [80 + index, 90 + index, 100 + index],
                "pixel_runs": runs(mask),
                "evidence_refs": ["phase06:test"],
            }
        )

    silhouette = (labels != 65535).astype(np.uint8) * 255
    payload = {
        "schema_version": "1.0",
        "coordinate_space": {
            "pixel_width": width,
            "pixel_height": height,
            "normalized_origin": "top-left",
            "normalized_range": [0.0, 1.0],
        },
        "masses": masses,
        "validation": {
            "subject_pixel_count": int(np.count_nonzero(silhouette)),
            "pass": True,
        },
    }
    return payload, labels, silhouette


def test_board_generation_does_not_change_importance_or_omission_outputs():
    production_evidence = (
        Evidence(
            "a",
            "region",
            CoordinateSpace(100, 100),
            Provenance("test", "1"),
            0.9,
            "person",
            {"bbox": [10, 10, 40, 40]},
            {},
        ),
        Evidence(
            "b",
            "region",
            CoordinateSpace(100, 100),
            Provenance("test", "1"),
            0.8,
            "accessory",
            {"bbox": [60, 10, 10, 10]},
            {},
        ),
    )
    scene = EvidenceFusion().fuse(production_evidence)
    importance_before = ImportanceEngine().apply(scene).to_json()

    payload, labels, silhouette = _phase8_fixture()
    omission_before = evaluate_importance_omission(
        copy.deepcopy(payload),
        labels.copy(),
        silhouette.copy(),
    ).to_dict()

    pb2, pb3 = _fixtures()
    build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
    )

    importance_after = ImportanceEngine().apply(scene).to_json()
    omission_after = evaluate_importance_omission(
        copy.deepcopy(payload),
        labels.copy(),
        silhouette.copy(),
    ).to_dict()

    assert importance_before == importance_after
    assert omission_before == omission_after


def test_static_image_layout_rejects_invalid_size():
    pb2, pb3 = _fixtures()
    board = build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
    )
    with pytest.raises(ValueError, match="layout"):
        render_pb4_debug_image(board, width=800)
