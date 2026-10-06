from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

from minimalizer_zerobase.semantic_abstraction.primitive_type_advisor import (
    PrimitiveAdvisorReport,
)
from minimalizer_zerobase.semantic_abstraction.semantic_retention_observer import (
    SemanticRetentionReport,
)


SEMANTIC_GOLDEN_TEACHER_VERSION = "sa9-v1"


class GoldenDecisionLabel(str, Enum):
    SURVIVED = "SURVIVED"
    SIMPLIFIED = "SIMPLIFIED"
    REMOVED = "REMOVED"
    REAUTHORED = "REAUTHORED"


@dataclass(frozen=True)
class GoldenTeacherAnnotation:
    role: str
    decision: GoldenDecisionLabel
    primitive_family: str | None = None
    rationale: str = ""
    source: str = "golden-evaluation"

    def __post_init__(self) -> None:
        if not self.role:
            raise ValueError("Golden teacher role is required")
        if self.source != "golden-evaluation":
            raise ValueError("Golden teacher annotations must be evaluation-only")

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "decision": self.decision.value,
            "primitive_family": self.primitive_family,
            "rationale": self.rationale,
            "source": self.source,
            "authority": {
                "state": "teacher-evaluation",
                "production_authority": False,
            },
        }


@dataclass(frozen=True)
class SemanticGoldenTeacherRoleAudit:
    role: str
    golden_decision: GoldenDecisionLabel | None
    semantic_retention: float | None
    primitive_suggested_family: str | None
    primitive_source_family: str | None
    primitive_family_agreement: bool | None
    golden_primitive_family: str | None
    golden_advisor_agreement: bool | None
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "golden_decision": (
                self.golden_decision.value if self.golden_decision is not None else None
            ),
            "semantic_retention": self.semantic_retention,
            "primitive_suggested_family": self.primitive_suggested_family,
            "primitive_source_family": self.primitive_source_family,
            "primitive_family_agreement": self.primitive_family_agreement,
            "golden_primitive_family": self.golden_primitive_family,
            "golden_advisor_agreement": self.golden_advisor_agreement,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class SemanticGoldenTeacherReport:
    roles: tuple[SemanticGoldenTeacherRoleAudit, ...]
    semantic_retention: Mapping[str, Any] | None
    primitive_advisor: Mapping[str, Any] | None
    provenance: Mapping[str, Any]
    authoritative: bool = False
    can_override_hard_fail: bool = False
    production_input_allowed: bool = False
    production_output_changed: bool = False
    version: str = SEMANTIC_GOLDEN_TEACHER_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "roles": [row.to_dict() for row in self.roles],
            "semantic_retention": (
                dict(self.semantic_retention)
                if self.semantic_retention is not None
                else None
            ),
            "primitive_advisor": (
                dict(self.primitive_advisor)
                if self.primitive_advisor is not None
                else None
            ),
            "provenance": dict(self.provenance),
            "authoritative": False,
            "can_override_hard_fail": False,
            "production_input_allowed": False,
            "production_output_changed": False,
        }


