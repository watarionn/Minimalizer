from __future__ import annotations
from dataclasses import dataclass
from math import hypot
from typing import Iterable, Mapping, Sequence

@dataclass(frozen=True)
class LossWeights:
    silhouette: float = 3.0
    palette: float = 1.0
    semantic: float = 2.0
    primitive_count: float = 0.12
    tiny_shape: float = 0.35
    complexity: float = 0.08

@dataclass(frozen=True)
class LossBreakdown:
    silhouette: float
    palette: float
    semantic: float
    primitive_count: float
    tiny_shape: float
    complexity: float
    total: float

@dataclass(frozen=True)
class AcceptancePolicy:
    min_identity_ratio: float = 0.985
    min_silhouette_ratio: float = 0.985
    min_improvement: float = 1e-6

def _mean(values: Iterable[float]) -> float:
    seq = tuple(float(v) for v in values)
    return sum(seq) / len(seq) if seq else 0.0

def palette_loss(reference_lab: Sequence[Sequence[float]], candidate_lab: Sequence[Sequence[float]]) -> float:
    if len(reference_lab) != len(candidate_lab):
        raise ValueError("palette samples must align")
    return _mean(hypot(hypot(a[0]-b[0], a[1]-b[1]), a[2]-b[2]) / 100.0
                 for a,b in zip(reference_lab,candidate_lab))

def cosine_loss(reference: Sequence[float], candidate: Sequence[float]) -> float:
    if len(reference) != len(candidate):
        raise ValueError("feature vectors must align")
    dot=sum(a*b for a,b in zip(reference,candidate))
    na=sum(a*a for a in reference) ** 0.5
    nb=sum(b*b for b in candidate) ** 0.5
    return 1.0 if na == 0.0 or nb == 0.0 else 1.0 - max(-1.0,min(1.0,dot/(na*nb)))

def objective(*, silhouette_iou: float, palette: float, semantic: float,
              primitive_count: int, tiny_shape_ratio: float, complexity: float,
              weights: LossWeights = LossWeights()) -> LossBreakdown:
    parts=dict(
        silhouette=(1.0-silhouette_iou)*weights.silhouette,
        palette=palette*weights.palette,
        semantic=semantic*weights.semantic,
        primitive_count=primitive_count*weights.primitive_count,
        tiny_shape=tiny_shape_ratio*weights.tiny_shape,
        complexity=complexity*weights.complexity,
    )
    return LossBreakdown(**parts,total=sum(parts.values()))

def accept_candidate(*, before: LossBreakdown, after: LossBreakdown,
                     identity_ratio: float, silhouette_ratio: float,
                     policy: AcceptancePolicy = AcceptancePolicy()) -> bool:
    return (identity_ratio >= policy.min_identity_ratio
            and silhouette_ratio >= policy.min_silhouette_ratio
            and before.total-after.total >= policy.min_improvement)
