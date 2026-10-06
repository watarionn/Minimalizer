from __future__ import annotations

import copy

import numpy as np
import pytest

from minimalizer_zerobase.analyzers.contracts import Evidence
from minimalizer_zerobase.analyzers.structured_mask_evidence import (
    build_pb2_structured_evidence,
)
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.importance import (
    ImportanceEngine,
    PB3Recommendation,
    build_pb3_importance_diagnostic,
    evaluate_importance_omission,
)
from minimalizer_zerobase.semantic_abstraction.primitive_type_advisor import (
    PrimitiveTypeSuggestion,
    audit_primitive_type_advice,
)
from minimalizer_zerobase.scene.fusion import EvidenceFusion
from minimalizer_zerobase.analyzers.contracts import Provenance


SPACE = CoordinateSpace(80, 80)


def _mask(boxes=()):
    out = np.zeros((80, 80), bool)
    for x0, y0, x1, y1 in boxes:
        out[y0:y1, x0:x1] = True
    return out


def _pb2():
    return build_pb2_structured_evidence(
        role_masks={
            "major_clothing": _mask(
                (
                    (5, 5, 45, 45),
                    (55, 5, 60, 10),
                )
            ),
            "hair": _mask(
                (
                    (10, 50, 40, 75),
                    (55, 60, 58, 63),
                )
            ),
        },
        coordinate_space=SPACE,
    )


def _retention(score):
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


def _component_ids(expansion, role):
    return [
        item.evidence_id
        for item in expansion.evidence
        if item.evidence_type == "region_component"
        and item.semantic_label == role
    ]


def test_unavailable_semantic_observer_never_infers_omission_from_area():
    expansion = _pb2()
    report = build_pb3_importance_diagnostic(
        pb2_evidence=expansion.evidence,
    )

    tiny = next(
        item
        for item in report.components
        if item.role == "major_clothing"
        and item.support_ratio < 0.05
    )
    assert tiny.recommendation is PB3Recommendation.INSUFFICIENT_EVIDENCE
    assert tiny.removal_impact is None
    assert tiny.production_action is None
    assert report.production_policy_changed is False


def test_high_observed_removal_impact_recommends_retain_evidence():
    expansion = _pb2()
    target = _component_ids(expansion, "major_clothing")[1]
    report = build_pb3_importance_diagnostic(
        pb2_evidence=expansion.evidence,
        removal_retention_by_component={
            target: _retention(0.70),
        },
    )

    item = next(row for row in report.components if row.component_id == target)
    assert item.removal_impact == pytest.approx(0.30)
    assert item.recommendation is PB3Recommendation.RETAIN_EVIDENCE
    assert "observed_removal_semantic_impact" in item.reasons


def test_low_impact_small_low_identity_component_can_be_omission_candidate_evidence():
    expansion = _pb2()
    target = _component_ids(expansion, "major_clothing")[1]
    report = build_pb3_importance_diagnostic(
        pb2_evidence=expansion.evidence,
        removal_retention_by_component={
            target: _retention(0.99),
        },
    )

    item = next(row for row in report.components if row.component_id == target)
    assert item.support_ratio < 0.05
    assert item.role_identity_importance < 0.80
    assert item.recommendation is PB3Recommendation.OMISSION_CANDIDATE_EVIDENCE
    assert item.production_action is None
    assert item.authoritative is False


def test_high_identity_role_is_not_omission_candidate_even_with_low_observed_impact():
    expansion = _pb2()
    target = _component_ids(expansion, "hair")[1]
    report = build_pb3_importance_diagnostic(
        pb2_evidence=expansion.evidence,
        removal_retention_by_component={
            target: _retention(0.99),
        },
    )

    item = next(row for row in report.components if row.component_id == target)
    assert item.role_identity_importance >= 0.80
    assert item.recommendation is PB3Recommendation.RETAIN_EVIDENCE
    assert "high_identity_role_context" in item.reasons


def test_low_merge_impact_with_explicit_target_is_merge_candidate_evidence():
    expansion = _pb2()
    ids = _component_ids(expansion, "major_clothing")
    target = ids[1]
    report = build_pb3_importance_diagnostic(
        pb2_evidence=expansion.evidence,
        merge_retention_by_component={
            target: _retention(0.99),
        },
        merge_target_by_component={
            target: ids[0],
        },
    )

    item = next(row for row in report.components if row.component_id == target)
    assert item.merge_impact == pytest.approx(0.01)
    assert item.merge_target_id == ids[0]
    assert item.recommendation is PB3Recommendation.MERGE_CANDIDATE_EVIDENCE


