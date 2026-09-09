from __future__ import annotations

from dataclasses import dataclass, field

from .models import CharacterPartCandidate, CharacterStructure


@dataclass
class SemanticShapeNode:
    name: str
    parent: str | None
    part_id: int | None = None
    children: list[str] = field(default_factory=list)
    primitive_budget: int = 1
    merge_group: str = "generic"
    protected: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "parent": self.parent,
            "part_id": self.part_id,
            "children": list(self.children),
            "primitive_budget": self.primitive_budget,
            "merge_group": self.merge_group,
            "protected": self.protected,
            "metadata": dict(self.metadata),
        }


@dataclass
class SemanticShapeTree:
    nodes: dict[str, SemanticShapeNode] = field(default_factory=dict)
    root: str = "subject"

    def get(self, name: str) -> SemanticShapeNode | None:
        return self.nodes.get(name)

    def parent_of(self, name: str) -> str | None:
        node = self.get(name)
        return node.parent if node is not None else None

    def same_merge_group(self, left: str, right: str) -> bool:
        a = self.get(left)
        b = self.get(right)
        return bool(a and b and a.merge_group == b.merge_group)

    def can_merge(self, left: str, right: str) -> bool:
        if left == right:
            return True
        a = self.get(left)
        b = self.get(right)
        if a is None or b is None:
            return False
        if a.protected or b.protected:
            return False
        if a.merge_group != b.merge_group:
            return False
        return a.parent == b.parent

    def add_synthetic(self, name: str, *, parent: str, primitive_budget: int = 1,
                      merge_group: str | None = None, protected: bool = True,
                      metadata: dict | None = None) -> SemanticShapeNode:
        existing = self.nodes.get(name)
        if existing is not None:
            return existing
        node = SemanticShapeNode(
            name=name,
            parent=parent,
            primitive_budget=primitive_budget,
            merge_group=merge_group or name,
            protected=protected,
            metadata=dict(metadata or {}),
        )
        self.nodes[name] = node
        if parent in self.nodes and name not in self.nodes[parent].children:
            self.nodes[parent].children.append(name)
            self.nodes[parent].children.sort()
        return node

    def to_dict(self) -> dict:
        return {
            "root": self.root,
            "nodes": {name: node.to_dict() for name, node in self.nodes.items()},
        }


_PARENT_RULES = {
    "head": "subject",
    "face": "head",
    "hair": "head",
    "bangs": "hair",
    "side_hair_left": "hair",
    "side_hair_right": "hair",
    "back_hair": "hair",
    "hair_feature": "hair",
    "torso": "subject",
    "outfit": "torso",
    "left_arm": "subject",
    "right_arm": "subject",
    "left_leg": "subject",
    "right_leg": "subject",
    "left_shoe": "left_leg",
    "right_shoe": "right_leg",
    "prop": "subject",
    "accessory": "head",
}


_MERGE_GROUPS = {
    "subject": "subject",
    "head": "head",
    "face": "face",
    "hair": "hair",
    "bangs": "hair",
    "side_hair_left": "hair",
    "side_hair_right": "hair",
    "back_hair": "hair",
    "hair_feature": "hair",
    "torso": "torso",
    "outfit": "outfit",
    "left_arm": "left_arm",
    "right_arm": "right_arm",
    "left_leg": "left_leg",
    "right_leg": "right_leg",
    "left_shoe": "left_leg",
    "right_shoe": "right_leg",
    "prop": "prop",
    "accessory": "accessory",
    "unknown": "unknown",
}


_PROTECTED = {"face", "prop", "accessory"}


_BUDGETS = {
    "face": 1,
    "hair": 3,
    "outfit": 3,
    "left_arm": 2,
    "right_arm": 2,
    "left_leg": 2,
    "right_leg": 2,
    "prop": 2,
    "accessory": 2,
}


def _best_part(parts: list[CharacterPartCandidate], name: str) -> CharacterPartCandidate | None:
    matches = [p for p in parts if str(p.part_type) == name]
    if not matches:
        return None
    return max(matches, key=lambda p: (float(p.confidence), int(p.area)))


def build_semantic_shape_tree(structure: CharacterStructure) -> SemanticShapeTree:
    nodes: dict[str, SemanticShapeNode] = {
        "subject": SemanticShapeNode(
            name="subject",
            parent=None,
            primitive_budget=0,
            merge_group="subject",
            protected=False,
            metadata={"bbox": list(structure.subject_bbox), "confidence": structure.confidence},
        )
    }

    available_names = {str(part.part_type) for part in structure.parts}
    if "head" not in available_names and ({"face", "hair"} & available_names):
        available_names.add("head")
    if "torso" not in available_names and "outfit" in available_names:
        available_names.add("torso")

    pending = sorted(available_names, key=lambda name: (0 if name in {"head", "torso"} else 1, name))
    for name in pending:
        if name == "subject":
            continue
        parent = _PARENT_RULES.get(name, "subject")
        if parent not in nodes and parent != "subject":
            nodes[parent] = SemanticShapeNode(
                name=parent,
                parent=_PARENT_RULES.get(parent, "subject"),
                primitive_budget=_BUDGETS.get(parent, 1),
                merge_group=_MERGE_GROUPS.get(parent, parent),
            )
        part = _best_part(structure.parts, name)
        metadata = {}
        part_id = None
        if part is not None:
            part_id = part.id
            metadata = {
                "bbox": list(part.bbox),
                "confidence": float(part.confidence),
                "area_ratio": float(part.area_ratio),
            }
        nodes[name] = SemanticShapeNode(
            name=name,
            parent=parent,
            part_id=part_id,
            primitive_budget=_BUDGETS.get(name, 1),
            merge_group=_MERGE_GROUPS.get(name, name),
            protected=name in _PROTECTED,
            metadata=metadata,
        )

    for node in nodes.values():
        if node.parent and node.parent in nodes:
            nodes[node.parent].children.append(node.name)
    for node in nodes.values():
        node.children.sort()
    return SemanticShapeTree(nodes=nodes)
