from __future__ import annotations

import numpy as np

from .models import CharacterStructure, PoseProxyNode, PoseProxyEdge, PoseProxyGraph
from .part_types import CharacterPartType


def _part_node(structure, part_type, node_id):
    part = structure.first_part(part_type)
    if part is None:
        return None
    return PoseProxyNode(
        id=node_id,
        part_type=part_type,
        position=part.centroid,
        confidence=part.confidence,
        source_part_id=part.id,
    )


def make_head_node(structure: CharacterStructure) -> PoseProxyNode | None:
    return _part_node(structure, CharacterPartType.HEAD, "head")


def make_torso_node(structure: CharacterStructure) -> PoseProxyNode | None:
    return _part_node(structure, CharacterPartType.TORSO, "torso")


def make_limb_nodes(structure: CharacterStructure) -> list[PoseProxyNode]:
    specs = [
        (CharacterPartType.LEFT_ARM, "left_arm"),
        (CharacterPartType.RIGHT_ARM, "right_arm"),
        (CharacterPartType.LEFT_LEG, "left_leg"),
        (CharacterPartType.RIGHT_LEG, "right_leg"),
    ]
    return [n for p, name in specs if (n := _part_node(structure, p, name)) is not None]


def connect_pose_nodes(nodes: list[PoseProxyNode]) -> list[PoseProxyEdge]:
    ids = {n.id: n for n in nodes}
    edges: list[PoseProxyEdge] = []

    def add(src, dst, relation, base=0.72):
        if src not in ids or dst not in ids:
            return
        conf = float(min(ids[src].confidence, ids[dst].confidence) * base + 0.20)
        edges.append(PoseProxyEdge(src, dst, min(1.0, conf), relation))

    add("head", "torso", "head_to_torso", 0.88)
    add("torso", "left_arm", "torso_to_arm", 0.75)
    add("torso", "right_arm", "torso_to_arm", 0.75)
    add("torso", "left_leg", "torso_to_leg", 0.82)
    add("torso", "right_leg", "torso_to_leg", 0.82)
    return edges


def attach_props_to_pose(
    structure: CharacterStructure,
    graph: PoseProxyGraph,
) -> PoseProxyGraph:
    nodes = list(graph.nodes)
    edges = list(graph.edges)

    arm_nodes = {
        "left": next((n for n in nodes if n.id == "left_arm"), None),
        "right": next((n for n in nodes if n.id == "right_arm"), None),
    }
    torso = next((n for n in nodes if n.id == "torso"), None)

    for i, prop in enumerate(structure.get_parts(CharacterPartType.PROP)):
        node = PoseProxyNode(
            id=f"prop_{i}",
            part_type=CharacterPartType.PROP,
            position=prop.centroid,
            confidence=prop.confidence,
            source_part_id=prop.id,
        )
        nodes.append(node)

        candidates = [n for n in arm_nodes.values() if n is not None]
        if not candidates and torso is not None:
            candidates = [torso]
        if candidates:
            nearest = min(
                candidates,
                key=lambda n: (n.position[0] - prop.centroid[0]) ** 2
                + (n.position[1] - prop.centroid[1]) ** 2,
            )
            relation = "arm_to_prop" if "arm" in nearest.id else "torso_to_prop"
            edges.append(
                PoseProxyEdge(
                    nearest.id,
                    node.id,
                    min(1.0, 0.45 + min(nearest.confidence, prop.confidence) * 0.45),
                    relation,
                )
            )

    graph.nodes = nodes
    graph.edges = edges
    return graph


def resolve_limb_sides(
    structure: CharacterStructure,
    graph: PoseProxyGraph,
) -> CharacterStructure:
    axis = graph.body_axis_x
    if axis is None:
        return structure

    for part in structure.parts:
        if part.part_type in {
            CharacterPartType.LEFT_ARM,
            CharacterPartType.LEFT_LEG,
        }:
            part.side = "left"
        elif part.part_type in {
            CharacterPartType.RIGHT_ARM,
            CharacterPartType.RIGHT_LEG,
        }:
            part.side = "right"
        elif part.part_type == CharacterPartType.PROP and part.side == "unknown":
            part.side = "left" if part.centroid[0] < axis else "right"
    return structure


def build_pose_proxy(structure: CharacterStructure) -> PoseProxyGraph:
    nodes = []
    head = make_head_node(structure)
    torso = make_torso_node(structure)
    if head:
        nodes.append(head)
    if torso:
        nodes.append(torso)
    nodes.extend(make_limb_nodes(structure))

    edges = connect_pose_nodes(nodes)
    sx, sy, sw, sh = structure.subject_bbox
    body_axis = float(structure.metadata.get("body_axis_x", sx + sw / 2.0))

    shoulder_y = None
    hip_y = None
    torso_part = structure.first_part(CharacterPartType.TORSO)
    if torso_part:
        tx, ty, tw, th = torso_part.bbox
        shoulder_y = float(ty + th * 0.18)
        hip_y = float(ty + th * 0.82)

    node_conf = [n.confidence for n in nodes]
    graph = PoseProxyGraph(
        nodes=nodes,
        edges=edges,
        body_axis_x=body_axis,
        shoulder_y=shoulder_y,
        hip_y=hip_y,
        confidence=float(np.mean(node_conf)) if node_conf else 0.0,
    )
    graph = attach_props_to_pose(structure, graph)
    structure.pose_graph = graph
    resolve_limb_sides(structure, graph)
    return graph
