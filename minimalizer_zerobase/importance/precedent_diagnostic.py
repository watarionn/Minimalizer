from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

from minimalizer_zerobase.analyzers.contracts import Evidence
from minimalizer_zerobase.importance.omission import (
    IDENTITY_ROLE_SCORES,
    SEMANTIC_ROLE_SCORES,
)
from minimalizer_zerobase.semantic_abstraction.semantic_retention_observer import (
    SemanticRetentionReport,
)
from minimalizer_zerobase.semantic_abstraction.primitive_type_advisor import (
    PrimitiveAdvisorReport,
)


PB3_DIAGNOSTIC_VERSION = "pb3-v1"


class PB3Recommendation(str, Enum):
    RETAIN_EVIDENCE = "retain-evidence"
    MERGE_CANDIDATE_EVIDENCE = "merge-candidate-evidence"
    OMISSION_CANDIDATE_EVIDENCE = "omission-candidate-evidence"
    INSUFFICIENT_EVIDENCE = "insufficient-evidence"


@dataclass(frozen=True)
class ComponentImportanceDiagnostic:
    component_id: str
    role: str
    support_ratio: float
    sibling_count: int
    role_semantic_importance: float
    role_identity_importance: float
    semantic_retention: float | None
    removal_impact: float | None
    merge_retention: float | None
    merge_impact: float | None
    merge_target_id: str | None
    primitive_advisor_status: str
    primitive_advisor_agreement: bool | None
    primitive_suggested_family: str | None
    primitive_source_family: str | None
    recommendation: PB3Recommendation
    reasons: tuple[str, ...]
    authority_state: str
    authoritative: bool = False
    production_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "role": self.role,
            "support_ratio": round(float(self.support_ratio), 12),
            "sibling_count": self.sibling_count,
            "role_semantic_importance": round(float(self.role_semantic_importance), 6),
            "role_identity_importance": round(float(self.role_identity_importance), 6),
            "semantic_retention": self.semantic_retention,
            "removal_impact": self.removal_impact,
            "merge_retention": self.merge_retention,
            "merge_impact": self.merge_impact,
            "merge_target_id": self.merge_target_id,
            "primitive_advisor_status": self.primitive_advisor_status,
            "primitive_advisor_agreement": self.primitive_advisor_agreement,
            "primitive_suggested_family": self.primitive_suggested_family,
            "primitive_source_family": self.primitive_source_family,
            "recommendation": self.recommendation.value,
            "reasons": list(self.reasons),
            "authority_state": self.authority_state,
            "authoritative": False,
            "production_action": None,
        }


@dataclass(frozen=True)
class PB3ImportanceDiagnosticReport:
    components: tuple[ComponentImportanceDiagnostic, ...]
    context_semantic_retention: Mapping[str, Any] | None
    hard_failures: tuple[str, ...]
    recommendation_counts: Mapping[str, int]
    authoritative: bool = False
    can_override_hard_fail: bool = False
    production_policy_changed: bool = False
    production_output_changed: bool = False
    version: str = PB3_DIAGNOSTIC_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "components": [item.to_dict() for item in self.components],
            "context_semantic_retention": (
                dict(self.context_semantic_retention)
                if self.context_semantic_retention is not None
                else None
            ),
            "hard_failures": list(self.hard_failures),
            "recommendation_counts": dict(sorted(self.recommendation_counts.items())),
            "authoritative": False,
            "can_override_hard_fail": False,
            "production_policy_changed": False,
            "production_output_changed": False,
        }


def _retention_payload(
    value: SemanticRetentionReport | Mapping[str, Any] | None,
    *,
    label: str,
) -> dict[str, Any] | None:
    if value is None:
        return None
    payload = value.to_dict() if isinstance(value, SemanticRetentionReport) else dict(value)
    if payload.get("authoritative") is not False:
        raise ValueError(f"{label} semantic retention must be non-authoritative")
    if payload.get("can_override_hard_fail") is not False:
        raise ValueError(f"{label} semantic retention cannot override hard fail")
    score = payload.get("semantic_retention_score")
    if score is not None:
        score = float(score)
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"{label} semantic retention score must be within [0, 1]")
        payload["semantic_retention_score"] = score
    return payload


def _impact(
    payload: Mapping[str, Any] | None,
) -> tuple[float | None, float | None]:
    if payload is None:
        return None, None
    score = payload.get("semantic_retention_score")
    if score is None:
        return None, None
    retention = float(score)
    return retention, round(1.0 - retention, 12)


