"""Guarded differentiable geometry transaction for SA10.22.

The optimizer is deliberately proposal-oriented: it can only replace parameters
of primitives already present in the canonical VectorScene.  Every proposal is
evaluated before it becomes the new baseline.  SA10.18 anatomy/silhouette and
SA10.20 topology are hard gates; SA10.19/21 are improvement evidence only.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Mapping

import numpy as np

from minimalizer_zerobase.compose import VectorScene
from minimalizer_zerobase.evaluation.saliency_perceptual import evaluate_saliency_perceptual
from minimalizer_zerobase.evaluation.source_shape_evidence import evaluate_source_shape_evidence
from minimalizer_zerobase.evaluation.structural_hard_evidence import evaluate_structural_hard_evidence
from .backend import backend_available
from .geometry import GeometryProposal, apply_geometry_proposals


@dataclass(frozen=True)
class DiffvgTransactionPolicy:
    min_shape_improvement: float = 1e-9
    min_region_improvement: float = 1e-9


@dataclass(frozen=True)
class ProposalResult:
    proposal_id: str
    accepted: bool
    rollback: bool
    reason: str
    shape_before: float | None
    shape_after: float | None
    region_before: float | None
    region_after: float | None
    hard_pass: bool


@dataclass(frozen=True)
class DiffvgTransaction:
    scene: VectorScene
    backend: str
    optimized: bool
    proposals: tuple[ProposalResult, ...]


def _shape_score(evidence: dict) -> float | None:
    value = evidence.get("match_shapes_i1")
    return None if value is None else -float(value)


def _region_score(evidence: dict) -> float | None:
    value = evidence.get("aggregate_score")
    return None if value is None else float(value)


def _protected_region_worsening(before: dict, after: dict, threshold: float) -> bool:
    """Reject a candidate when any available protected region materially regresses.

    The aggregate is observer-only evidence and is intentionally not consulted.
    """
    before_rows = before.get("regions", {})
    after_rows = after.get("regions", {})
    for name, row in before_rows.items():
        old = row.get("score")
        new = after_rows.get(name, {}).get("score")
        if row.get("available") and old is not None and new is not None:
            if float(new) < float(old) - threshold:
                return True
    return False


def run_constrained_diffvg(
    scene: VectorScene,
    *,
    source_masks: Mapping[str, np.ndarray],
    candidate_masks: Callable[[VectorScene], Mapping[str, np.ndarray]],
    source_rgb: np.ndarray,
    candidate_rgb: Callable[[VectorScene], np.ndarray],
    proposals: tuple[GeometryProposal, ...],
    backend: str = "diffvg",
    policy: DiffvgTransactionPolicy = DiffvgTransactionPolicy(),
) -> DiffvgTransaction:
    """Evaluate proposals one at a time and commit only individually safe steps.

    A missing diffvg backend is a visible deterministic no-op.  It never returns
    ``optimized=True`` and never pretends the fallback was diffvg.
    """
    if backend != "diffvg" or not backend_available("diffvg"):
        return DiffvgTransaction(scene, "fallback_noop", False, tuple(
            ProposalResult("backend", False, True, "diffvg-unavailable-fallback-noop", None, None, None, None, False)
            for _ in [0]
        ))

    current = scene
    results: list[ProposalResult] = []
    for index, proposal in enumerate(proposals):
        before_masks = candidate_masks(current)
        before_shape = evaluate_source_shape_evidence(
            np.logical_or.reduce(list(source_masks.values())),
            np.logical_or.reduce(list(before_masks.values())),
        )
        before_rgb = candidate_rgb(current)
        before_region = evaluate_saliency_perceptual(source_rgb, before_rgb, source_masks)
        candidate = apply_geometry_proposals(current, (proposal,))
        after_masks = candidate_masks(candidate)
        hard = evaluate_structural_hard_evidence(source_masks=source_masks, candidate_masks=after_masks)
        after_shape = evaluate_source_shape_evidence(
            np.logical_or.reduce(list(source_masks.values())),
            np.logical_or.reduce(list(after_masks.values())),
        )
        after_region = evaluate_saliency_perceptual(source_rgb, candidate_rgb(candidate), source_masks)
        sb, sa = _shape_score(before_shape), _shape_score(after_shape)
        rb, ra = _region_score(before_region), _region_score(after_region)
        region_improved = any(
            before_region.get("regions", {}).get(name, {}).get("score") is not None
            and after_region.get("regions", {}).get(name, {}).get("score") is not None
            and after_region["regions"][name]["score"] > before_region["regions"][name]["score"] + policy.min_region_improvement
            for name in before_region.get("regions", {})
        )
        protected_worsened = _protected_region_worsening(
            before_region, after_region, policy.min_region_improvement)
        improved = ((sa is not None and sb is not None and sa > sb + policy.min_shape_improvement)
                    or region_improved)
        accepted = bool(hard.anatomy_pass and hard.topology_pass and improved and not protected_worsened)
        reason = "accepted-hard-gates-and-evidence-improved" if accepted else (
            "hard-gate-regression-rollback" if not (hard.anatomy_pass and hard.topology_pass)
            else "protected-region-worsening-rollback" if protected_worsened
            else "no-source-shape-or-region-improvement-rollback")
        results.append(ProposalResult(str(index), accepted, not accepted, reason, sb, sa, rb, ra,
                                      bool(hard.anatomy_pass and hard.topology_pass)))
        if accepted:
            current = candidate
    return DiffvgTransaction(current, "diffvg", bool(results and any(r.accepted for r in results)), tuple(results))
