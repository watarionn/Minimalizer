from __future__ import annotations
from typing import Callable
from minimalizer_zerobase.refine.regions import RegionObservation

class SamUnavailable(RuntimeError):
    pass

class SamObserver:
    """Frozen SAM-family adapter. Segmentation observations only; never generation or mutation."""
    name = "sam"

    def __init__(self, extractor: Callable[[object], tuple[RegionObservation, ...]] | None = None):
        if extractor is None:
            raise SamUnavailable("SAM extractor is optional and not configured")
        self._extractor = extractor

    def observe(self, image: object) -> tuple[RegionObservation, ...]:
        observations = self._extractor(image)
        if not isinstance(observations, tuple) or not all(isinstance(x, RegionObservation) for x in observations):
            raise TypeError("SAM extractor must return tuple[RegionObservation, ...]")
        labels = [x.label for x in observations]
        if len(labels) != len(set(labels)):
            raise ValueError("SAM observations contain duplicate labels")
        return observations