def _advisor_payload(
    value: PrimitiveAdvisorReport | Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if value is None:
        return None
    payload = value.to_dict() if isinstance(value, PrimitiveAdvisorReport) else dict(value)
    if payload.get("authoritative") is not False:
        raise ValueError("primitive advisor must be non-authoritative")
    if payload.get("production_output_changed") is not False:
        raise ValueError("primitive advisor must not change production output in PB3")
    return payload


def _primitive_context(
    role: str,
    advisor: Mapping[str, Any] | None,
) -> tuple[str, bool | None, str | None, str | None]:
    if advisor is None:
        return "UNAVAILABLE", None, None, None

    status = str(advisor.get("status", "UNAVAILABLE"))
    geometry = advisor.get("geometry_evidence") or {}
    role_geometry = geometry.get(role) or {}
    source_family = role_geometry.get("deterministic_family")

    audit = None
    for item in advisor.get("audits") or ():
        if item.get("role") == role:
            audit = item
            break

    if audit is None:
        return status, None, None, source_family

    suggestion = audit.get("suggestion") or {}
    return (
        status,
        bool(audit.get("family_agreement")),
        suggestion.get("primitive_family"),
        source_family,
    )


def _component_records(evidence: Iterable[Evidence]) -> tuple[Evidence, ...]:
    rows = tuple(
        sorted(
            (
                item
                for item in evidence
                if item.evidence_type == "region_component"
            ),
            key=lambda item: item.evidence_id,
        )
    )
    if not rows:
        raise ValueError("PB3 requires PB2 region_component Evidence")

    ids = [item.evidence_id for item in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("PB3 component evidence ids must be unique")

    for item in rows:
        authority = item.normalization.get("authority")
        if not isinstance(authority, Mapping):
            raise ValueError(f"{item.evidence_id}: missing authority provenance")
        if authority.get("production_authority") is not False:
            raise ValueError(
                f"{item.evidence_id}: PB3 requires non-authoritative PB2 evidence"
            )
        if str(authority.get("state", "")) not in {"observed", "advisor"}:
            raise ValueError(
                f"{item.evidence_id}: unsupported PB3 evidence authority state"
            )
        support = item.geometry.get("support_ratio")
        if support is None or not 0.0 <= float(support) <= 1.0:
            raise ValueError(f"{item.evidence_id}: invalid support_ratio")
    return rows


def _recommend(
    *,
    support_ratio: float,
    sibling_count: int,
    role_identity_importance: float,
    removal_impact: float | None,
    merge_impact: float | None,
    merge_target_id: str | None,
) -> tuple[PB3Recommendation, tuple[str, ...]]:
    reasons: list[str] = []

    if removal_impact is None and merge_impact is None:
        return (
            PB3Recommendation.INSUFFICIENT_EVIDENCE,
            ("semantic_impact_observation_unavailable",),
        )

    if removal_impact is not None and removal_impact >= 0.15:
        return (
            PB3Recommendation.RETAIN_EVIDENCE,
            ("observed_removal_semantic_impact",),
        )

    if (
        merge_impact is not None
        and merge_target_id is not None
        and merge_impact <= 0.03
        and sibling_count > 1
    ):
        return (
            PB3Recommendation.MERGE_CANDIDATE_EVIDENCE,
            (
                "observed_low_merge_semantic_impact",
                "same_role_has_multiple_components",
            ),
        )

    if (
        removal_impact is not None
        and removal_impact <= 0.03
        and support_ratio <= 0.05
        and sibling_count > 1
        and role_identity_importance < 0.80
    ):
        return (
            PB3Recommendation.OMISSION_CANDIDATE_EVIDENCE,
            (
                "observed_low_removal_semantic_impact",
                "low_source_support",
                "same_role_has_multiple_components",
                "role_not_high_identity_guard",
            ),
        )

    if removal_impact is not None:
        reasons.append("semantic_observation_does_not_support_safe_omission")
    if merge_impact is not None:
        reasons.append("semantic_observation_does_not_support_safe_merge")
    if role_identity_importance >= 0.80:
        reasons.append("high_identity_role_context")
    if support_ratio > 0.05:
        reasons.append("nontrivial_source_support")
    if sibling_count <= 1:
        reasons.append("no_same_role_sibling_component")

    return (
        PB3Recommendation.RETAIN_EVIDENCE,
        tuple(reasons or ("retain_by_fail_safe_default",)),
    )


def build_pb3_importance_diagnostic(
    *,
    pb2_evidence: Iterable[Evidence],
    removal_retention_by_component: Mapping[
        str, SemanticRetentionReport | Mapping[str, Any]
    ] | None = None,
    merge_retention_by_component: Mapping[
        str, SemanticRetentionReport | Mapping[str, Any]
    ] | None = None,
    merge_target_by_component: Mapping[str, str] | None = None,
    primitive_advisor: PrimitiveAdvisorReport | Mapping[str, Any] | None = None,
    context_semantic_retention: (
        SemanticRetentionReport | Mapping[str, Any] | None
    ) = None,
    hard_failures: Iterable[str] = (),
) -> PB3ImportanceDiagnosticReport:
    """Build PB3 diagnostic evidence without changing production policy.

    Removal/merge impact is only derived from explicit semantic-retention
    observations supplied for that component. Area/support alone can never
    manufacture an omission recommendation.
    """
    components = _component_records(pb2_evidence)
    removal = dict(removal_retention_by_component or {})
    merge = dict(merge_retention_by_component or {})
    targets = dict(merge_target_by_component or {})
    known_ids = {item.evidence_id for item in components}

    unknown = (set(removal) | set(merge) | set(targets)) - known_ids
    if unknown:
        raise ValueError(
            "PB3 semantic evidence references unknown components: "
            + ", ".join(sorted(unknown))
        )

    advisor = _advisor_payload(primitive_advisor)
    context = _retention_payload(
        context_semantic_retention,
        label="context",
    )

    sibling_counts: dict[str, int] = {}
    for item in components:
        role = str(item.semantic_label or "unknown")
        sibling_counts[role] = sibling_counts.get(role, 0) + 1

    diagnostics: list[ComponentImportanceDiagnostic] = []
    for item in components:
        role = str(item.semantic_label or "unknown")
        support_ratio = float(item.geometry["support_ratio"])
        authority = item.normalization["authority"]
        authority_state = str(authority["state"])

        removal_payload = _retention_payload(
            removal.get(item.evidence_id),
            label=f"{item.evidence_id}:removal",
        )
        merge_payload = _retention_payload(
            merge.get(item.evidence_id),
            label=f"{item.evidence_id}:merge",
        )
        removal_retention, removal_impact = _impact(removal_payload)
        merge_retention, merge_impact = _impact(merge_payload)
        merge_target_id = targets.get(item.evidence_id)
        if merge_payload is not None and merge_target_id is None:
            raise ValueError(
                f"{item.evidence_id}: merge semantic evidence requires merge target"
            )
        if merge_target_id is not None:
            if merge_target_id not in known_ids:
                raise ValueError(
                    f"{item.evidence_id}: merge target is unknown"
                )
            if merge_target_id == item.evidence_id:
                raise ValueError(
                    f"{item.evidence_id}: merge target must be another component"
                )

        semantic_importance = float(
            SEMANTIC_ROLE_SCORES.get(role, 0.5)
        )
        identity_importance = float(
            IDENTITY_ROLE_SCORES.get(role, 0.5)
        )
        (
            advisor_status,
            advisor_agreement,
            suggested_family,
            source_family,
        ) = _primitive_context(role, advisor)

        recommendation, reasons = _recommend(
            support_ratio=support_ratio,
            sibling_count=sibling_counts[role],
            role_identity_importance=identity_importance,
            removal_impact=removal_impact,
            merge_impact=merge_impact,
            merge_target_id=merge_target_id,
        )

        diagnostics.append(
            ComponentImportanceDiagnostic(
                component_id=item.evidence_id,
                role=role,
                support_ratio=support_ratio,
                sibling_count=sibling_counts[role],
                role_semantic_importance=semantic_importance,
                role_identity_importance=identity_importance,
                semantic_retention=removal_retention,
                removal_impact=removal_impact,
                merge_retention=merge_retention,
                merge_impact=merge_impact,
                merge_target_id=merge_target_id,
                primitive_advisor_status=advisor_status,
                primitive_advisor_agreement=advisor_agreement,
                primitive_suggested_family=suggested_family,
                primitive_source_family=source_family,
                recommendation=recommendation,
                reasons=reasons,
                authority_state=authority_state,
            )
        )

    counts: dict[str, int] = {}
    for item in diagnostics:
        key = item.recommendation.value
        counts[key] = counts.get(key, 0) + 1

    failures = tuple(sorted(str(item) for item in hard_failures))
    return PB3ImportanceDiagnosticReport(
        components=tuple(diagnostics),
        context_semantic_retention=context,
        hard_failures=failures,
        recommendation_counts=counts,
    )
