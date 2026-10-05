from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

import numpy as np

from minimalizer_zerobase.structure.graph import StructuralLayoutGraph

from .anatomy_guard import AnatomyGuardResult, anatomy_integrity_gate
from .evidence_adapter import build_semantic_abstraction_evidence
from .face_feature_evidence import (
    FaceFeatureEvidence,
    attach_facial_feature_evidence,
    detect_facial_feature_evidence,
)
from .face_neutralization import face_neutralization_gate
from .ir import AbstractionPlan, AbstractionPolicy
from .policy import apply_importance_policy


_ANATOMY_ALLOCATION_IDS = ("head", "torso", "left_arm", "right_arm", "lower_body")


@dataclass(frozen=True)
class SemanticRenderGuardResult:
    safe_allocations: dict[str, int]
    face_evidence: FaceFeatureEvidence
    face_gate: dict[str, object]
    anatomy_before_restore: AnatomyGuardResult
    anatomy_after_restore: AnatomyGuardResult

    @property
    def passed(self) -> bool:
        return bool(self.face_gate.get("pass")) and self.anatomy_after_restore.passed

    def to_dict(self) -> dict:
        return {
            "pass": self.passed,
            "safe_allocations": dict(sorted(self.safe_allocations.items())),
            "face_evidence": self.face_evidence.to_dict(),
            "face_gate": self.face_gate,
            "anatomy_before_restore": self.anatomy_before_restore.to_dict(),
            "anatomy_after_restore": self.anatomy_after_restore.to_dict(),
        }


def _allocation_candidate(
    plan: AbstractionPlan,
    allocations: Mapping[str, int],
) -> AbstractionPlan:
    parts = []
    for part in plan.parts:
        if part.id in _ANATOMY_ALLOCATION_IDS and allocations.get(part.id, 0) < 1:
            parts.append(replace(part, abstraction_policy=AbstractionPolicy.SUPPRESS))
        else:
            parts.append(part)
    return AbstractionPlan(parts=tuple(parts), schema_version=plan.schema_version)


def build_semantic_render_guard(
    rgb: np.ndarray,
    masks: Mapping[str, np.ndarray],
    graph: StructuralLayoutGraph,
    allocations: Mapping[str, int],
) -> SemanticRenderGuardResult:
    baseline = apply_importance_policy(
        build_semantic_abstraction_evidence(part_masks=masks, graph=graph)
    )

    face_mask = np.asarray(masks.get("face", np.zeros(rgb.shape[:2], dtype=np.uint8)))
    if np.any(face_mask):
        face_evidence = detect_facial_feature_evidence(rgb, face_mask)
        semantic_plan = attach_facial_feature_evidence(baseline, face_evidence)
        face_gate = face_neutralization_gate(semantic_plan)
    else:
        face_evidence = FaceFeatureEvidence((), False, False, 0.0)
        semantic_plan = baseline
        face_gate = {
            "pass": True,
            "applicable": False,
            "face_surface_count": 0,
            "unsuppressed_facial_features": [],
        }

    candidate = _allocation_candidate(semantic_plan, allocations)
    before_restore = anatomy_integrity_gate(semantic_plan, candidate)

    safe_allocations = {str(key): int(value) for key, value in allocations.items()}
    for part_id in before_restore.suppressed_parts:
        if part_id in _ANATOMY_ALLOCATION_IDS:
            safe_allocations[part_id] = max(1, safe_allocations.get(part_id, 0))

    restored = _allocation_candidate(semantic_plan, safe_allocations)
    after_restore = anatomy_integrity_gate(semantic_plan, restored)

    return SemanticRenderGuardResult(
        safe_allocations=safe_allocations,
        face_evidence=face_evidence,
        face_gate=face_gate,
        anatomy_before_restore=before_restore,
        anatomy_after_restore=after_restore,
    )
