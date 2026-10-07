"""SA10.18 source-evidence silhouette/anatomy gate.

This is an evaluation contract only.  It never creates geometry and no
perceptual or saliency score can override a structural hard failure.
"""
from __future__ import annotations

from typing import Any, Mapping
import cv2
import numpy as np


def _topology(mask: np.ndarray) -> tuple[int, int]:
    binary = (mask > 0).astype(np.uint8)
    components, _, _, _ = cv2.connectedComponentsWithStats(binary, 8)
    padded = cv2.copyMakeBorder(binary, 1, 1, 1, 1, cv2.BORDER_CONSTANT)
    holes, _, _, _ = cv2.connectedComponentsWithStats(1 - padded, 8)
    return max(0, components - 1), max(0, holes - 1)  # label 0 is not a component


def _iou(source: np.ndarray, candidate: np.ndarray) -> float:
    a, b = source > 0, candidate > 0
    union = int(np.count_nonzero(a | b))
    return 1.0 if union == 0 else float(np.count_nonzero(a & b) / union)


def evaluate_source_silhouette_anatomy(
    source_mask: np.ndarray,
    candidate_mask: np.ndarray,
    *,
    fragmentation_penalty: float,
    anatomy_evidence: Mapping[str, Any] | None = None,
    silhouette_iou_minimum: float = 0.96,
    fragmentation_threshold: float = 0.20,
) -> dict[str, Any]:
    """Return a fail-closed SA10.18 report for source and candidate masks."""
    if source_mask.shape != candidate_mask.shape or source_mask.ndim != 2:
        raise ValueError("source and candidate masks must be same-size 2D arrays")
    if not 0 <= fragmentation_penalty <= 1:
        raise ValueError("fragmentation_penalty must be in [0, 1]")
    evidence = dict(anatomy_evidence or {})
    source_topology = _topology(source_mask)
    candidate_topology = _topology(candidate_mask)
    iou = _iou(source_mask, candidate_mask)
    hard_failures: list[str] = []
    if iou < silhouette_iou_minimum:
        hard_failures.append("source_silhouette_iou_below_minimum")
    if fragmentation_penalty > fragmentation_threshold:
        hard_failures.append("fragmentation_above_0.20")
    if source_topology != candidate_topology:
        hard_failures.append("source_topology_changed")
    required = evidence.get("required_parts", ())
    retained = evidence.get("retained_parts", ())
    if required and not set(required).issubset(set(retained)):
        hard_failures.append("required_anatomy_evidence_missing")
    scores = {k: evidence[k] for k in ("shape_matching", "saliency", "perceptual") if k in evidence}
    return {
        "schema_version": "sa10.18-source-silhouette-anatomy-gate-v1",
        "gate": "PASS" if not hard_failures else "FAIL",
        "hard_failures": hard_failures,
        "can_override_hard_fail": False,
        "source_evidence": {"mask_pixels": int(np.count_nonzero(source_mask)), "topology": source_topology},
        "candidate_evidence": {"mask_pixels": int(np.count_nonzero(candidate_mask)), "topology": candidate_topology},
        "metrics": {"silhouette_iou": iou, "fragmentation_penalty": float(fragmentation_penalty), **scores},
        "policy": {"silhouette_iou_minimum": silhouette_iou_minimum, "fragmentation_threshold": fragmentation_threshold,
                   "vectorization_authority": False, "shape_matching_authority": False,
                   "topology_preservation_hard": True, "saliency_perceptual_observer_only": True},
    }
