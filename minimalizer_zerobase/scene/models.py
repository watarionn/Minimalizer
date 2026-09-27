from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from minimalizer_zerobase import SCHEMA_VERSION
from minimalizer_zerobase.core.coordinates import CoordinateSpace
from minimalizer_zerobase.core.serialization import CanonicalModel

@dataclass(frozen=True)
class Relation(CanonicalModel):
    source_id: str
    target_id: str
    kind: str
    confidence: float | None = None

@dataclass(frozen=True)
class Region(CanonicalModel):
    region_id: str
    semantic_role: str
    evidence_ids: tuple[str, ...] = ()
    importance: float = 0.0
    confidence: float = 0.0
    geometry: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Subject(CanonicalModel):
    subject_id: str
    semantic_class: str
    region_ids: tuple[str, ...] = ()
    importance: float = 0.0
    confidence: float = 0.0

@dataclass(frozen=True)
class Scene(CanonicalModel):
    coordinate_space: CoordinateSpace
    producer: str
    producer_version: str
    subjects: tuple[Subject, ...] = ()
    regions: tuple[Region, ...] = ()
    relations: tuple[Relation, ...] = ()
    palette: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION
