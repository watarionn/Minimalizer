from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

from .part_types import CharacterPartType, SideHint


@dataclass
class CharacterPartCandidate:
    id: int
    part_type: CharacterPartType
    mask: np.ndarray
    bbox: tuple[int, int, int, int]
    centroid: tuple[float, float]
    area: int
    area_ratio: float
    region_ids: list[int] = field(default_factory=list)
    confidence: float = 0.0
    side: SideHint = "unknown"
    parent_part_id: int | None = None
    color_rgb: tuple[int, int, int] | None = None
    color_lab: tuple[float, float, float] | None = None
    abstraction_level: float = 1.0
    shape_budget: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class PoseProxyNode:
    id: str
    part_type: CharacterPartType
    position: tuple[float, float]
    confidence: float
    source_part_id: int | None = None


@dataclass
class PoseProxyEdge:
    source_id: str
    target_id: str
    confidence: float
    relation: str


@dataclass
class PoseProxyGraph:
    nodes: list[PoseProxyNode] = field(default_factory=list)
    edges: list[PoseProxyEdge] = field(default_factory=list)
    body_axis_x: float | None = None
    shoulder_y: float | None = None
    hip_y: float | None = None
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "body_axis_x": self.body_axis_x,
            "shoulder_y": self.shoulder_y,
            "hip_y": self.hip_y,
            "confidence": self.confidence,
            "nodes": [
                {
                    "id": n.id,
                    "part_type": str(n.part_type),
                    "position": list(n.position),
                    "confidence": n.confidence,
                    "source_part_id": n.source_part_id,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "confidence": e.confidence,
                    "relation": e.relation,
                }
                for e in self.edges
            ],
        }


@dataclass
class CharacterShapeBudget:
    total: int
    per_part: dict[CharacterPartType, int]
    reserved_face: int = 0
    reserved_hair: int = 0
    reserved_props: int = 0
    reserved_outfit: int = 0
    reserved_body: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "per_part": {str(k): v for k, v in self.per_part.items()},
            "reserved_face": self.reserved_face,
            "reserved_hair": self.reserved_hair,
            "reserved_props": self.reserved_props,
            "reserved_outfit": self.reserved_outfit,
            "reserved_body": self.reserved_body,
            "metadata": self.metadata,
        }


@dataclass
class CharacterStructure:
    subject_bbox: tuple[int, int, int, int]
    subject_mask: np.ndarray
    parts: list[CharacterPartCandidate]
    pose_graph: PoseProxyGraph | None = None
    preset: str = "auto"
    confidence: float = 0.0
    metadata: dict = field(default_factory=dict)

    def get_parts(self, part_type: CharacterPartType) -> list[CharacterPartCandidate]:
        return [p for p in self.parts if p.part_type == part_type]

    def first_part(self, part_type: CharacterPartType) -> CharacterPartCandidate | None:
        return next((p for p in self.parts if p.part_type == part_type), None)

    def to_dict(self, include_masks: bool = False) -> dict:
        parts = []
        for p in self.parts:
            item = {
                "id": p.id,
                "part_type": str(p.part_type),
                "bbox": list(p.bbox),
                "centroid": list(p.centroid),
                "area": p.area,
                "area_ratio": p.area_ratio,
                "region_ids": list(p.region_ids),
                "confidence": p.confidence,
                "side": p.side,
                "parent_part_id": p.parent_part_id,
                "shape_budget": p.shape_budget,
                "abstraction_level": p.abstraction_level,
                "metadata": p.metadata,
            }
            if include_masks:
                item["mask_shape"] = list(p.mask.shape)
            parts.append(item)
        return {
            "subject_bbox": list(self.subject_bbox),
            "preset": self.preset,
            "confidence": self.confidence,
            "parts": parts,
            "pose_graph": self.pose_graph.to_dict() if self.pose_graph else None,
            "metadata": self.metadata,
        }



@dataclass
class CharacterShapeResult:
    shapes: list
    body_shapes: list = field(default_factory=list)
    hand_shapes: list = field(default_factory=list)
    face_shapes: list = field(default_factory=list)
    hair_shapes: list = field(default_factory=list)
    outfit_shapes: list = field(default_factory=list)
    prop_shapes: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "shape_count": len(self.shapes),
            "body_shape_count": len(self.body_shapes),
            "hand_shape_count": len(self.hand_shapes),
            "face_shape_count": len(self.face_shapes),
            "hair_shape_count": len(self.hair_shapes),
            "outfit_shape_count": len(self.outfit_shapes),
            "prop_shape_count": len(self.prop_shapes),
            "metadata": self.metadata,
        }
