"""Validate the evidence needed for a whole-body L02 observer probe.

The capability-name gate is intentionally small.  This layer validates the
actual source-only arrays that a probe would consume, so a broad ``topwear``
mask cannot be presented as outerwear/underlayer/sleeve/arm/occlusion
authority by metadata alone.

This module never creates an owner map.  Missing or conflicting evidence is a
hold, and pixels without positive evidence remain unknown rather than
negative.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np


class ObserverEvidenceHold(ValueError):
    """Raised when source-only observer evidence is not admissible."""


REQUIRED_MASK_ROLES = frozenset({"outerwear", "underlayer", "sleeve", "arm"})
REQUIRED_CAPABILITIES = frozenset(
    {*REQUIRED_MASK_ROLES, "occlusion_relation", "instance_grouping"}
)


@dataclass(frozen=True)
class RoleObservation:
    role: str
    mask: np.ndarray
    expected_sha256: str
    observer_id: str


@dataclass(frozen=True)
class ScalarObservation:
    capability: str
    values: np.ndarray
    expected_sha256: str
    observer_id: str


@dataclass(frozen=True)
class ObserverEvidenceAssessment:
    status: str
    formal_probe_allowed: bool
    source_only: bool
    human_labels_used: bool
    owner_arrays_used: bool
    unknown_not_treated_as_negative: bool
    observed_capabilities: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    reason: str


def _sha256(array: np.ndarray) -> str:
    return hashlib.sha256(array.tobytes(order="C")).hexdigest()


def _validate_sha(array: np.ndarray, expected: str, error: str) -> None:
    if type(expected) is not str or len(expected) != 64 or _sha256(array) != expected:
        raise ObserverEvidenceHold(error)


def _validate_source_alpha(source_alpha: np.ndarray) -> tuple[int, int]:
    if (
        type(source_alpha) is not np.ndarray
        or source_alpha.dtype != np.bool_
        or source_alpha.ndim != 2
        or not source_alpha.size
    ):
        raise ObserverEvidenceHold("INVALID_SOURCE_ALPHA")
    return source_alpha.shape


def assess_observer_evidence(
    *,
    source_alpha: np.ndarray,
    role_observations: tuple[RoleObservation, ...],
    occlusion_relation: ScalarObservation | None,
    instance_grouping: ScalarObservation | None,
    source_only: bool = True,
    human_labels_used: bool = False,
    owner_arrays_used: bool = False,
) -> ObserverEvidenceAssessment:
    """Validate a complete source-only observer evidence bundle.

    ``occlusion_relation.values`` uses ``-1`` for behind, ``1`` for in front,
    and ``0`` for unknown.  ``instance_grouping.values`` uses zero for
    ungrouped/unknown pixels and positive integer IDs for observed instances.
    Neither array assigns an owner; they are only evidence for a later
    component-level solver.
    """

    shape = _validate_source_alpha(source_alpha)
    if source_only is not True:
        raise ObserverEvidenceHold("NON_SOURCE_ONLY_OBSERVER")
    if human_labels_used is not False:
        raise ObserverEvidenceHold("HUMAN_LABELS_IN_INFERENCE")
    if owner_arrays_used is not False:
        raise ObserverEvidenceHold("FROZEN_OWNER_IN_INFERENCE")
    if not isinstance(role_observations, tuple):
        raise ObserverEvidenceHold("INVALID_ROLE_OBSERVATIONS")

    seen_roles: set[str] = set()
    seen_observers: set[str] = set()
    for observation in role_observations:
        if not isinstance(observation, RoleObservation):
            raise ObserverEvidenceHold("INVALID_ROLE_OBSERVATION")
        if (
            observation.role not in REQUIRED_MASK_ROLES
            or observation.role in seen_roles
            or not isinstance(observation.observer_id, str)
            or not observation.observer_id
            or observation.observer_id in seen_observers
        ):
            raise ObserverEvidenceHold("INVALID_ROLE_OBSERVATION")
        mask = observation.mask
        if (
            type(mask) is not np.ndarray
            or mask.dtype != np.bool_
            or mask.ndim != 2
            or mask.shape != shape
        ):
            raise ObserverEvidenceHold("INVALID_ROLE_MASK")
        _validate_sha(mask, observation.expected_sha256, "ROLE_MASK_SHA_MISMATCH")
        if np.any(mask & ~source_alpha):
            raise ObserverEvidenceHold("ROLE_MASK_OUTSIDE_SOURCE_ALPHA")
        seen_roles.add(observation.role)
        seen_observers.add(observation.observer_id)

    def validate_scalar(
        observation: ScalarObservation | None,
        capability: str,
        dtype: np.dtype,
        allowed: set[int] | None = None,
    ) -> None:
        if not isinstance(observation, ScalarObservation) or observation.capability != capability:
            raise ObserverEvidenceHold(f"MISSING_{capability.upper()}")
        if (
            type(observation.observer_id) is not str
            or not observation.observer_id
            or observation.observer_id in seen_observers
        ):
            raise ObserverEvidenceHold("INVALID_SCALAR_OBSERVATION")
        values = observation.values
        if type(values) is not np.ndarray or values.dtype != dtype or values.shape != shape:
            raise ObserverEvidenceHold(f"INVALID_{capability.upper()}")
        _validate_sha(values, observation.expected_sha256, f"{capability.upper()}_SHA_MISMATCH")
        if capability == "occlusion_relation":
            if np.any(~np.isin(values, (-1, 0, 1))):
                raise ObserverEvidenceHold("INVALID_OCCLUSION_VALUES")
        elif allowed is not None and np.any(~np.isin(values, tuple(allowed))):
            raise ObserverEvidenceHold("INVALID_INSTANCE_VALUES")

    missing = tuple(sorted(REQUIRED_MASK_ROLES - seen_roles))
    if missing:
        return ObserverEvidenceAssessment(
            status="CAPABILITY_HOLD",
            formal_probe_allowed=False,
            source_only=True,
            human_labels_used=False,
            owner_arrays_used=False,
            unknown_not_treated_as_negative=True,
            observed_capabilities=tuple(sorted(seen_roles)),
            missing_capabilities=missing + ("occlusion_relation", "instance_grouping"),
            reason="required role evidence is missing",
        )

    validate_scalar(
        occlusion_relation,
        "occlusion_relation",
        np.dtype(np.int8),
    )
    validate_scalar(
        instance_grouping,
        "instance_grouping",
        np.dtype(np.uint32),
    )
    observed = tuple(sorted(REQUIRED_CAPABILITIES))
    return ObserverEvidenceAssessment(
        status="CAPABILITY_PASS_RESEARCH_ONLY",
        formal_probe_allowed=True,
        source_only=True,
        human_labels_used=False,
        owner_arrays_used=False,
        unknown_not_treated_as_negative=True,
        observed_capabilities=observed,
        missing_capabilities=(),
        reason="source-only evidence contract is complete; Phase4 remains separate",
    )
