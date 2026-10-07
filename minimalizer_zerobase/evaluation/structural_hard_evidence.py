from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.semantic_abstraction.anatomy_guard import (
    AnatomyGuardResult,
    anatomy_integrity_gate,
)
from minimalizer_zerobase.semantic_abstraction.evidence_adapter import (
    build_semantic_abstraction_evidence,
)
from minimalizer_zerobase.structure.graph import (
    build_structural_layout_graph,
    graph_validation,
)

SA10_STRUCTURAL_HARD_EVIDENCE_VERSION = "sa10.10-v1"


def _normalize_masks(
    masks: Mapping[str, np.ndarray],
    *,
    shape: tuple[int, int],
) -> dict[str, np.ndarray]:
    return {
        name: (
            np.asarray(masks[name]).astype(bool)
            if name in masks
            else np.zeros(shape, dtype=bool)
        )
        for name in PART_NAMES
    }


@dataclass(frozen=True)
class StructuralHardEvidenceReport:
    anatomy: AnatomyGuardResult
    source_topology_validation: dict
    candidate_topology_validation: dict
    anatomy_pass: bool
    topology_pass: bool
    version: str = SA10_STRUCTURAL_HARD_EVIDENCE_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "anatomy": {
                "status": "AVAILABLE",
                "passed": self.anatomy_pass,
                "details": self.anatomy.to_dict(),
            },
            "topology": {
                "status": "AVAILABLE",
                "passed": self.topology_pass,
                "source_validation": self.source_topology_validation,
                "candidate_validation": self.candidate_topology_validation,
            },
            "phase14_metric_relabeling": False,
        }


def evaluate_structural_hard_evidence(
    *,
    source_masks: Mapping[str, np.ndarray],
    candidate_masks: Mapping[str, np.ndarray],
    accessory_kind: str = "none",
    accessory_confidence: float = 0.0,
) -> StructuralHardEvidenceReport:
    source_any = next((np.asarray(v) for v in source_masks.values()), None)
    candidate_any = next((np.asarray(v) for v in candidate_masks.values()), None)
    if source_any is None or candidate_any is None:
        raise ValueError("source and candidate masks are required")
    if source_any.ndim != 2 or candidate_any.ndim != 2:
        raise ValueError("2D masks are required")
    if source_any.shape != candidate_any.shape:
        raise ValueError("source/candidate mask frames must align")

    shape = source_any.shape
    source = _normalize_masks(source_masks, shape=shape)
    candidate = _normalize_masks(candidate_masks, shape=shape)

    source_graph = build_structural_layout_graph(
        source,
        accessory_kind=accessory_kind,
        accessory_confidence=accessory_confidence,
    )
    candidate_graph = build_structural_layout_graph(
        candidate,
        accessory_kind=accessory_kind,
        accessory_confidence=accessory_confidence,
    )
    source_validation = graph_validation(source_graph)
    candidate_validation = graph_validation(candidate_graph)

    baseline_plan = build_semantic_abstraction_evidence(
        part_masks=source,
        graph=source_graph,
    )
    candidate_plan = build_semantic_abstraction_evidence(
        part_masks=candidate,
        graph=candidate_graph,
    )
    anatomy = anatomy_integrity_gate(baseline_plan, candidate_plan)

    return StructuralHardEvidenceReport(
        anatomy=anatomy,
        source_topology_validation=source_validation,
        candidate_topology_validation=candidate_validation,
        anatomy_pass=anatomy.passed,
        topology_pass=bool(source_validation["pass"] and candidate_validation["pass"]),
    )
