from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Mapping, Any
from minimalizer_zerobase.compose.composer import ComposedPrimitive, VectorScene

SUPPORTED = frozenset({"rectangle", "ellipse", "triangle", "trapezoid", "convex_polygon"})

@dataclass(frozen=True)
class GeometryProposal:
    primitive_id: str
    parameters: Mapping[str, Any]

def apply_geometry_proposals(scene: VectorScene, proposals: tuple[GeometryProposal, ...]) -> VectorScene:
    by_id = {p.primitive_id: p for p in proposals}
    if len(by_id) != len(proposals):
        raise ValueError("duplicate geometry proposal")
    known = {p.primitive_id for p in scene.primitives}
    if set(by_id) - known:
        raise ValueError("proposal references unknown primitive")
    out = []
    for primitive in scene.primitives:
        proposal = by_id.get(primitive.primitive_id)
        if proposal is None:
            out.append(primitive)
            continue
        if primitive.primitive_type not in SUPPORTED:
            raise ValueError(f"unsupported primitive type: {primitive.primitive_type}")
        out.append(ComposedPrimitive(
            primitive_id=primitive.primitive_id,
            source_region_id=primitive.source_region_id,
            selected_candidate_id=primitive.selected_candidate_id,
            primitive_type=primitive.primitive_type,
            parameters=dict(proposal.parameters),
            fill_ref=primitive.fill_ref,
            z_order=primitive.z_order,
            occluded_by=primitive.occluded_by,
        ))
    provenance = dict(scene.provenance)
    provenance["geometry_refinement"] = {
        "mode": "proposal",
        "topology_changed": False,
        "primitive_count_changed": False,
    }
    return VectorScene(scene.width, scene.height, tuple(out), provenance)

def finite_difference_step(
    parameters: Mapping[str, float],
    loss: Callable[[Mapping[str, float]], float],
    *,
    learning_rate: float = 0.1,
    epsilon: float = 1e-3,
) -> dict[str, float]:
    """Backend-independent P2 smoke optimizer.

    It proves the geometry contract without making finite differences the production
    differentiable backend. diffvg can later supply gradients behind the same boundary.
    """
    base = {k: float(v) for k, v in parameters.items()}
    updated = dict(base)
    for key in sorted(base):
        plus, minus = dict(base), dict(base)
        plus[key] += epsilon
        minus[key] -= epsilon
        grad = (loss(plus) - loss(minus)) / (2.0 * epsilon)
        updated[key] = base[key] - learning_rate * grad
    return updated
