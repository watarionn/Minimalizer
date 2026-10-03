from __future__ import annotations
from typing import Callable
from minimalizer_zerobase.refine.semantic import SemanticObservation

class DinoV3Unavailable(RuntimeError):
    pass

class DinoV3Observer:
    """Frozen, observation-only DINOv3 adapter.

    The loader is injected so production Minimalizer has no hard DINO/transformers dependency.
    The returned model must expose an eval-style callable supplied by the research runtime.
    """
    name = "dinov3"

    def __init__(self, extractor: Callable[[object], SemanticObservation] | None = None):
        if extractor is None:
            raise DinoV3Unavailable("DINOv3 extractor is optional and not configured")
        self._extractor = extractor

    def observe(self, image: object) -> SemanticObservation:
        observation = self._extractor(image)
        if not isinstance(observation, SemanticObservation):
            raise TypeError("DINOv3 extractor must return SemanticObservation")
        return observation
