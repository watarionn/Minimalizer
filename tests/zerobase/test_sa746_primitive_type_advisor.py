import cv2
import numpy as np
import pytest

from minimalizer_zerobase.semantic_abstraction.primitive_type_advisor import (
    PrimitiveAdvisorStatus,
    PrimitiveTypeSuggestion,
    analyze_primitive_geometry,
    audit_primitive_type_advice,
)


def _rectangle():
    mask = np.zeros((120, 120), bool)
    mask[20:80, 20:90] = True
    return mask


def _ellipse():
    mask = np.zeros((120, 120), np.uint8)
    cv2.ellipse(mask, (60, 60), (28, 20), 0, 0, 360, 1, -1)
    return mask.astype(bool)


def _line():
    mask = np.zeros((120, 120), bool)
    mask[55:59, 10:110] = True
    return mask


def _ribbon():
    mask = np.zeros((120, 120), bool)
    mask[48:64, 10:110] = True
    return mask


def _polygon():
    mask = np.zeros((120, 120), np.uint8)
    points = np.array(
        [[15, 20], [65, 10], [100, 45], [80, 100], [25, 90], [45, 55]],
        np.int32,
    )
    cv2.fillPoly(mask, [points], 1)
    return mask.astype(bool)


def test_deterministic_geometry_baseline_recognizes_basic_families():
    assert analyze_primitive_geometry("box", _rectangle()).deterministic_family == "rectangle"
    assert analyze_primitive_geometry("oval", _ellipse()).deterministic_family == "ellipse"
    assert analyze_primitive_geometry("stroke", _line()).deterministic_family == "line"
    assert analyze_primitive_geometry("band", _ribbon()).deterministic_family == "ribbon"
    assert analyze_primitive_geometry("irregular", _polygon()).deterministic_family == "polygon"


def test_unavailable_advisor_keeps_geometry_evidence_and_changes_nothing():
    report = audit_primitive_type_advice(
        {"hair": _polygon(), "major_clothing": _rectangle()},
        None,
    )

    assert report.status is PrimitiveAdvisorStatus.UNAVAILABLE
    assert report.audits == ()
    assert report.authoritative is False
    assert report.production_output_changed is False
    assert set(report.geometry_evidence) == {"hair", "major_clothing"}


def test_matching_advice_is_still_not_production_eligible():
    report = audit_primitive_type_advice(
        {"major_clothing": _rectangle()},
        (
            PrimitiveTypeSuggestion(
                role="major_clothing",
                primitive_family="rectangle",
                confidence=0.99,
                source="starvector-style-synthetic",
            ),
        ),
    )

    audit = report.audits[0]
    assert report.status is PrimitiveAdvisorStatus.AVAILABLE
    assert audit.family_agreement is True
    assert audit.renderer_supported is True
    assert audit.production_eligible is False
    assert "advisor_output_is_research_only" in audit.reasons


def test_high_confidence_disagreement_cannot_override_source_geometry():
    report = audit_primitive_type_advice(
        {"hair": _polygon()},
        (
            PrimitiveTypeSuggestion(
                role="hair",
                primitive_family="ellipse",
                confidence=1.0,
                source="external-advisor",
            ),
        ),
    )

    audit = report.audits[0]
    assert audit.family_agreement is False
    assert audit.production_eligible is False
    assert "advisor_family_disagrees_with_source_geometry_evidence" in audit.reasons


def test_line_or_ribbon_advice_is_recorded_but_not_renderer_authority():
    report = audit_primitive_type_advice(
        {"accent": _line()},
        (
            PrimitiveTypeSuggestion(
                role="accent",
                primitive_family="line",
                confidence=0.9,
                source="external-advisor",
            ),
        ),
    )

    audit = report.audits[0]
    assert audit.family_agreement is True
    assert audit.renderer_supported is False
    assert audit.production_eligible is False
    assert "advisor_family_not_currently_renderer_supported" in audit.reasons


def test_authoritative_advice_fails_closed():
    with pytest.raises(ValueError, match="non-authoritative"):
        PrimitiveTypeSuggestion(
            role="hair",
            primitive_family="polygon",
            confidence=0.9,
            source="bad-advisor",
            authoritative=True,
        )


def test_unknown_family_fails_closed():
    with pytest.raises(ValueError, match="unsupported"):
        PrimitiveTypeSuggestion(
            role="hair",
            primitive_family="bezier_magic",
            confidence=0.9,
            source="bad-advisor",
        )


def test_unknown_role_fails_closed():
    with pytest.raises(ValueError, match="unknown role"):
        audit_primitive_type_advice(
            {"hair": _polygon()},
            (
                PrimitiveTypeSuggestion(
                    role="invented",
                    primitive_family="polygon",
                    confidence=0.5,
                    source="external-advisor",
                ),
            ),
        )


def test_duplicate_role_suggestions_fail_closed():
    suggestion = PrimitiveTypeSuggestion(
        role="hair",
        primitive_family="polygon",
        confidence=0.5,
        source="external-advisor",
    )
    with pytest.raises(ValueError, match="duplicate"):
        audit_primitive_type_advice(
            {"hair": _polygon()},
            (suggestion, suggestion),
        )


def test_geometry_evidence_is_deterministic():
    a = analyze_primitive_geometry("hair", _polygon()).to_dict()
    b = analyze_primitive_geometry("hair", _polygon()).to_dict()
    assert a == b
