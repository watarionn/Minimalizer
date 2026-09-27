from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from minimalizer_zerobase import SCHEMA_VERSION
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.core.serialization import CanonicalModel

@dataclass(frozen=True)
class Provenance(CanonicalModel):
    producer: str
    producer_version: str
    model_id: str | None = None
    model_version: str | None = None

@dataclass(frozen=True)
class Evidence(CanonicalModel):
    evidence_id: str
    evidence_type: str
    coordinate_space: CoordinateSpace
    provenance: Provenance
    confidence: float | None = None
    semantic_label: str | None = None
    geometry: dict[str, Any] = field(default_factory=dict)
    normalization: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1: raise ValueError("confidence must be 0..1")

class AnalyzerAdapter(ABC):
    @property
    @abstractmethod
    def adapter_id(self) -> str: ...

    @abstractmethod
    def analyze(self, image: Any, coordinate_space: CoordinateSpace) -> list[Evidence]: ...
