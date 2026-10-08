"""SA10.34 lossless *source-derived* polygon research, never automatic promotion.

Replace coordinates only inside an already existing, provenance-bound polygon.
The official OpenCV polygon rasterizer is both the candidate-render authority
and the serialized geometry checker. No source-pixel overlay or new primitive.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Mapping

import cv2
import numpy as np

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.evaluation.material_topology import mask_topology
from minimalizer_zerobase.evaluation.source_silhouette_anatomy_gate import (
    evaluate_source_silhouette_anatomy,
)


def _binary(raw: np.ndarray, *, shape: tuple[int, int]) -> np.ndarray:
    array = np.asarray(raw)
    if array.ndim != 2 or array.shape != shape or not array.any():
        raise ValueError("source mask must be nonempty and match the scene canvas")
    return array.astype(bool)


def _ring_depth(hierarchy: np.ndarray, index: int) -> int:
    depth = 0
    parent = int(hierarchy[index][3])
    while parent >= 0:
        depth += 1
        parent = int(hierarchy[parent][3])
    return depth


def _vertex_budget(primitives: list[dict]) -> dict:
    return {
        "ring_vertices": sum(
            len(ring.get("points", []))
            for primitive in primitives
            for ring in primitive.get("parameters", {}).get("rings", [])
        ),
        "component_vertices": sum(
            len(component)
            for primitive in primitives
            for component in primitive.get("parameters", {}).get("components", [])
        ),
    }


def exact_source_bound_polygon(
    original: Mapping[str, Any],
    source_mask: np.ndarray,
    *,
    width: int,
    height: int,
) -> tuple[dict, np.ndarray, dict]:
    """Build exact contours into an existing primitive, verifying full parity.

    Degenerate 1-2 point contours are *retained* because the canonical OpenCV
    renderer draws them. They are NOT considered browser-SVG-valid filled paths.
    """
    if original.get("primitive_type") != "polygon":
        raise ValueError("only existing polygon records can be modified")
    if original.get("source_mask_replay") is not True:
        raise ValueError("source replay provenance required")
    owner = original.get("source_mask_owner")
    semantic = original.get("semantic_part_id")
    composition = original.get("composition_part")
    allowed = (
        isinstance(owner, str) and bool(owner)
        and (owner == semantic == composition
             or (owner == "unknown" and semantic is None and composition == "__unbound__"))
    )
    if not allowed:
        raise ValueError("no explicit source-mask owner or mismatched semantic owner")
    evidence = original.get("source_evidence_refs")
    if not isinstance(evidence, list) or f"phase04:part_masks/{owner}.png" not in evidence:
        raise ValueError("missing exact Phase04 source-mask reference")
    parameters = original.get("parameters")
    if not isinstance(parameters, Mapping) or parameters.get("hole_preservation") != "contour-tree-even-odd":
        raise ValueError("unsupported contour hierarchy policy")
    source = _binary(source_mask, shape=(height, width))
    contours, hierarchy = cv2.findContours(
        source.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours or hierarchy is None:
        raise ValueError("empty source contour hierarchy")
    rings: list[dict] = []
    components: list[list[list[float]]] = []
    holes: list[list[list[float]]] = []
    for index, contour in enumerate(contours):
        # Unlike approxPolyDP, CHAIN_APPROX_SIMPLE removes only redundant
        # points along straight digital segments, not 1px source islands.
        points = contour.reshape(-1, 2).astype(float).tolist()
        depth = _ring_depth(hierarchy[0], index)
        ring = {
            "depth": depth, "role": "fill" if depth % 2 == 0 else "hole",
            "points": points, "source_contour_index": index,
        }
        rings.append(ring)
        (components if depth % 2 == 0 else holes).append(points)
    output = deepcopy(dict(original))
    output["parameters"] = {
        **deepcopy(dict(parameters)),
        "components": components,
        "holes": holes,
        "rings": rings,
        "hole_preservation": "contour-tree-even-odd",
    }
    output["geometry_source"] = "exact-phase04-contours-research-only"
    observed = rasterize_primitive_candidate(output, width=width, height=height)
    if not np.array_equal(observed, source):
        raise ValueError("canonical polygon raster does not reproduce source exactly")
    if mask_topology(observed) != mask_topology(source):
        raise ValueError("source topology not preserved")
    audit = {
        "owner": owner,
        "primitive_id": output.get("primitive_id"),
        "source_pixels": int(source.sum()),
        "source_mask_sha256": sha256(np.ascontiguousarray(source, dtype=np.uint8).tobytes()).hexdigest(),
        "rings": len(rings),
        "degenerate_1_or_2_point_rings": sum(len(ring["points"]) < 3 for ring in rings),
        "raster_exact": True,
        "raw_topology": mask_topology(source),
        "owner_and_material_unchanged": (
            output.get("semantic_part_id") == original.get("semantic_part_id")
            and output.get("composition_part") == original.get("composition_part")
            and output.get("palette_color_rgb") == original.get("palette_color_rgb")
            and output.get("primitive_id") == original.get("primitive_id")
            and output.get("raster_index") == original.get("raster_index")
        ),
    }
    if not audit["owner_and_material_unchanged"]:
        raise AssertionError("immutable primitive fields were modified")
    return output, observed, audit


def evaluate_exact_replay(
    selected_primitives: list[dict],
    source_masks: Mapping[str, np.ndarray],
    *,
    width: int,
    height: int,
    max_ring_vertices: int | None = None,
    max_component_vertices: int | None = None,
) -> tuple[list[dict], dict[str, np.ndarray], dict]:
    """Produce a diagnostic candidate and hard-gate results.

    Budget limits default to the *current* selected scene. Strict vertex
    comparisons cannot be silently relaxed. Quality success in this method
    still does not grant user visual approval or a browser SVG pass.
    """
    if width <= 0 or height <= 0 or not isinstance(selected_primitives, list) or not selected_primitives:
        raise ValueError("invalid scene")
    original_ids = [p.get("primitive_id") for p in selected_primitives]
    if not all(isinstance(i, str) and i for i in original_ids) or len(set(original_ids)) != len(original_ids):
        raise ValueError("missing or duplicate primitive IDs")
    old_vertices = _vertex_budget(selected_primitives)
    ring_cap = old_vertices["ring_vertices"] if max_ring_vertices is None else max_ring_vertices
    component_cap = old_vertices["component_vertices"] if max_component_vertices is None else max_component_vertices
    if ring_cap < 1 or component_cap < 1:
        raise ValueError("invalid hard vertex budget")
    rebuilt: list[dict] = []
    candidate_masks: dict[str, np.ndarray] = {}
    owners: dict[str, dict] = {}
    for primitive in selected_primitives:
        owner = primitive.get("source_mask_owner")
        if owner not in source_masks:
            raise ValueError(f"missing source-owned mask for {owner}")
        candidate, raster, audit = exact_source_bound_polygon(
            primitive, source_masks[owner], width=width, height=height
        )
        rebuilt.append(candidate)
        candidate_masks[candidate["primitive_id"]] = raster
        owners[str(owner)] = audit

    if len(rebuilt) != len(selected_primitives):
        raise AssertionError("primitive count drift")
    if not {"face", "hair", "left_arm", "right_arm"}.issubset(owners):
        raise ValueError("face, hair and both arms must remain explicitly owned")
    if "unknown" not in owners:
        raise ValueError("unbound unknown mask required for full source authority")
    source_union = np.logical_or.reduce([
        _binary(mask, shape=(height, width)) for mask in source_masks.values()
    ])
    painted_masks = [
        candidate_masks[primitive["primitive_id"]]
        for primitive in rebuilt if primitive.get("structural_support_only") is not True
    ]
    if not painted_masks:
        raise ValueError("no paintable source-bound primitives")
    painted_union = np.logical_or.reduce(painted_masks)
    anatomy = evaluate_source_silhouette_anatomy(
        source_union, painted_union, fragmentation_penalty=0.0
    )
    updated_vertices = _vertex_budget(rebuilt)
    budget_pass = (
        updated_vertices["ring_vertices"] <= ring_cap
        and updated_vertices["component_vertices"] <= component_cap
    )
    degenerate = sum(x["degenerate_1_or_2_point_rings"] for x in owners.values())
    source_raster_exact = bool(np.array_equal(painted_union, source_union))
    topology_pass = anatomy["gate"] == "PASS"
    export_mask_exact = all(v["raster_exact"] for v in owners.values())
    reasons = []
    if not topology_pass:
        reasons.extend(anatomy["hard_failures"])
    if not export_mask_exact:
        reasons.append("SERIALIZED_VECTOR_MASK_MISMATCH")
    if not budget_pass:
        reasons.append("VERTEX_BUDGET_EXCEEDED")
    if degenerate:
        reasons.append("DEGENERATE_SVG_FILL_PATHS")
    reasons.append("BROWSER_SVG_RASTER_AND_HUMAN_VISUAL_GATES_PENDING")
    return rebuilt, candidate_masks, {
        "schema": "sa10.34-exact-source-contour-research-v1",
        "primitive_count_old": len(selected_primitives),
        "primitive_count_new": len(rebuilt),
        "old_vertices": old_vertices,
        "new_vertices": updated_vertices,
        "budget": {"ring_vertices": ring_cap, "component_vertices": component_cap},
        "vertex_budget_pass": budget_pass,
        "source_raster_exact": source_raster_exact,
        "full_anatomy": anatomy,
        "owner_evidence": owners,
        "opencv_polygon_export_render_parity": export_mask_exact,
        "degenerate_svg_rings": degenerate,
        "browser_svg_parity_verified": False,
        "human_visual_gate": "PENDING",
        "promotion_authorized": False,
        "status": "RESEARCH_TOPOLOGY_RESTORED_NO_GO" if topology_pass else "HOLD_SOURCE_TOPOLOGY",
        "blockers": reasons,
    }
