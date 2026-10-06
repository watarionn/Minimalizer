from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from minimalizer_zerobase.semantic_abstraction.adaptive_primitive_budget import (
    AdaptivePrimitiveBudget,
)

SA10_COMPONENT_ECONOMY_EVIDENCE_VERSION = "sa10.4-v1"


@dataclass(frozen=True)
class RoleComponentEvidence:
    role: str
    source_components: int
    represented_components: int
    emitted_primitives: int
    source_supported_primitives: int

    def __post_init__(self) -> None:
        values = (
            self.source_components,
            self.represented_components,
            self.emitted_primitives,
            self.source_supported_primitives,
        )
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in values):
            raise ValueError("evidence counts must be non-negative integers")
        if self.represented_components > self.source_components:
            raise ValueError("represented components cannot exceed source components")
        if self.source_supported_primitives > self.emitted_primitives:
            raise ValueError("source-supported primitives cannot exceed emitted primitives")


@dataclass(frozen=True)
class ComponentEconomyEvidence:
    roles: tuple[RoleComponentEvidence, ...]
    source_components: int
    represented_components: int
    emitted_primitives: int
    source_supported_primitives: int
    authoritative: bool = False
    version: str = SA10_COMPONENT_ECONOMY_EVIDENCE_VERSION

    @property
    def component_survival_ratio(self) -> float | None:
        if self.source_components == 0:
            return None
        return self.represented_components / self.source_components

    @property
    def primitive_economy_ratio(self) -> float | None:
        if self.emitted_primitives == 0:
            return 1.0 if self.source_supported_primitives == 0 else None
        return self.source_supported_primitives / self.emitted_primitives

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "authoritative": False,
            "source_components": self.source_components,
            "represented_components": self.represented_components,
            "component_survival_ratio": self.component_survival_ratio,
            "emitted_primitives": self.emitted_primitives,
            "source_supported_primitives": self.source_supported_primitives,
            "primitive_economy_ratio": self.primitive_economy_ratio,
            "roles": [
                {
                    "role": r.role,
                    "source_components": r.source_components,
                    "represented_components": r.represented_components,
                    "emitted_primitives": r.emitted_primitives,
                    "source_supported_primitives": r.source_supported_primitives,
                }
                for r in self.roles
            ],
        }


def build_component_economy_evidence(
    budget: AdaptivePrimitiveBudget,
    *,
    represented_components: Mapping[str, int],
    source_supported_primitives: Mapping[str, int],
) -> ComponentEconomyEvidence:
    """Build explicit diagnostic counts in the adaptive-budget role frame.

    The budget supplies source major-component counts and emitted macro
    primitives. Representation/support counts must be supplied explicitly by
    the caller; this function never guesses them from similarity scores.
    """
    roles: list[RoleComponentEvidence] = []
    known = {entry.role for entry in budget.entries}
    unknown = (set(represented_components) | set(source_supported_primitives)) - known
    if unknown:
        raise ValueError(f"unknown evidence roles: {sorted(unknown)}")

    for entry in budget.entries:
        if entry.role not in represented_components:
            raise ValueError(f"missing represented-component evidence for {entry.role}")
        if entry.role not in source_supported_primitives:
            raise ValueError(f"missing primitive-support evidence for {entry.role}")
        roles.append(
            RoleComponentEvidence(
                role=entry.role,
                source_components=entry.major_component_count,
                represented_components=int(represented_components[entry.role]),
                emitted_primitives=entry.allocated_primitives,
                source_supported_primitives=int(source_supported_primitives[entry.role]),
            )
        )

    return ComponentEconomyEvidence(
        roles=tuple(roles),
        source_components=sum(r.source_components for r in roles),
        represented_components=sum(r.represented_components for r in roles),
        emitted_primitives=sum(r.emitted_primitives for r in roles),
        source_supported_primitives=sum(r.source_supported_primitives for r in roles),
    )
