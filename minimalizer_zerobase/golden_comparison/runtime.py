"""Runtime boundary for Golden Gap evaluation and optional Event Hub delivery.

The evaluator stays pure. This module owns the post-evaluation observational
boundary: build one event envelope, attempt fail-open delivery, and preserve
that exact envelope for explicit retries.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from minimalizer_zerobase.golden_comparison.event_hub_client import (
    make_event_hub_sender_from_environment,
)
from minimalizer_zerobase.golden_comparison.events import build_golden_evaluated_event
from minimalizer_zerobase.golden_comparison.golden_gap import evaluate_golden_gap
from minimalizer_zerobase.golden_comparison.shadow import (
    ShadowDeliveryResult,
    deliver_shadow,
)


@dataclass(frozen=True)
class GoldenEvaluationRuntimeResult:
    report: dict[str, Any]
    event: dict[str, Any] | None
    delivery: ShadowDeliveryResult | None
    integration_error: str | None = None


def evaluate_golden_and_shadow(
    *,
    case_id: str,
    feature_survival_report: Mapping[str, Any],
    dimension_scores: Mapping[str, Any],
    run_id: str,
    previous_report: Mapping[str, Any] | None = None,
    feature_local_evidence: Mapping[str, Any] | None = None,
    allowed_feature_ids: set[str] | None = None,
    send: Callable[[Mapping[str, Any]], Any] | None = None,
    occurred_at: str | None = None,
    event_id: str | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
    hop_count: int = 0,
) -> GoldenEvaluationRuntimeResult:
    """Evaluate natively, then attempt observational shadow delivery.

    Native evaluation errors still fail closed. Once a valid report exists,
    all Event Hub integration work is fail-open and cannot invalidate it.
    """
    report = evaluate_golden_gap(
        case_id=case_id,
        feature_survival_report=feature_survival_report,
        dimension_scores=dimension_scores,
        feature_local_evidence=feature_local_evidence,
        allowed_feature_ids=allowed_feature_ids,
    )

    event: dict[str, Any] | None = None
    try:
        event = build_golden_evaluated_event(
            report,
            previous_report=previous_report,
            run_id=run_id,
            occurred_at=occurred_at,
            event_id=event_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            hop_count=hop_count,
        )
        delivery = deliver_shadow(event, send)
    except Exception as exc:
        return GoldenEvaluationRuntimeResult(
            report=report,
            event=event,
            delivery=None,
            integration_error=type(exc).__name__,
        )

    return GoldenEvaluationRuntimeResult(
        report=report,
        event=event,
        delivery=delivery,
        integration_error=None,
    )


def evaluate_golden_runtime(
    *,
    case_id: str,
    feature_survival_report: Mapping[str, Any],
    dimension_scores: Mapping[str, Any],
    run_id: str,
    previous_report: Mapping[str, Any] | None = None,
    feature_local_evidence: Mapping[str, Any] | None = None,
    allowed_feature_ids: set[str] | None = None,
    environ: Mapping[str, str] | None = None,
    occurred_at: str | None = None,
    event_id: str | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
    hop_count: int = 0,
) -> GoldenEvaluationRuntimeResult:
    """Canonical runtime callsite using optional Event Hub environment config."""
    sender = make_event_hub_sender_from_environment(environ)
    return evaluate_golden_and_shadow(
        case_id=case_id,
        feature_survival_report=feature_survival_report,
        dimension_scores=dimension_scores,
        run_id=run_id,
        previous_report=previous_report,
        feature_local_evidence=feature_local_evidence,
        allowed_feature_ids=allowed_feature_ids,
        send=sender,
        occurred_at=occurred_at,
        event_id=event_id,
        correlation_id=correlation_id,
        causation_id=causation_id,
        hop_count=hop_count,
    )


def retry_golden_shadow(
    result: GoldenEvaluationRuntimeResult,
    send: Callable[[Mapping[str, Any]], Any] | None,
) -> ShadowDeliveryResult:
    """Retry only delivery, reusing the exact event envelope from evaluation."""
    if result.event is None:
        raise ValueError("Golden runtime result has no event envelope to retry")
    return deliver_shadow(result.event, send)
