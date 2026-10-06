from __future__ import annotations

import copy

import pytest

from minimalizer_zerobase.semantic_abstraction.semantic_golden_teacher import (
    GoldenDecisionLabel,
    GoldenTeacherAnnotation,
    build_semantic_golden_teacher_report,
)


def _semantic(role_similarity=None):
    return {
        "version": "sa7.45-v1",
        "observer": "synthetic",
        "status": "AVAILABLE",
        "global_similarity": 0.9,
        "patch_similarity": 0.8,
        "role_similarity": role_similarity or {},
        "semantic_retention_score": 0.85,
        "fidelity_score": 0.85,
        "simplicity_score": None,
        "authoritative": False,
        "can_override_hard_fail": False,
        "reasons": [],
    }


def _advisor():
    return {
        "version": "sa7.46-v1",
        "status": "AVAILABLE",
        "geometry_evidence": {},
        "audits": [
            {
                "role": "hair",
                "suggestion": {
                    "role": "hair",
                    "primitive_family": "polygon",
                    "confidence": 0.9,
                    "source": "synthetic-starvector",
                    "authoritative": False,
                },
                "geometry": {"deterministic_family": "polygon"},
                "family_agreement": True,
                "renderer_supported": True,
                "production_eligible": False,
                "reasons": ["advisor_output_is_research_only"],
            }
        ],
        "authoritative": False,
        "production_output_changed": False,
    }


def test_teacher_joins_roles_semantics_and_primitive_advice_deterministically():
    report = build_semantic_golden_teacher_report(
        production_roles=("major_clothing", "hair"),
        golden_annotations=(
            GoldenTeacherAnnotation(
                role="hair",
                decision=GoldenDecisionLabel.SIMPLIFIED,
                primitive_family="polygon",
            ),
        ),
        semantic_retention=_semantic({"hair": 0.91}),
        primitive_advisor=_advisor(),
        case_id="GC001",
    )

    assert [row.role for row in report.roles] == ["hair", "major_clothing"]
    hair = report.roles[0]
    assert hair.golden_decision is GoldenDecisionLabel.SIMPLIFIED
    assert hair.semantic_retention == pytest.approx(0.91)
    assert hair.primitive_family_agreement is True
    assert hair.golden_advisor_agreement is True
    assert report.authoritative is False
    assert report.production_input_allowed is False
    assert report.production_output_changed is False


def test_golden_contract_contains_no_raster_geometry_color_or_mask_payload():
    payload = build_semantic_golden_teacher_report(
        production_roles=("hair",),
        golden_annotations=(
            GoldenTeacherAnnotation(
                role="hair",
                decision=GoldenDecisionLabel.REAUTHORED,
                primitive_family="polygon",
            ),
        ),
    ).to_dict()

    assert payload["provenance"]["golden_raster_used"] is False
    assert payload["provenance"]["golden_coordinates_used"] is False
    assert payload["provenance"]["golden_masks_used"] is False
    assert payload["provenance"]["golden_colors_used"] is False
    assert payload["provenance"]["golden_geometry_used"] is False
    serialized = repr(payload).lower()
    assert "pixel_runs" not in serialized
    assert "bbox_xywh" not in serialized


def test_absent_golden_teacher_is_valid_and_evaluation_only():
    report = build_semantic_golden_teacher_report(
        production_roles=("hair", "major_clothing"),
        semantic_retention=_semantic({"hair": 0.8}),
    )
    assert all(row.golden_decision is None for row in report.roles)
    assert all("golden_teacher_label_unavailable" in row.reasons for row in report.roles)
    assert report.production_input_allowed is False


def test_changing_golden_teacher_data_does_not_mutate_production_state():
    production_state = {
        "roles": ["hair", "major_clothing"],
        "renderer": {"primitive_budget": 12, "palette": ["#111111", "#eeeeee"]},
    }
    before = copy.deepcopy(production_state)

    a = build_semantic_golden_teacher_report(
        production_roles=production_state["roles"],
        golden_annotations=(
            GoldenTeacherAnnotation("hair", GoldenDecisionLabel.SURVIVED),
        ),
    )
    b = build_semantic_golden_teacher_report(
        production_roles=production_state["roles"],
        golden_annotations=(
            GoldenTeacherAnnotation("hair", GoldenDecisionLabel.REMOVED),
        ),
    )

    assert production_state == before
    assert a.to_dict() != b.to_dict()
    assert a.production_output_changed is False
    assert b.production_output_changed is False


def test_unknown_or_duplicate_golden_roles_fail_closed():
    with pytest.raises(ValueError, match="unknown production role"):
        build_semantic_golden_teacher_report(
            production_roles=("hair",),
            golden_annotations=(
                GoldenTeacherAnnotation("invented", GoldenDecisionLabel.SURVIVED),
            ),
        )

    duplicate = GoldenTeacherAnnotation("hair", GoldenDecisionLabel.SURVIVED)
    with pytest.raises(ValueError, match="duplicate"):
        build_semantic_golden_teacher_report(
            production_roles=("hair",),
            golden_annotations=(duplicate, duplicate),
        )


def test_authoritative_semantic_or_advisor_input_fails_closed():
    semantic = _semantic()
    semantic["authoritative"] = True
    with pytest.raises(ValueError, match="non-authoritative"):
        build_semantic_golden_teacher_report(
            production_roles=("hair",),
            semantic_retention=semantic,
        )

    advisor = _advisor()
    advisor["authoritative"] = True
    with pytest.raises(ValueError, match="non-authoritative"):
        build_semantic_golden_teacher_report(
            production_roles=("hair",),
            primitive_advisor=advisor,
        )


def test_unknown_semantic_or_advisor_role_fails_closed():
    with pytest.raises(ValueError, match="semantic retention references unknown"):
        build_semantic_golden_teacher_report(
            production_roles=("hair",),
            semantic_retention=_semantic({"invented": 0.9}),
        )

    advisor = _advisor()
    advisor["audits"][0]["role"] = "invented"
    with pytest.raises(ValueError, match="primitive advisor references unknown"):
        build_semantic_golden_teacher_report(
            production_roles=("hair",),
            primitive_advisor=advisor,
        )
