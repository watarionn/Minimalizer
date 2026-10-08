"""SA10.34 greedy topology-constrained contour simplification research.

Only modifies points on source-provenanced existing primitive rings. Every
accepted edit must retain owner-local raw topology, preserve source micro
islands/holes, and pass the *unchanged* full-scene hard gate plus an explicit
minimum historical silhouette IoU. This is neither browser SVG validation nor
production permission.
"""
from __future__ import annotations

from copy import deepcopy

import cv2
import numpy as np

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.evaluation.material_topology import mask_topology
from minimalizer_zerobase.evaluation.source_silhouette_anatomy_gate import evaluate_source_silhouette_anatomy
from .source_exact_vector_replay import _binary, _vertex_budget

DEFAULT_EPSILONS = (2.0, 1.5, 1.25, 1.0, 0.75, 0.6, 0.5)


def _micro_features(source: np.ndarray, *, maximum_pixels: int) -> tuple[np.ndarray, np.ndarray]:
    mask = source.astype(np.uint8)
    connected, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    tiny_islands = np.zeros(mask.shape, dtype=bool)
    for index in range(1, connected):
        if int(stats[index, cv2.CC_STAT_AREA]) <= maximum_pixels:
            tiny_islands |= labels == index
    padded = cv2.copyMakeBorder(mask, 1, 1, 1, 1, cv2.BORDER_CONSTANT)
    connected, labels, stats, _ = cv2.connectedComponentsWithStats(1 - padded, 8)
    tiny_holes = np.zeros(mask.shape, dtype=bool)
    for index in range(1, connected):
        x, y, w, h, area = stats[index]
        if (x > 0 and y > 0 and x + w < padded.shape[1]
                and y + h < padded.shape[0]
                and int(area) <= maximum_pixels):
            tiny_holes |= labels[1:-1, 1:-1] == index
    return tiny_islands, tiny_holes


