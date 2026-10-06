from __future__ import annotations

import hashlib

import numpy as np

from minimalizer_zerobase.analyzers.structured_mask_evidence import (
    build_pb2_structured_evidence,
)
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.evaluation.forbidden_face_detail_gate import (
    forbidden_face_detail_ratio,
)
from minimalizer_zerobase.importance import build_pb3_importance_diagnostic
from minimalizer_zerobase.semantic_abstraction.face_raster_guard import (
    apply_face_raster_guard,
)
from minimalizer_zerobase.semantic_abstraction.precedent_debug_board import (
    build_pb4_semantic_debug_board,
    render_pb4_debug_image,
    render_pb4_debug_text,
)
from minimalizer_zerobase.semantic_abstraction.primitive_type_advisor import (
    PrimitiveTypeSuggestion,
    audit_primitive_type_advice,
)


SPACE = CoordinateSpace(80, 80)


def _mask(boxes=()):
    out = np.zeros((80, 80), bool)
    for x0, y0, x1, y1 in boxes:
        out[y0:y1, x0:x1] = True
    return out


def _semantic(score=1.0):
    return {
        "version": "sa7.45-v1",
        "observer": "synthetic",
        "status": "AVAILABLE",
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


def _pb2_face_head():
    return build_pb2_structured_evidence(
        role_masks={
            "face": _mask(((25, 20, 50, 48),)),
            "head": _mask(((18, 12, 58, 55),)),
            "hair": _mask(((15, 8, 60, 32),)),
        },
        coordinate_space=SPACE,
        source_refs={
            "face": "phase04:part_masks/face.png",
            "head": "phase04:part_masks/head.png",
            "hair": "phase04:part_masks/hair.png",
        },
    )


def _face_component_id(pb2):
    return next(
        row.evidence_id
        for row in pb2.evidence
        if row.evidence_type == "region_component"
        and row.semantic_label == "face"
    )


def _synthetic_face_guard():
    source = np.full((80, 80, 3), [245, 220, 210], dtype=np.uint8)
    source[20:48, 25:50] = [250, 225, 218]
    rendered = np.full((80, 80, 3), [255, 255, 255], dtype=np.uint8)
    rendered[27:32, 31:37] = [20, 20, 20]
    face = _mask(((25, 20, 50, 48),))
    result = apply_face_raster_guard(rendered, source, face)
    return source, rendered, face, result


def _sha(rgb):
    return hashlib.sha256(np.asarray(rgb, dtype=np.uint8).tobytes()).hexdigest()


def test_pb2_face_and_head_evidence_remains_non_authoritative():
    pb2 = _pb2_face_head()
    rows = [
        row
        for row in pb2.evidence
        if row.semantic_label in {"face", "head"}
    ]
    assert rows
    assert all(
        row.normalization["authority"]["state"] == "observed"
        for row in rows
    )
    assert all(
        row.normalization["authority"]["production_authority"] is False
        for row in rows
    )


def test_pb3_unavailable_face_semantic_perturbation_cannot_imply_omission():
    pb2 = _pb2_face_head()
    report = build_pb3_importance_diagnostic(pb2_evidence=pb2.evidence)
    face = next(row for row in report.components if row.role == "face")

    assert face.recommendation.value == "insufficient-evidence"
    assert face.production_action is None
    assert face.removal_impact is None
    assert face.merge_impact is None


def test_pb3_perfect_semantic_score_cannot_override_face_hard_failure():
    pb2 = _pb2_face_head()
    face_id = _face_component_id(pb2)
    report = build_pb3_importance_diagnostic(
        pb2_evidence=pb2.evidence,
        removal_retention_by_component={face_id: _semantic(1.0)},
        hard_failures=("forbidden_face_detail_nonzero",),
    )

    assert report.hard_failures == ("forbidden_face_detail_nonzero",)
    assert report.can_override_hard_fail is False
    assert report.authoritative is False
    assert all(row.production_action is None for row in report.components)


def test_pb4_explicitly_displays_face_hard_failure():
    pb2 = _pb2_face_head()
    pb3 = build_pb3_importance_diagnostic(
        pb2_evidence=pb2.evidence,
        context_semantic_retention=_semantic(1.0),
        hard_failures=("forbidden_face_detail_nonzero",),
    )
    board = build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
    )
    text = render_pb4_debug_text(board)

    assert board.semantic_context_score == 1.0
    assert board.hard_failures == ("forbidden_face_detail_nonzero",)
    assert "HARD FAIL: forbidden_face_detail_nonzero" in text
    assert "hard-fail override allowed: false" in text


