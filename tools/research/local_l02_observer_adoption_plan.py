"""Fail-closed adoption plan for the six-capability L02 observer.

This module records the remaining research path when no already-qualified
observer checkpoint is available.  It is deliberately source-free: it does
not open images, masks, labels, or model weights.  A passing plan confirms
that the training/introduction route is concrete and auditable; it never
promotes a candidate to Phase4, Phase5, or production.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from tools.research.local_l02_observer_capability_gate import (
    REQUIRED_CAPABILITIES,
    REQUIRED_CASES,
    REQUIRED_UNKNOWN_POLICY,
)


class AdoptionPlanHold(ValueError):
    """Raised when an observer adoption plan is incomplete or unsafe."""


REQUIRED_MILESTONES = (
    "metadata_catalog",
    "train_validation_split",
    "blind_holdout_inference",
    "independent_phase4_review",
)


@dataclass(frozen=True)
class ObserverAdoptionPlan:
    plan_id: str
    revision: str
    target_capabilities: tuple[str, ...]
    required_cases: tuple[str, ...]
    required_milestones: tuple[str, ...]
    source_only: bool
    human_labels_used_for_inference: bool
    unknown_policy: str
    holdout_is_frozen_before_inference: bool
    phase4_before_phase5: bool
    production_authority: bool = False


def assess_adoption_plan(plan: ObserverAdoptionPlan) -> dict[str, object]:
    """Validate a concrete, source-free introduction plan."""
    if not isinstance(plan, ObserverAdoptionPlan):
        raise AdoptionPlanHold("INVALID_PLAN")
    if not plan.plan_id or not plan.revision:
        raise AdoptionPlanHold("INVALID_PLAN_IDENTITY")
    if set(plan.target_capabilities) != set(REQUIRED_CAPABILITIES):
        raise AdoptionPlanHold("INCOMPLETE_TARGET_CAPABILITIES")
    if tuple(plan.required_cases) != REQUIRED_CASES:
        raise AdoptionPlanHold("THREE_CASES_NOT_FIXED")
    if tuple(plan.required_milestones) != REQUIRED_MILESTONES:
        raise AdoptionPlanHold("INCOMPLETE_MILESTONES")
    if plan.source_only is not True:
        raise AdoptionPlanHold("NON_SOURCE_ONLY_PLAN")
    if plan.human_labels_used_for_inference is not False:
        raise AdoptionPlanHold("HUMAN_LABELS_IN_INFERENCE")
    if plan.unknown_policy != REQUIRED_UNKNOWN_POLICY:
        raise AdoptionPlanHold("UNKNOWN_NOT_SEPARATE_FROM_NEGATIVE")
    if plan.holdout_is_frozen_before_inference is not True:
        raise AdoptionPlanHold("HOLDOUT_NOT_FROZEN_BEFORE_INFERENCE")
    if plan.phase4_before_phase5 is not True:
        raise AdoptionPlanHold("PHASE5_BEFORE_PHASE4")
    if plan.production_authority is not False:
        raise AdoptionPlanHold("PLAN_CANNOT_GRANT_PRODUCTION_AUTHORITY")

    return {
        "schema": "minimalizer/l02/observer_adoption_plan/v1",
        "status": "ADOPTION_PLAN_PASS_RESEARCH_ONLY",
        "plan_id": plan.plan_id,
        "revision": plan.revision,
        "target_capabilities": tuple(sorted(REQUIRED_CAPABILITIES)),
        "required_cases": REQUIRED_CASES,
        "required_milestones": REQUIRED_MILESTONES,
        "source_only": True,
        "human_labels_used_for_inference": False,
        "unknown_policy": REQUIRED_UNKNOWN_POLICY,
        "phase4_before_phase5": True,
        "production_authority": False,
    }


def default_adoption_plan() -> ObserverAdoptionPlan:
    """Return the pinned plan used by the source-free research gate."""
    return ObserverAdoptionPlan(
        plan_id="l02-six-capability-observer-introduction",
        revision="20261120-r1",
        target_capabilities=tuple(sorted(REQUIRED_CAPABILITIES)),
        required_cases=REQUIRED_CASES,
        required_milestones=REQUIRED_MILESTONES,
        source_only=True,
        human_labels_used_for_inference=False,
        unknown_policy=REQUIRED_UNKNOWN_POLICY,
        holdout_is_frozen_before_inference=True,
        phase4_before_phase5=True,
        production_authority=False,
    )


def adoption_plan_summary() -> Mapping[str, object]:
    """Return the serialisable summary without touching private evidence."""
    return assess_adoption_plan(default_adoption_plan())
