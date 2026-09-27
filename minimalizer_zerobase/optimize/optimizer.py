from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Mapping
from minimalizer_zerobase import SCHEMA_VERSION
from minimalizer_zerobase.core.serialization import CanonicalModel
from minimalizer_zerobase.geometry.models import PrimitiveCandidate
from minimalizer_zerobase.scene.models import Scene

@dataclass(frozen=True)
class GeometryObjectivePolicy:
    coverage_weight: float = 3.0
    silhouette_weight: float = 2.0
    complexity_weight: float = 0.12
    angularity_weight: float = 0.25
    semantic_weight: float = 0.5
    undercoverage_weight: float = 4.0
    min_coverage: float = 0.70
    min_silhouette: float = 0.65
    semantic_angularity_targets: dict[str, float] = field(default_factory=lambda: {
        "background": 1.0, "coat": 0.9, "shirt": 0.9,
        "identity_accent": 0.75, "face": 0.15, "head": 0.15,
        "hair": 0.55, "arm": 0.45, "leg": 0.45, "hand": 0.25,
    })

@dataclass(frozen=True)
class CandidateSelectionDecision(CanonicalModel):
    region_id: str
    selected_candidate_id: str
    primitive_type: str
    score: float
    costs: dict[str, float] = field(default_factory=dict)
    rejected_candidate_ids: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class GeometryOptimizationResult(CanonicalModel):
    selections: dict[str, str] = field(default_factory=dict)
    decisions: tuple[CandidateSelectionDecision, ...] = ()
    provenance: dict[str, object] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

class GeometryOptimizer:
    producer = "GeometryOptimizer"
    producer_version = "1.0"

    def __init__(self, policy: GeometryObjectivePolicy | None = None):
        self.policy = policy or GeometryObjectivePolicy()

    def optimize(self, scene: Scene, candidates: Iterable[PrimitiveCandidate]) -> GeometryOptimizationResult:
        regions = {r.region_id: r for r in scene.regions}
        candidate_list = tuple(candidates)
        ids = [c.candidate_id for c in candidate_list]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate primitive candidate_id")

        grouped: dict[str, list[PrimitiveCandidate]] = {}
        for candidate in candidate_list:
            if candidate.source_region_id not in regions:
                raise ValueError("candidate references unknown region")
            grouped.setdefault(candidate.source_region_id, []).append(candidate)
        decisions = []
        for region_id in sorted(grouped):
            region = regions[region_id]
            scored = []
            rejected = []
            for candidate in sorted(grouped[region_id], key=lambda c: c.candidate_id):
                costs = self._costs(region.semantic_role, candidate)
                if costs["coverage"] > 1.0 - self.policy.min_coverage or costs["silhouette"] > 1.0 - self.policy.min_silhouette:
                    rejected.append(candidate.candidate_id)
                    continue
                score = self._score(costs)
                scored.append((round(score, 12), candidate.candidate_id, candidate, costs))
            if not scored:
                raise ValueError(f"no candidate passes quality gates for region: {region_id}")
            score, _, selected, costs = min(scored, key=lambda item: (item[0], item[1]))
            decisions.append(CandidateSelectionDecision(
                region_id, selected.candidate_id, selected.primitive_type, score,
                costs, tuple(sorted(rejected)),
            ))
        selections = {d.region_id: d.selected_candidate_id for d in decisions}
        provenance = {
            "producer": self.producer, "producer_version": self.producer_version,
            "policy": self._policy_dict(), "selection_authority": self.producer,
        }
        return GeometryOptimizationResult(selections, tuple(decisions), provenance)

    def _costs(self, semantic_role: str, candidate: PrimitiveCandidate) -> dict[str, float]:
        metrics = candidate.metrics
        required = {"coverage", "silhouette", "complexity", "angularity"}
        if not required <= metrics.keys():
            raise ValueError("candidate missing required optimizer metrics")
        coverage = self._unit(metrics["coverage"], "coverage")
        silhouette = self._unit(metrics["silhouette"], "silhouette")
        angularity = self._unit(metrics["angularity"], "angularity")
        complexity = float(metrics["complexity"])
        if complexity < 0:
            raise ValueError("complexity must be non-negative")
        target = self.policy.semantic_angularity_targets.get(semantic_role, 0.5)
        semantic_cost = abs(angularity - target)
        return {
            "coverage": round(1.0 - coverage, 12),
            "silhouette": round(1.0 - silhouette, 12),
            "complexity": round(complexity, 12),
            "angularity": round(1.0 - angularity, 12),
            "semantic": round(semantic_cost, 12),
            "undercoverage": round(max(0.0, self.policy.min_coverage - coverage), 12),
        }

    def _score(self, c: Mapping[str, float]) -> float:
        p = self.policy
        return (p.coverage_weight*c["coverage"] + p.silhouette_weight*c["silhouette"] +
                p.complexity_weight*c["complexity"] + p.angularity_weight*c["angularity"] +
                p.semantic_weight*c["semantic"] + p.undercoverage_weight*c["undercoverage"])

    def _policy_dict(self) -> dict[str, object]:
        p = self.policy
        return {
            "coverage_weight": p.coverage_weight, "silhouette_weight": p.silhouette_weight,
            "complexity_weight": p.complexity_weight, "angularity_weight": p.angularity_weight,
            "semantic_weight": p.semantic_weight, "undercoverage_weight": p.undercoverage_weight,
            "min_coverage": p.min_coverage, "min_silhouette": p.min_silhouette,
            "semantic_angularity_targets": [[k, p.semantic_angularity_targets[k]]
                                             for k in sorted(p.semantic_angularity_targets)],
        }

    @staticmethod
    def _unit(value: float, name: str) -> float:
        value = float(value)
        if value < 0.0 or value > 1.0:
            raise ValueError(f"{name} must be between 0 and 1")
        return value