def test_pb4_generation_leaves_guarded_face_raster_byte_identical():
    source, rendered, face, guarded = _synthetic_face_guard()
    before = _sha(guarded.rgb)

    pb2 = _pb2_face_head()
    pb3 = build_pb3_importance_diagnostic(
        pb2_evidence=pb2.evidence,
        context_semantic_retention=_semantic(0.99),
    )
    board = build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
    )
    render_pb4_debug_text(board)
    render_pb4_debug_image(board)

    after = _sha(guarded.rgb)
    assert before == after
    assert np.array_equal(guarded.rgb[~face], rendered[~face])
    assert np.array_equal(source.shape, rendered.shape)


def test_face_raster_guard_still_writes_zero_pixels_outside_face_mask():
    _, rendered, face, result = _synthetic_face_guard()
    assert result.changed_outside_face_pixels == 0
    assert np.array_equal(result.rgb[~face], rendered[~face])


def test_guarded_raster_still_yields_zero_forbidden_face_detail():
    _, _, face, result = _synthetic_face_guard()
    assert forbidden_face_detail_ratio(result.rgb, face) == 0.0


def test_unavailable_observer_and_advisor_paths_do_not_change_face_output():
    _, _, face, guarded = _synthetic_face_guard()
    before = _sha(guarded.rgb)

    pb2 = _pb2_face_head()
    pb3 = build_pb3_importance_diagnostic(pb2_evidence=pb2.evidence)
    board = build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
    )

    assert all(
        row.primitive_advisor_status == "UNAVAILABLE"
        for row in pb3.components
    )
    assert all(
        row.semantic_removal_observer == "UNAVAILABLE"
        for row in board.component_rows
    )
    assert _sha(guarded.rgb) == before
    assert forbidden_face_detail_ratio(guarded.rgb, face) == 0.0


def test_arbitrary_primitive_advice_cannot_become_face_geometry_authority():
    pb2 = _pb2_face_head()
    role_masks = {
        "face": _mask(((25, 20, 50, 48),)),
        "head": _mask(((18, 12, 58, 55),)),
        "hair": _mask(((15, 8, 60, 32),)),
    }
    advisor = audit_primitive_type_advice(
        role_masks,
        (
            PrimitiveTypeSuggestion(
                role="face",
                primitive_family="ellipse",
                confidence=1.0,
                source="synthetic-starvector",
            ),
        ),
    )
    pb3 = build_pb3_importance_diagnostic(
        pb2_evidence=pb2.evidence,
        primitive_advisor=advisor,
    )
    face = next(row for row in pb3.components if row.role == "face")

    assert face.primitive_advisor_status == "AVAILABLE"
    assert face.primitive_suggested_family == "ellipse"
    assert face.production_action is None
    assert face.recommendation.value == "insufficient-evidence"

    audit = next(row for row in advisor.audits if row.role == "face")
    assert audit.production_eligible is False
    assert advisor.authoritative is False
    assert advisor.production_output_changed is False


def test_pb5_diagnostics_are_noop_after_canonical_face_guard():
    _, _, face, guarded = _synthetic_face_guard()
    guarded_before = guarded.rgb.copy()

    pb2 = _pb2_face_head()
    face_id = _face_component_id(pb2)
    pb3 = build_pb3_importance_diagnostic(
        pb2_evidence=pb2.evidence,
        removal_retention_by_component={face_id: _semantic(1.0)},
        context_semantic_retention=_semantic(1.0),
        hard_failures=(),
    )
    board = build_pb4_semantic_debug_board(
        pb2_evidence=pb2.evidence,
        pb3_report=pb3,
        adopted_visual_baseline="test-baseline",
    )
    _ = render_pb4_debug_text(board)
    _ = render_pb4_debug_image(board)

    assert np.array_equal(guarded.rgb, guarded_before)
    assert forbidden_face_detail_ratio(guarded.rgb, face) == 0.0
    assert board.authority_counts["promoted"] == 0
    assert board.production_policy_changed is False
    assert board.production_output_changed is False
