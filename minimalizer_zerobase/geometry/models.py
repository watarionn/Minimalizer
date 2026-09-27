from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from minimalizer_zerobase import SCHEMA_VERSION
from minimalizer_zerobase.core.serialization import CanonicalModel

@dataclass(frozen=True)
class PrimitiveCandidate(CanonicalModel):
    candidate_id: str
    primitive_type: str
    source_region_id: str
    parameters: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    semantic_constraints: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class Primitive(CanonicalModel):
    primitive_id: str
    selected_candidate_id: str
    source_region_id: str
    fill_ref: str | None = None
    z_order: int = 0
    provenance: dict[str, Any] = field(default_factory=dict)
    selection_rationale: dict[str, float] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION
