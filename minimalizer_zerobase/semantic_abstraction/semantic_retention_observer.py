from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from minimalizer_zerobase.refine.objective import cosine_loss
from minimalizer_zerobase.refine.semantic import SemanticObservation


SEMANTIC_RETENTION_VERSION = "sa7.45-v1"


class SemanticRetentionStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class SemanticRetentionReport:
    observer: str
    status: SemanticRetentionStatus
    global_similarity: float | None
    patch_similarity: float | None
    role_similarity: Mapping[str, float]
    semantic_retention_score: float | None
    fidelity_score: float | None
    simplicity_score: float | None
    reasons: tuple[str, ...]
    authoritative: bool = False
    can_override_hard_fail: bool = False
    version: str = SEMANTIC_RETENTION_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "observer": self.observer,
            "status": self.status.value,
            "global_similarity": self.global_similarity,
            "patch_similarity": self.patch_similarity,
            "role_similarity": dict(sorted(self.role_similarity.items())),
            "semantic_retention_score": self.semantic_retention_score,
            "fidelity_score": self.fidelity_score,
            "simplicity_score": self.simplicity_score,
            "authoritative": self.authoritative,
            "can_override_hard_fail": self.can_override_hard_fail,
            "reasons": list(self.reasons),
        }


def _similarity(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    loss = cosine_loss(a, b)
    # cosine_loss spans [0, 2]; expose an intuitive [0, 1] observer score.
    return max(0.0, min(1.0, 1.0 - loss / 2.0))


def _patch_similarity(
    source: SemanticObservation,
    candidate: SemanticObservation,
) -> tuple[float | None, str | None]:
    source_has = bool(source.patch_features)
    candidate_has = bool(candidate.patch_features)
    if not source_has and not candidate_has:
        return None, None
    if source_has != candidate_has:
        return None, "patch_feature_availability_mismatch"
    if len(source.patch_features) != len(candidate.patch_features):
        return None, "patch_feature_count_mismatch"
    if not source.patch_features:
        return None, None
    scores = [
        _similarity(a, b)
        for a, b in zip(source.patch_features, candidate.patch_features)
    ]
    return sum(scores) / len(scores), None


def evaluate_semantic_retention(
    *,
    observer: str,
    source: SemanticObservation | None,
    candidate: SemanticObservation | None,
    source_roles: Mapping[str, SemanticObservation] | None = None,
    candidate_roles: Mapping[str, SemanticObservation] | None = None,
    simplicity_score: float | None = None,
) -> SemanticRetentionReport:
    """Observer-only semantic-retention diagnostic.

    This function never changes geometry or rendering. External models may
    provide frozen SemanticObservation values, but the report is explicitly
    non-authoritative and cannot override hard semantic/safety gates.
    """
    if not observer:
        raise ValueError("observer name is required")
    if simplicity_score is not None and not 0.0 <= float(simplicity_score) <= 1.0:
        raise ValueError("simplicity_score must be within [0, 1]")

    if source is None or candidate is None:
        return SemanticRetentionReport(
            observer=observer,
            status=SemanticRetentionStatus.UNAVAILABLE,
            global_similarity=None,
            patch_similarity=None,
            role_similarity={},
            semantic_retention_score=None,
            fidelity_score=None,
            simplicity_score=simplicity_score,
            reasons=("global_observation_unavailable",),
        )

    reasons: list[str] = []
    global_similarity = _similarity(
        source.global_feature,
        candidate.global_feature,
    )
    patch_similarity, patch_reason = _patch_similarity(source, candidate)
    if patch_reason:
        reasons.append(patch_reason)

    source_roles = dict(source_roles or {})
    candidate_roles = dict(candidate_roles or {})
    all_roles = sorted(set(source_roles) | set(candidate_roles))
    role_similarity: dict[str, float] = {}

    for role in all_roles:
        src = source_roles.get(role)
        cand = candidate_roles.get(role)
        if src is None or cand is None:
            reasons.append(f"role_observation_missing:{role}")
            continue
        role_similarity[role] = _similarity(
            src.global_feature,
            cand.global_feature,
        )

    terms = [global_similarity]
    if patch_similarity is not None:
        terms.append(patch_similarity)
    if role_similarity:
        terms.append(sum(role_similarity.values()) / len(role_similarity))
    retention = sum(terms) / len(terms)

    status = (
        SemanticRetentionStatus.DEGRADED
        if reasons
        else SemanticRetentionStatus.AVAILABLE
    )

    return SemanticRetentionReport(
        observer=observer,
        status=status,
        global_similarity=global_similarity,
        patch_similarity=patch_similarity,
        role_similarity=role_similarity,
        semantic_retention_score=retention,
        fidelity_score=retention,
        simplicity_score=simplicity_score,
        reasons=tuple(reasons),
    )
