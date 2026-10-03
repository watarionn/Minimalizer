from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Sequence
from minimalizer_zerobase.refine.objective import cosine_loss

FeatureVector = tuple[float, ...]
PatchFeatures = tuple[FeatureVector, ...]

@dataclass(frozen=True)
class SemanticObservation:
    global_feature: FeatureVector
    patch_features: PatchFeatures = ()

class SemanticObserver(Protocol):
    """Read-only observer. Implementations return features and cannot mutate Scene/VectorScene."""
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
        patch_part = sum(cosine_loss(a, b) for a, b in zip(reference.patch_features, candidate.patch_features)) / len(reference.patch_features)
    else:
        patch_weight = 0.0
    denom = global_weight + patch_weight
    return (global_weight * global_part + patch_weight * patch_part) / denom

def identity_ratio_from_loss(loss: float) -> float:
    return max(0.0, min(1.0, 1.0 - float(loss)))
