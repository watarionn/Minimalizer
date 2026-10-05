from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class AbstractionPolicy(str, Enum):
    PRESERVE = "preserve"
    SIMPLIFY = "simplify"
    SUPPRESS = "suppress"
    CONDITIONAL = "conditional"


class StructuralRole(str, Enum):
    ROOT = "root"
    BODY = "body"
    CONNECTOR = "connector"
    ATTACHED = "attached"
    ENVIRONMENT = "environment"
    UNKNOWN = "unknown"


class VisualRole(str, Enum):
    SILHOUETTE = "silhouette"
    MAJOR_MASS = "major_mass"
    IDENTITY_ACCENT = "identity_accent"
    INTERNAL_DETAIL = "internal_detail"
    BACKGROUND = "background"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TopologyConstraint:
    relation: str
    target_part_id: str
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation": self.relation,
            "target_part_id": self.target_part_id,
            "required": self.required,
        }


@dataclass(frozen=True)
class GeometryConstraints:
    allowed_families: tuple[str, ...] = ()
    min_primitives: int = 0
    max_primitives: int | None = None
    preserve_outer_contour: bool = False

    def __post_init__(self) -> None:
        if self.min_primitives < 0:
            raise ValueError("min_primitives must be >= 0")
        if self.max_primitives is not None and self.max_primitives < self.min_primitives:
            raise ValueError("max_primitives must be >= min_primitives")

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed_families": list(self.allowed_families),
            "min_primitives": self.min_primitives,
            "max_primitives": self.max_primitives,
            "preserve_outer_contour": self.preserve_outer_contour,
        }


@dataclass(frozen=True)
class SemanticPart:
    id: str
    category: str
    subcategory: str | None = None
    parent: str | None = None
    children: tuple[str, ...] = ()
    mask_ref: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    contour_ref: str | None = None
    confidence: float = 0.0
    structural_role: StructuralRole = StructuralRole.UNKNOWN
    visual_role: VisualRole = VisualRole.UNKNOWN
    importance: float = 0.0
    abstraction_policy: AbstractionPolicy = AbstractionPolicy.CONDITIONAL
    topology_constraints: tuple[TopologyConstraint, ...] = ()
    geometry_constraints: GeometryConstraints = field(default_factory=GeometryConstraints)
    source_regions: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("SemanticPart.id must not be empty")
        if not self.category:
            raise ValueError("SemanticPart.category must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within [0, 1]")
        if self.bbox is not None and len(self.bbox) != 4:
            raise ValueError("bbox must contain exactly four values")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "subcategory": self.subcategory,
            "parent": self.parent,
            "children": list(self.children),
            "mask_ref": self.mask_ref,
            "bbox": list(self.bbox) if self.bbox is not None else None,
            "contour_ref": self.contour_ref,
            "confidence": round(float(self.confidence), 6),
            "structural_role": self.structural_role.value,
            "visual_role": self.visual_role.value,
            "importance": round(float(self.importance), 6),
            "abstraction_policy": self.abstraction_policy.value,
            "topology_constraints": [item.to_dict() for item in self.topology_constraints],
            "geometry_constraints": self.geometry_constraints.to_dict(),
            "source_regions": sorted(self.source_regions),
            "evidence_refs": sorted(self.evidence_refs),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SemanticPart":
        geometry = value.get("geometry_constraints") or {}
        return cls(
            id=str(value["id"]),
            category=str(value.get("category") or "unknown"),
            subcategory=value.get("subcategory"),
            parent=value.get("parent"),
            children=tuple(value.get("children") or ()),
            mask_ref=value.get("mask_ref"),
            bbox=tuple(value["bbox"]) if value.get("bbox") is not None else None,
            contour_ref=value.get("contour_ref"),
            confidence=float(value.get("confidence", 0.0)),
            structural_role=StructuralRole(value.get("structural_role", "unknown")),
            visual_role=VisualRole(value.get("visual_role", "unknown")),
            importance=float(value.get("importance", 0.0)),
            abstraction_policy=AbstractionPolicy(value.get("abstraction_policy", "conditional")),
            topology_constraints=tuple(
                TopologyConstraint(
                    relation=str(item["relation"]),
                    target_part_id=str(item["target_part_id"]),
                    required=bool(item.get("required", True)),
                )
                for item in value.get("topology_constraints") or ()
            ),
            geometry_constraints=GeometryConstraints(
                allowed_families=tuple(geometry.get("allowed_families") or ()),
                min_primitives=int(geometry.get("min_primitives", 0)),
                max_primitives=geometry.get("max_primitives"),
                preserve_outer_contour=bool(geometry.get("preserve_outer_contour", False)),
            ),
            source_regions=tuple(value.get("source_regions") or ()),
            evidence_refs=tuple(value.get("evidence_refs") or ()),
        )


@dataclass(frozen=True)
class AbstractionPlan:
    parts: tuple[SemanticPart, ...]
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        ids = [part.id for part in self.parts]
        if len(ids) != len(set(ids)):
            raise ValueError("SemanticPart ids must be unique")

    def to_dict(self) -> dict[str, Any]:
        ordered = sorted(self.parts, key=lambda part: part.id)
        return {
            "schema_version": self.schema_version,
            "parts": [part.to_dict() for part in ordered],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AbstractionPlan":
        return cls(
            schema_version=str(value.get("schema_version", "1.0")),
            parts=tuple(SemanticPart.from_dict(item) for item in value.get("parts") or ()),
        )