def test_merge_semantic_evidence_requires_explicit_target():
    expansion = _pb2()
    target = _component_ids(expansion, "major_clothing")[1]
    with pytest.raises(ValueError, match="requires merge target"):
        build_pb3_importance_diagnostic(
            pb2_evidence=expansion.evidence,
            merge_retention_by_component={
                target: _retention(0.99),
            },
        )


def test_primitive_advisor_context_never_creates_action_without_semantic_impact():
    expansion = _pb2()
    masks = {
        "major_clothing": _mask(((5, 5, 45, 45),)),
        "hair": _mask(((10, 50, 40, 75),)),
    }
    advisor = audit_primitive_type_advice(
        masks,
        (
            PrimitiveTypeSuggestion(
                role="major_clothing",
                primitive_family="rectangle",
                confidence=1.0,
                source="synthetic-starvector",
            ),
        ),
    )
    report = build_pb3_importance_diagnostic(
        pb2_evidence=expansion.evidence,
        primitive_advisor=advisor,
    )

    item = next(row for row in report.components if row.role == "major_clothing")
    assert item.primitive_advisor_status == "AVAILABLE"
    assert item.primitive_suggested_family == "rectangle"
    assert item.recommendation is PB3Recommendation.INSUFFICIENT_EVIDENCE
    assert item.production_action is None


def test_perfect_semantic_score_cannot_clear_existing_hard_failure():
    expansion = _pb2()
    target = _component_ids(expansion, "major_clothing")[1]
    report = build_pb3_importance_diagnostic(
        pb2_evidence=expansion.evidence,
        removal_retention_by_component={
            target: _retention(1.0),
        },
        hard_failures=("feature_survival_missing",),
    )

    assert report.hard_failures == ("feature_survival_missing",)
    assert report.can_override_hard_fail is False
    assert report.authoritative is False
    assert all(item.production_action is None for item in report.components)


def test_authoritative_semantic_retention_fails_closed():
    expansion = _pb2()
    target = _component_ids(expansion, "major_clothing")[1]
    payload = _retention(0.99)
    payload["authoritative"] = True

    with pytest.raises(ValueError, match="non-authoritative"):
        build_pb3_importance_diagnostic(
            pb2_evidence=expansion.evidence,
            removal_retention_by_component={target: payload},
        )


def test_unknown_component_semantic_evidence_fails_closed():
    expansion = _pb2()
    with pytest.raises(ValueError, match="unknown components"):
        build_pb3_importance_diagnostic(
            pb2_evidence=expansion.evidence,
            removal_retention_by_component={
                "pb2:invented:component:999": _retention(0.99),
            },
        )


def test_promoted_pb2_evidence_is_rejected_as_pb3_observer_input():
    expansion = _pb2()
    row = next(
        item
        for item in expansion.evidence
        if item.evidence_type == "region_component"
    )
    normalization = dict(row.normalization)
    authority = dict(normalization["authority"])
    authority["state"] = "promoted"
    authority["production_authority"] = True
    normalization["authority"] = authority

    promoted = Evidence(
        row.evidence_id,
        row.evidence_type,
        row.coordinate_space,
        row.provenance,
        row.confidence,
        row.semantic_label,
        dict(row.geometry),
        normalization,
    )

    with pytest.raises(ValueError, match="non-authoritative"):
        build_pb3_importance_diagnostic(pb2_evidence=(promoted,))


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
    specs = (
        ("torso", (80, 90, 100)),
        ("torso", (81, 91, 101)),
    )
    for index, (part, color) in enumerate(specs):
        mask = labels == index
        ys, xs = np.where(mask)
        masses.append(
            {
                "mass_id": f"mass-{index:04d}",
                "semantic_part_id": part,
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
                "mean_rgb": list(color),
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


def test_pb3_generation_does_not_change_importance_or_omission_outputs():
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

    expansion = _pb2()
    build_pb3_importance_diagnostic(pb2_evidence=expansion.evidence)

    importance_after = ImportanceEngine().apply(scene).to_json()
    omission_after = evaluate_importance_omission(
        copy.deepcopy(payload),
        labels.copy(),
        silhouette.copy(),
    ).to_dict()

    assert importance_before == importance_after
    assert omission_before == omission_after