def _semantic_payload(
    value: SemanticRetentionReport | Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if value is None:
        return None
    payload = value.to_dict() if isinstance(value, SemanticRetentionReport) else dict(value)
    if payload.get("authoritative") is not False:
        raise ValueError("semantic retention must be non-authoritative")
    if payload.get("can_override_hard_fail") is not False:
        raise ValueError("semantic retention cannot override hard fail")
    return payload


def _advisor_payload(
    value: PrimitiveAdvisorReport | Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if value is None:
        return None
    payload = value.to_dict() if isinstance(value, PrimitiveAdvisorReport) else dict(value)
    if payload.get("authoritative") is not False:
        raise ValueError("primitive advisor must be non-authoritative")
    if payload.get("production_output_changed") is not False:
        raise ValueError("primitive advisor must not change production output")
    return payload


def build_semantic_golden_teacher_report(
    *,
    production_roles: Iterable[str],
    golden_annotations: Iterable[GoldenTeacherAnnotation] = (),
    semantic_retention: SemanticRetentionReport | Mapping[str, Any] | None = None,
    primitive_advisor: PrimitiveAdvisorReport | Mapping[str, Any] | None = None,
    case_id: str | None = None,
) -> SemanticGoldenTeacherReport:
    """Join production role names with evaluation-only Golden teacher labels.

    Golden coordinates, masks, colors, raster data, and geometry are deliberately
    absent from this contract. The result is diagnostic-only and cannot feed
    production inference.
    """
    roles = tuple(sorted({str(role) for role in production_roles if str(role)}))
    if not roles:
        raise ValueError("SA9 requires at least one production semantic role")

    annotations: dict[str, GoldenTeacherAnnotation] = {}
    for annotation in golden_annotations:
        if annotation.role in annotations:
            raise ValueError(f"duplicate Golden teacher role: {annotation.role}")
        if annotation.role not in roles:
            raise ValueError(
                f"Golden teacher annotation references unknown production role: {annotation.role}"
            )
        annotations[annotation.role] = annotation

    semantic = _semantic_payload(semantic_retention)
    advisor = _advisor_payload(primitive_advisor)

    role_similarity = (semantic or {}).get("role_similarity") or {}
    unknown_semantic_roles = set(role_similarity) - set(roles)
    if unknown_semantic_roles:
        raise ValueError(
            "semantic retention references unknown production roles: "
            + ", ".join(sorted(unknown_semantic_roles))
        )

    advisor_by_role: dict[str, Mapping[str, Any]] = {}
    if advisor is not None:
        for audit in advisor.get("audits") or ():
            role = str(audit.get("role", ""))
            if role and role not in roles:
                raise ValueError(
                    f"primitive advisor references unknown production role: {role}"
                )
            if role:
                advisor_by_role[role] = audit

    rows: list[SemanticGoldenTeacherRoleAudit] = []
    for role in roles:
        annotation = annotations.get(role)
        audit = advisor_by_role.get(role)
        suggestion = (audit or {}).get("suggestion") or {}
        geometry = (audit or {}).get("geometry") or {}
        suggested = suggestion.get("primitive_family")
        source_family = geometry.get("deterministic_family")
        family_agreement = (
            bool(audit.get("family_agreement")) if audit is not None else None
        )
        golden_family = annotation.primitive_family if annotation is not None else None
        golden_advisor_agreement = (
            golden_family == suggested
            if golden_family is not None and suggested is not None
            else None
        )

        reasons: list[str] = []
        if annotation is None:
            reasons.append("golden_teacher_label_unavailable")
        else:
            reasons.append("golden_teacher_label_evaluation_only")
        if role not in role_similarity:
            reasons.append("role_semantic_retention_unavailable")
        if audit is None:
            reasons.append("primitive_advisor_audit_unavailable")

        rows.append(
            SemanticGoldenTeacherRoleAudit(
                role=role,
                golden_decision=annotation.decision if annotation is not None else None,
                semantic_retention=(
                    float(role_similarity[role]) if role in role_similarity else None
                ),
                primitive_suggested_family=suggested,
                primitive_source_family=source_family,
                primitive_family_agreement=family_agreement,
                golden_primitive_family=golden_family,
                golden_advisor_agreement=golden_advisor_agreement,
                reasons=tuple(reasons),
            )
        )

    return SemanticGoldenTeacherReport(
        roles=tuple(rows),
        semantic_retention=semantic,
        primitive_advisor=advisor,
        provenance={
            "case_id": case_id,
            "golden_source": "evaluation-only",
            "golden_raster_used": False,
            "golden_coordinates_used": False,
            "golden_masks_used": False,
            "golden_colors_used": False,
            "golden_geometry_used": False,
            "production_roles_source": "production-semantic-role-names",
        },
    )