def adapt_exact_contours(
    exact_primitives: list[dict],
    exact_masks: dict[str, np.ndarray],
    source_masks: dict[str, np.ndarray],
    *,
    width: int,
    height: int,
    minimum_global_iou: float,
    minimum_owner_iou: float = 0.995,
    micro_feature_max_pixels: int = 8,
    epsilons: tuple[float, ...] = DEFAULT_EPSILONS,
    original_ring_budget: int,
    original_component_budget: int,
) -> tuple[list[dict], dict[str, np.ndarray], dict]:
    if not 0.96 <= minimum_global_iou <= 1.0:
        raise ValueError("minimum global IoU must not weaken the original 0.96 gate")
    if not 0.96 <= minimum_owner_iou <= 1.0 or micro_feature_max_pixels < 1:
        raise ValueError("invalid part micro-feature preservation policy")
    if not epsilons or not all(0 < epsilon <= 8 for epsilon in epsilons):
        raise ValueError("invalid approximation search sequence")
    candidates = deepcopy(exact_primitives)
    if not candidates:
        raise ValueError("no existing contour primitives")
    ids = [p["primitive_id"] for p in candidates]
    if len(set(ids)) != len(ids) or set(ids) != set(exact_masks):
        raise ValueError("candidate primitive identities mismatch")
    masks = {key: np.asarray(value).astype(bool).copy() for key, value in exact_masks.items()}
    shape = (height, width)
    source = {owner: _binary(mask, shape=shape) for owner, mask in source_masks.items()}
    source_union = np.logical_or.reduce(list(source.values()))
    owner_topology = {owner: mask_topology(mask) for owner, mask in source.items()}
    tiny = {owner: _micro_features(mask, maximum_pixels=micro_feature_max_pixels)
            for owner, mask in source.items()}

    def gate() -> dict:
        visible = [
            masks[p["primitive_id"]]
            for p in candidates if p.get("structural_support_only") is not True
        ]
        painted = np.logical_or.reduce(visible)
        return evaluate_source_silhouette_anatomy(
            source_union, painted, fragmentation_penalty=0.0
        )

    original_gate = gate()
    if original_gate["gate"] != "PASS" or original_gate["metrics"]["silhouette_iou"] < minimum_global_iou:
        raise ValueError("input source-exact candidate must pass the original hard gate")

    edits: list[dict] = []
    for primitive in candidates:
        owner = primitive.get("source_mask_owner")
        if owner not in source or primitive.get("source_mask_replay") is not True:
            raise ValueError("unbound or unverified source mask")
        primitive_id = primitive["primitive_id"]
        params = primitive["parameters"]
        rings = params["rings"]
        for index in sorted(range(len(rings)), key=lambda i: -len(rings[i]["points"])):
            previous_points = rings[index]["points"]
            old_vertices = len(previous_points)
            if old_vertices <= 3:
                continue
            selected = None
            for epsilon in epsilons:
                points = cv2.approxPolyDP(
                    np.asarray(previous_points, dtype=np.float32).reshape(-1, 1, 2),
                    float(epsilon), True
                ).reshape(-1, 2).astype(float).tolist()
                if not points or len(points) >= old_vertices:
                    continue
                rings[index]["points"] = points
                params["components"] = [r["points"] for r in rings if r["depth"] % 2 == 0]
                params["holes"] = [r["points"] for r in rings if r["depth"] % 2 == 1]
                rendered = rasterize_primitive_candidate(primitive, width=width, height=height)
                if mask_topology(rendered) != owner_topology[owner]:
                    continue
                tiny_islands, tiny_holes = tiny[owner]
                if np.any(tiny_islands & ~rendered) or np.any(tiny_holes & rendered):
                    continue
                m = source[owner]
                overlap = int(np.count_nonzero(m & rendered))
                union = int(np.count_nonzero(m | rendered))
                if (overlap / union if union else 0.0) + 1e-12 < minimum_owner_iou:
                    continue
                masks[primitive_id] = rendered
                full = gate()
                if (full["gate"] == "PASS"
                        and full["metrics"]["silhouette_iou"] + 1e-12 >= minimum_global_iou):
                    selected = (points, rendered, epsilon)
                    break
            if selected is None:
                rings[index]["points"] = previous_points
            else:
                rings[index]["points"] = selected[0]
                masks[primitive_id] = selected[1]
                edits.append({
                    "owner": owner,
                    "primitive_id": primitive_id,
                    "source_ring_index": index,
                    "vertices_before": old_vertices,
                    "vertices_after": len(selected[0]),
                    "epsilon": selected[2],
                })
            params["components"] = [r["points"] for r in rings if r["depth"] % 2 == 0]
            params["holes"] = [r["points"] for r in rings if r["depth"] % 2 == 1]

    final_gate = gate()
    if final_gate["gate"] != "PASS":
        raise AssertionError("adaptive process violated raw global hard gate")
    budget = _vertex_budget(candidates)
    original = _vertex_budget(exact_primitives)
    budget_ok = (budget["ring_vertices"] <= original_ring_budget
                 and budget["component_vertices"] <= original_component_budget)
    if not all(
        np.array_equal(rasterize_primitive_candidate(p, width=width, height=height),
                       masks[p["primitive_id"]])
        for p in candidates
    ):
        raise AssertionError("render must have exact authority from serialized polygon")
    if not all(
        mask_topology(masks[p["primitive_id"]]) == owner_topology[p["source_mask_owner"]]
        for p in candidates
    ):
        raise AssertionError("owner raw topology changed")
    degenerate = sum(
        len(ring["points"]) < 3 for p in candidates for ring in p["parameters"]["rings"]
    )
    blockers = []
    if not budget_ok:
        blockers.append("VERTEX_BUDGET_EXCEEDED")
    if degenerate:
        blockers.append("DEGENERATE_SVG_FILL_PATHS")
    blockers.append("BROWSER_SVG_RASTER_AND_HUMAN_VISUAL_GATES_PENDING")
    return candidates, masks, {
        "schema": "sa10.34-topology-greedy-contour-research-v1",
        "original_exact_source_ring_vertices": original["ring_vertices"],
        "original_budget": {
            "ring_vertices": original_ring_budget,
            "component_vertices": original_component_budget,
        },
        "candidate_vertices": budget,
        "accepted_edit_count": len(edits),
        "reduced_ring_vertices": original["ring_vertices"] - budget["ring_vertices"],
        "edits": edits,
        "raw_owner_topology_pass": True,
        "tiny_source_islands_and_holes_preserved": True,
        "global_anatomy": final_gate,
        "vertex_budget_pass": budget_ok,
        "source_owned_paint_masks": True,
        "opencv_vector_render_parity": True,
        "svg_degenerate_rings": degenerate,
        "browser_svg_parity_verified": False,
        "human_visual_gate": "PENDING",
        "promotion_authorized": False,
        "blockers": blockers,
        "status": "RESEARCH_ADAPTIVE_HARD_GATES_PASS_BUDGET_HOLD" if not budget_ok else "HOLD_BROWSER_SVG_AND_HUMAN_GATES",
    }
