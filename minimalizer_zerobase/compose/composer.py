from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Any
from minimalizer_zerobase import SCHEMA_VERSION
from minimalizer_zerobase.core.serialization import CanonicalModel
from minimalizer_zerobase.geometry.models import PrimitiveCandidate
from minimalizer_zerobase.palette.engine import MaterialAssignment
from minimalizer_zerobase.scene.models import Scene

@dataclass(frozen=True)
class ComposedPrimitive(CanonicalModel):
    primitive_id: str
    source_region_id: str
    selected_candidate_id: str
    primitive_type: str
    parameters: dict[str, Any] = field(default_factory=dict)
    fill_ref: str | None = None
    z_order: int = 0
    occluded_by: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class VectorScene(CanonicalModel):
    width: int
    height: int
    primitives: tuple[ComposedPrimitive, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

@dataclass(frozen=True)
class CompositionPolicy:
    background_roles: tuple[str, ...] = ("background",)
    strict_materials: bool = True
    strict_relations: bool = True

class SemanticComposer:
    producer = "SemanticComposer"
    producer_version = "1.0"

    def __init__(self, policy: CompositionPolicy | None = None):
        self.policy = policy or CompositionPolicy()

    def compose(
        self,
        scene: Scene,
        candidates: Iterable[PrimitiveCandidate],
        selections: Mapping[str, str],
        materials: Iterable[MaterialAssignment],
    ) -> VectorScene:
        regions = {r.region_id: r for r in scene.regions}
        candidate_list = tuple(candidates)
        by_id = {c.candidate_id: c for c in candidate_list}
        if len(by_id) != len(candidate_list):
            raise ValueError("duplicate primitive candidate_id")
        unknown_selection = set(selections) - set(regions)
        if unknown_selection:
            raise ValueError("selection references unknown region")
        selected = {}
        for region_id, candidate_id in sorted(selections.items()):
            candidate = by_id.get(candidate_id)
            if candidate is None:
                raise ValueError("selection references missing candidate")
            if candidate.source_region_id != region_id:
                raise ValueError("candidate selected for wrong region")
            selected[region_id] = candidate

        material_list = tuple(materials)
        material_map = {m.region_id: m for m in material_list}
        if len(material_map) != len(material_list):
            raise ValueError("duplicate material assignment region_id")
        if set(material_map) - set(regions):
            raise ValueError("material references unknown region")
        if self.policy.strict_materials and set(selected) - set(material_map):
            raise ValueError("selected region is missing material assignment")

        edges = self._occlusion_edges(scene, set(selected))
        order = self._z_order(regions, set(selected), edges)
        above = {rid: [] for rid in selected}
        for lower, upper in edges:
            above[lower].append(upper)

        primitives = []
        for region_id in sorted(selected, key=lambda rid: order[rid]):
            candidate = selected[region_id]
            material = material_map.get(region_id)
            primitives.append(ComposedPrimitive(
                primitive_id=f"primitive:{region_id}",
                source_region_id=region_id,
                selected_candidate_id=candidate.candidate_id,
                primitive_type=candidate.primitive_type,
                parameters=dict(candidate.parameters),
                fill_ref=material.palette_color if material else None,
                z_order=order[region_id],
                occluded_by=tuple(sorted(above[region_id])),
            ))
        provenance = {
            "producer": self.producer,
            "producer_version": self.producer_version,
            "selection_authority": "external",
            "selections": [[rid, selections[rid]] for rid in sorted(selections)],
            "occlusion_edges": [list(edge) for edge in sorted(edges)],
        }
        return VectorScene(scene.coordinate_space.width, scene.coordinate_space.height,
                           tuple(primitives), provenance)

    def _occlusion_edges(self, scene: Scene, selected: set[str]) -> set[tuple[str, str]]:
        edges = set()
        region_ids = {r.region_id for r in scene.regions}
        for relation in scene.relations:
            if relation.kind not in {"in_front_of", "behind"}:
                continue
            if relation.source_id not in region_ids or relation.target_id not in region_ids:
                if self.policy.strict_relations:
                    raise ValueError("occlusion relation references unknown region")
                continue
            if relation.source_id not in selected or relation.target_id not in selected:
                continue
            edge = ((relation.target_id, relation.source_id)
                    if relation.kind == "in_front_of"
                    else (relation.source_id, relation.target_id))
            if edge[0] != edge[1]:
                edges.add(edge)
        return edges

    def _z_order(self, regions, selected: set[str], edges: set[tuple[str, str]]) -> dict[str, int]:
        incoming = {rid: 0 for rid in selected}
        outgoing = {rid: set() for rid in selected}
        for lower, upper in edges:
            if upper not in outgoing[lower]:
                outgoing[lower].add(upper)
                incoming[upper] += 1
        def key(rid: str):
            background = 0 if regions[rid].semantic_role in self.policy.background_roles else 1
            return (background, rid)
        ready = sorted((rid for rid, degree in incoming.items() if degree == 0), key=key)
        ordered = []
        while ready:
            rid = ready.pop(0)
            ordered.append(rid)
            for upper in sorted(outgoing[rid], key=key):
                incoming[upper] -= 1
                if incoming[upper] == 0:
                    ready.append(upper)
                    ready.sort(key=key)
        if len(ordered) != len(selected):
            raise ValueError("occlusion relations contain a cycle")
        return {rid: index for index, rid in enumerate(ordered)}
