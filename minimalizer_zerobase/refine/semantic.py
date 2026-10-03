from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from minimalizer_zerobase.refine.objective import AcceptancePolicy, LossBreakdown, accept_candidate, cosine_loss

FeatureVector = tuple[float, ...]
PatchFeatures = tuple[FeatureVector, ...]

@dataclass(frozen=True)
class SemanticObservation:
    global_feature: FeatureVector
    patch_features: PatchFeatures = ()

class SemanticObserver(Protocol):
    """Read-only observer. Implementations return frozen features only."""
    name: str
    def observe(self, image: object) -> SemanticObservation: ...

def semantic_feature_loss(reference: SemanticObservation, candidate: SemanticObservation,
                          *, global_weight: float = 0.5, patch_weight: float = 0.5) -> float:
    if global_weight < 0 or patch_weight < 0 or global_weight + patch_weight <= 0:
        raise ValueError("semantic weights must be non-negative with positive sum")
    global_part = cosine_loss(reference.global_feature, candidate.global_feature)
    if bool(reference.patch_features) != bool(candidate.patch_features):
        raise ValueError("patch feature availability must align")
    patch_part = 0.0
    if reference.patch_features:
        if len(reference.patch_features) != len(candidate.patch_features):
            raise ValueError("patch feature grids must align")
        patch_part = sum(cosine_loss(a,b) for a,b in zip(reference.patch_features,candidate.patch_features))/len(reference.patch_features)
    else:
        patch_weight = 0.0
    return (global_weight*global_part + patch_weight*patch_part)/(global_weight+patch_weight)

def identity_ratio_from_loss(loss: float) -> float:
    return max(0.0, min(1.0, 1.0-float(loss)))

def accept_with_semantic_observation(*, before: LossBreakdown, after: LossBreakdown,
                                     reference: SemanticObservation, candidate: SemanticObservation,
                                     silhouette_ratio: float,
                                     policy: AcceptancePolicy = AcceptancePolicy()) -> bool:
    """Feed frozen observer evidence into the existing hard acceptance gate."""
    semantic_loss = semantic_feature_loss(reference, candidate)
    return accept_candidate(before=before, after=after,
                            identity_ratio=identity_ratio_from_loss(semantic_loss),
                            silhouette_ratio=silhouette_ratio, policy=policy)
