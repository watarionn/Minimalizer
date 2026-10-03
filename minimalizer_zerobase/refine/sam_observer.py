from __future__ import annotations
from typing import Callable
from .regions import RegionObservation

class SamUnavailable(RuntimeError): pass

class SamObserver:
    """Frozen SAM-family adapter. It observes regions only and never edits pixels."""
    name="sam"
    def __init__(self, extractor: Callable[[object,tuple[str,...]],tuple[RegionObservation,...]] | None=None):
        if extractor is None: raise SamUnavailable("SAM extractor is optional and not configured")
        self._extractor=extractor
    def observe(self,image:object,concepts:tuple[str,...]=()) -> tuple[RegionObservation,...]:
        observations=self._extractor(image,concepts)
        if not isinstance(observations,tuple) or not all(isinstance(x,RegionObservation) for x in observations):
            raise TypeError("SAM extractor must return tuple[RegionObservation, ...]")
        labels=tuple(x.label for x in observations)
        if len(labels)!=len(set(labels)): raise ValueError("SAM observations contain duplicate labels")
        if concepts and labels != concepts: raise ValueError("SAM observation labels must align with requested concepts")
        return observations
