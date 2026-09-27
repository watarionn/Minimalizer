from __future__ import annotations
from dataclasses import dataclass, field
import json
from pathlib import Path
from statistics import fmean
from typing import Iterable, Mapping, Sequence
from minimalizer_zerobase.geometry import PrimitiveCandidate
from minimalizer_zerobase.optimize import GeometryObjectivePolicy, GeometryOptimizer
from minimalizer_zerobase.scene.models import Scene

@dataclass(frozen=True)
class ApprovedReference:
    index: int
    name: str
    reference_filename: str
    scene_artifact: str
    candidate_artifact: str

@dataclass(frozen=True)
class Approved78Binding:
    references: tuple[ApprovedReference, ...]
    corpus_id: str = "Approved-78"
    revision: str = "2026-09-18"

    def validate(self) -> None:
        if len(self.references) != 78:
            raise ValueError("Approved-78 binding must contain exactly 78 references")
        indexes = tuple(r.index for r in self.references)
        if indexes != tuple(range(1, 79)):
            raise ValueError("Approved-78 indexes must be exactly 1..78")
        if len({r.reference_filename for r in self.references}) != 78:
            raise ValueError("Approved-78 reference filenames must be unique")
        for r in self.references:
            if not r.scene_artifact or not r.candidate_artifact:
                raise ValueError("every reference requires saved Scene and candidate artifacts")

@dataclass(frozen=True)
class CalibrationCase:
    reference: ApprovedReference
    scene: Scene
    candidates: tuple[PrimitiveCandidate, ...]

@dataclass(frozen=True)
class CalibrationMetrics:
    case_count: int
    region_count: int
    mean_coverage: float
    mean_silhouette: float
    mean_complexity: float
    mean_angularity: float
    mean_semantic_cost: float
    rejected_candidate_rate: float
    primitive_type_rates: dict[str, float] = field(default_factory=dict)

@dataclass(frozen=True)
class CalibrationTargets:
    min_mean_coverage: float = 0.90
    min_mean_silhouette: float = 0.88
    max_mean_complexity: float = 4.5
    min_mean_angularity: float = 0.55
    max_mean_semantic_cost: float = 0.22

@dataclass(frozen=True)
class CalibrationResult:
    policy: GeometryObjectivePolicy
    metrics: CalibrationMetrics
    loss: float

def load_approved78_binding(path: str | Path) -> Approved78Binding:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    refs = tuple(ApprovedReference(
        int(item["index"]), Path(item["reference_filename"]).stem,
        str(item["reference_filename"]), str(item["scene_artifact"]),
        str(item["candidate_artifact"]),
    ) for item in payload["references"])
    binding = Approved78Binding(refs, str(payload["corpus_id"]), str(payload["revision"]))
    binding.validate()
    return binding

class Approved78CalibrationHarness:
    def __init__(self, binding: Approved78Binding, targets: CalibrationTargets | None = None):
        binding.validate()
        self.binding = binding
        self.targets = targets

    def evaluate(self, cases: Iterable[CalibrationCase],
                 policy: GeometryObjectivePolicy | None = None) -> CalibrationMetrics:
        policy = policy or GeometryObjectivePolicy()
        case_list = tuple(cases)
        self._validate_cases(case_list)
        selected: list[tuple[PrimitiveCandidate, Mapping[str, float]]] = []
        rejected = total = 0
        type_counts: dict[str, int] = {}
        for case in case_list:
            optimizer = GeometryOptimizer(policy)
            result = optimizer.optimize(case.scene, case.candidates)
            by_id = {c.candidate_id: c for c in case.candidates}
            total += len(case.candidates)
            for decision in result.decisions:
                candidate = by_id[decision.selected_candidate_id]
                selected.append((candidate, decision.costs))
                rejected += len(decision.rejected_candidate_ids)
                type_counts[candidate.primitive_type] = type_counts.get(candidate.primitive_type, 0) + 1
        if not selected:
            raise ValueError("calibration cases produced no selected primitives")
        n = len(selected)
        return CalibrationMetrics(
            len(case_list), n,
            round(fmean(1.0-c[1]["coverage"] for c in selected), 12),
            round(fmean(1.0-c[1]["silhouette"] for c in selected), 12),
            round(fmean(c[0].metrics["complexity"] for c in selected), 12),
            round(fmean(c[0].metrics["angularity"] for c in selected), 12),
            round(fmean(c[1]["semantic"] for c in selected), 12),
            round(rejected / total if total else 0.0, 12),
            {k: round(v/n, 12) for k, v in sorted(type_counts.items())},
        )

    def calibrate(self, cases: Iterable[CalibrationCase],
                  policies: Sequence[GeometryObjectivePolicy]) -> CalibrationResult:
        case_list = tuple(cases)
        if self.targets is None:
            raise ValueError("calibration targets must be explicitly supplied")
        if not policies:
            raise ValueError("at least one calibration policy is required")
        ranked = []
        for policy in policies:
            metrics = self.evaluate(case_list, policy)
            loss = self._loss(metrics)
            signature = tuple(sorted(GeometryOptimizer(policy)._policy_dict().items(), key=lambda x: x[0]))
            ranked.append((round(loss, 12), repr(signature), policy, metrics))
        loss, _, policy, metrics = min(ranked, key=lambda x: (x[0], x[1]))
        return CalibrationResult(policy, metrics, loss)

    def _validate_cases(self, cases: tuple[CalibrationCase, ...]) -> None:
        known = {r.index: r for r in self.binding.references}
        seen = set()
        for case in cases:
            idx = case.reference.index
            if idx not in known or known[idx] != case.reference:
                raise ValueError("case is not bound to canonical Approved-78 reference")
            if idx in seen:
                raise ValueError("duplicate Approved-78 calibration case")
            seen.add(idx)
            if not case.candidates:
                raise ValueError("calibration case requires candidates")

    def _loss(self, m: CalibrationMetrics) -> float:
        if self.targets is None:
            raise ValueError("calibration targets must be explicitly supplied")
        t = self.targets
        return (
            max(0.0, t.min_mean_coverage-m.mean_coverage)*4.0 +
            max(0.0, t.min_mean_silhouette-m.mean_silhouette)*3.0 +
            max(0.0, m.mean_complexity-t.max_mean_complexity)*0.25 +
            max(0.0, t.min_mean_angularity-m.mean_angularity) +
            max(0.0, m.mean_semantic_cost-t.max_mean_semantic_cost)*2.0
        )

