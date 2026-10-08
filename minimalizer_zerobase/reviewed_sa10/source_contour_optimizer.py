"""Research-only constrained replacement of an existing face/hair contour.

No primitive creation, owner mutation, material mutation or production scene writes.
"""
from __future__ import annotations
from dataclasses import dataclass
import cv2
import numpy as np
from .source_svg_contour_proposals import ContourProposal, propose_existing_contour


@dataclass(frozen=True)
class OptimizationDecision:
    status: str
    proposal: ContourProposal | None
    reason: str


def _topology(mask: np.ndarray) -> tuple[int, int]:
    _, hierarchy = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return (0, 0)
    parents = hierarchy[0][:, 3]
    return (int(np.count_nonzero(parents == -1)), int(np.count_nonzero(parents != -1)))


def optimize_existing_owner_contour(
    *, owner: str, existing_mask: np.ndarray, source_mask: np.ndarray,
    existing_primitive_count: int, proposed_primitive_count: int,
    existing_material: str, proposed_material: str,
    vertex_budget: int = 16, minimum_source_iou: float = 0.90,
    minimum_existing_iou: float = 0.90,
) -> OptimizationDecision:
    if owner not in ("face", "hair"):
        return OptimizationDecision("HOLD", None, "owner_not_eligible")
    if existing_primitive_count < 1 or proposed_primitive_count != existing_primitive_count:
        return OptimizationDecision("HOLD", None, "primitive_budget_changed")
    if not existing_material or proposed_material != existing_material:
        return OptimizationDecision("HOLD", None, "material_changed")
    a = np.asarray(existing_mask).astype(bool)
    b = np.asarray(source_mask).astype(bool)
    if a.ndim != 2 or b.shape != a.shape or not a.any() or not b.any():
        return OptimizationDecision("HOLD", None, "invalid_mask")
    if _topology(a) != _topology(b):
        return OptimizationDecision("HOLD", None, "source_topology_mismatch")
    proposal = propose_existing_contour(
        owner, a, b, vertex_budget=vertex_budget,
        min_iou=minimum_source_iou, require_improvement=True,
    )
    if proposal is None:
        return OptimizationDecision("HOLD", None, "no_safe_improving_contour")
    raster = np.zeros(a.shape, np.uint8)
    cv2.fillPoly(raster, [np.asarray(proposal.points_xy, np.int32)], 1)
    if _topology(raster) != _topology(a):
        return OptimizationDecision("HOLD", None, "candidate_topology_mismatch")
    if proposal.candidate_existing_iou < minimum_existing_iou:
        return OptimizationDecision("HOLD", None, "existing_geometry_divergence")
    return OptimizationDecision("RESEARCH_CANDIDATE_ONLY", proposal, "requires_full_scene_gates")
