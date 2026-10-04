from __future__ import annotations

import hashlib
from dataclasses import dataclass
from itertools import combinations
from typing import Any, Mapping

import cv2
import numpy as np


UNBOUND_PART = "__unbound__"


def _rounded(value: float) -> float:
    return round(float(value), 6)


@dataclass(frozen=True)
class CompositionPolicy:
    critical_visible_parts: tuple[str, ...] = (
        "face",
        "left_arm",
        "right_arm",
        "accessory_or_held_object",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "critical_visible_parts": list(self.critical_visible_parts),
            "explicit_depth_relations": ["in_front_of", "behind"],
            "non_depth_relations_as_z_order": "forbidden",
            "unresolved_depth": "preserve-as-unresolved",
            "raster_tie_break": "per-pixel-phase10-mask-and-phase9-color-raster-v2",
            "intra_part_order": "per-pixel-mask-and-palette-color-key",
            "identifier_tie_break": "exactly-identical-per-pixel-raster-only",
            "id_only_ordering": "forbidden",
        }


@dataclass(frozen=True)
class SemanticCompositionResult:
    width: int
    height: int
    primitives: tuple[dict[str, Any], ...]
    part_raster_order: tuple[str, ...]
    applied_graph_edges: tuple[dict[str, Any], ...]
    unresolved_depth_pairs: tuple[dict[str, Any], ...]
    validation: dict[str, Any]
    policy: CompositionPolicy
    primitive_masks: dict[str, np.ndarray]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "coordinate_space": {
                "pixel_width": self.width,
                "pixel_height": self.height,
                "normalized_origin": "top-left",
                "normalized_range": [0.0, 1.0],
            },
            "composition_policy": self.policy.to_dict(),
            "part_raster_order_back_to_front": list(self.part_raster_order),
            "applied_graph_edges": list(self.applied_graph_edges),
            "unresolved_depth_pairs": list(self.unresolved_depth_pairs),
            "primitives_back_to_front": list(self.primitives),
            "validation": self.validation,
        }


def _points(raw: Any) -> np.ndarray:
    if not isinstance(raw, list) or not raw:
        raise ValueError("Phase 10 primitive points must be a non-empty list")
    points = np.asarray(raw, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 2 or not np.all(np.isfinite(points)):
        raise ValueError("Phase 10 primitive points must contain finite [x, y] pairs")
    return points


def _fill_polygons(shape: tuple[int, int], polygons: list[np.ndarray]) -> np.ndarray:
    canvas = np.zeros(shape, dtype=np.uint8)
    for points in polygons:
        rounded = np.rint(points).astype(np.int32).reshape(-1, 1, 2)
        if len(rounded) >= 3:
            cv2.fillPoly(canvas, [rounded], 255, lineType=cv2.LINE_8)
        elif len(rounded) == 2:
            cv2.line(
                canvas,
                tuple(rounded[0, 0]),
                tuple(rounded[1, 0]),
                255,
                1,
                cv2.LINE_8,
            )
        elif len(rounded) == 1:
            x, y = rounded[0, 0]
            if 0 <= y < shape[0] and 0 <= x < shape[1]:
                canvas[y, x] = 255
    return canvas > 0


def rasterize_primitive_candidate(
    candidate: Mapping[str, Any], *, width: int, height: int
) -> np.ndarray:
    family = candidate.get("primitive_type")
    parameters = candidate.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("Phase 10 primitive parameters must be an object")
    shape = (height, width)
    if family in {"polygon", "rounded_polygon"}:
        raw_components = parameters.get("components")
        if not isinstance(raw_components, list) or not raw_components:
            raise ValueError("polygon primitive requires components")
        raw_rings = parameters.get("rings")
        if raw_rings is not None:
            if family != "polygon":
                raise ValueError("ring-aware geometry is currently polygon-only")
            if not isinstance(raw_rings, list) or not raw_rings:
                raise ValueError("polygon rings must be a non-empty list")
            canvas = np.zeros(shape, dtype=np.uint8)
            normalized_rings: list[tuple[int, int, np.ndarray]] = []
            for index, ring in enumerate(raw_rings):
                if not isinstance(ring, Mapping):
                    raise ValueError("polygon ring entries must be objects")
                depth = int(ring.get("depth", -1))
                role = ring.get("role")
                expected_role = "fill" if depth >= 0 and depth % 2 == 0 else "hole"
                if depth < 0 or role != expected_role:
                    raise ValueError("polygon ring role/depth mismatch")
                normalized_rings.append((depth, index, _points(ring.get("points"))))
            contours = [
                np.rint(points).astype(np.int32).reshape(-1, 1, 2)
                for _, _, points in sorted(normalized_rings)
            ]
            # A single FILLED draw uses OpenCV's even-odd contour rule, preserving
            # hole boundary pixels. Separate fill/hole passes erase those pixels
            # and drift from the Phase 10 fidelity raster.
            cv2.drawContours(
                canvas,
                contours,
                -1,
                255,
                thickness=cv2.FILLED,
                lineType=cv2.LINE_8,
            )
            mask = canvas > 0
        else:
            mask = _fill_polygons(shape, [_points(item) for item in raw_components])
        if family == "rounded_polygon":
            radius = int(parameters.get("corner_radius_px", 0))
            if radius < 0:
                raise ValueError("rounded polygon radius must be non-negative")
            if radius > 0:
                kernel_size = radius * 2 + 1
                blurred = cv2.GaussianBlur(
                    mask.astype(np.uint8) * 255,
                    (kernel_size, kernel_size),
                    0,
                )
                rounded_mask = blurred >= 128
                if np.any(rounded_mask):
                    mask = rounded_mask
        return mask
    if family == "ellipse":
        center = _points([parameters.get("center_xy")])[0]
        radii = _points([parameters.get("radii_xy")])[0]
        angle = float(parameters.get("angle_degrees", 0.0))
        if not np.all(np.isfinite(radii)) or np.any(radii <= 0.0) or not np.isfinite(angle):
            raise ValueError("ellipse parameters are invalid")
        canvas = np.zeros(shape, dtype=np.uint8)
        cv2.ellipse(
            canvas,
            tuple(np.rint(center).astype(int)),
            tuple(np.maximum(1, np.rint(radii).astype(int))),
            angle,
            0,
            360,
            255,
            -1,
            cv2.LINE_8,
        )
        return canvas > 0
    if family == "capsule":
        start = _points([parameters.get("start_xy")])[0]
        end = _points([parameters.get("end_xy")])[0]
        radius = float(parameters.get("radius_px", 0.0))
        if not np.isfinite(radius) or radius <= 0.0:
            raise ValueError("capsule radius must be positive")
        canvas = np.zeros(shape, dtype=np.uint8)
        start_xy = tuple(np.rint(start).astype(int))
        end_xy = tuple(np.rint(end).astype(int))
        cv2.line(
            canvas,
            start_xy,
            end_xy,
            255,
            max(1, int(round(radius * 2.0))),
            cv2.LINE_8,
        )
        cv2.circle(canvas, start_xy, max(1, int(round(radius))), 255, -1, cv2.LINE_8)
        cv2.circle(canvas, end_xy, max(1, int(round(radius))), 255, -1, cv2.LINE_8)
        return canvas > 0
    if family == "oriented_rectangle":
        return _fill_polygons(shape, [_points(parameters.get("points"))])
    if family == "tapered_strip":
        return _fill_polygons(shape, [_points(parameters.get("points"))])
    if family == "polyline_ribbon":
        return _fill_polygons(shape, [_points(parameters.get("outline"))])
    raise ValueError(f"unsupported Phase 10 primitive family: {family!r}")


def _coordinate(payload: Mapping[str, Any], *, phase: int) -> tuple[int, int]:
    coordinate = payload.get("coordinate_space")
    if not isinstance(coordinate, Mapping):
        raise ValueError(f"Phase {phase} coordinate_space is missing")
    width = int(coordinate.get("pixel_width", 0))
    height = int(coordinate.get("pixel_height", 0))
    if width <= 0 or height <= 0:
        raise ValueError(f"Phase {phase} coordinate_space must be positive")
    return width, height


def _unique_records(raw: Any, key: str, *, label: str) -> dict[str, Mapping[str, Any]]:
    if not isinstance(raw, list):
        raise ValueError(f"{label} must be a list")
    output: dict[str, Mapping[str, Any]] = {}
    for item in raw:
        if not isinstance(item, Mapping):
            raise ValueError(f"{label} entries must be objects")
        value = item.get(key)
        if not isinstance(value, str) or not value or value in output:
            raise ValueError(f"{label} {key} values must be present and unique")
        output[value] = item
    return output


def _relation_edges(
    graph_payload: Mapping[str, Any],
    selected_parts: set[str],
) -> tuple[dict[str, Any], ...]:
    present_raw = graph_payload.get("present_parts")
    relations = graph_payload.get("relations")
    if not isinstance(present_raw, list) or not all(isinstance(item, str) for item in present_raw):
        raise ValueError("Phase 5 present_parts must be a string list")
    present = set(present_raw)
    if not isinstance(relations, list):
        raise ValueError("Phase 5 relations must be a list")
    if selected_parts - present:
        raise ValueError(
            "Phase 10 selected semantic owner is absent from the Phase 5 graph"
        )

    by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for relation in relations:
        if not isinstance(relation, Mapping):
            raise ValueError("Phase 5 relation entries must be objects")
        source = relation.get("source_part")
        target = relation.get("target_part")
        kind = relation.get("relation_kind")
        relation_id = relation.get("relation_id")
        if not all(isinstance(item, str) and item for item in (source, target, kind, relation_id)):
            raise ValueError("Phase 5 relation identity is incomplete")
        if source not in present or target not in present:
            raise ValueError("Phase 5 relation references an absent part")
        lower: str | None = None
        upper: str | None = None
        rule: str | None = None
        if kind == "in_front_of":
            lower, upper, rule = target, source, "explicit-occlusion"
        elif kind == "behind":
            lower, upper, rule = source, target, "explicit-occlusion"
        if lower is None or lower not in selected_parts or upper not in selected_parts:
            continue
        if lower == upper:
            raise ValueError("Phase 5 relation creates a self occlusion edge")
        key = (lower, upper)
        entry = by_pair.setdefault(
            key,
            {
                "lower_part": lower,
                "upper_part": upper,
                "relation_ids": [],
                "relation_kinds": [],
                "resolution": rule,
            },
        )
        entry["relation_ids"].append(relation_id)
        entry["relation_kinds"].append(kind)

    edges: list[dict[str, Any]] = []
    for key in sorted(by_pair):
        entry = by_pair[key]
        entry["relation_ids"] = sorted(set(entry["relation_ids"]))
        entry["relation_kinds"] = sorted(set(entry["relation_kinds"]))
        edges.append(entry)

    return tuple(edges)


def _mask_digest(mask: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(mask, dtype=np.uint8).tobytes()).hexdigest()


def _part_raster_key(
    part: str,
    mask: np.ndarray,
    colors: tuple[tuple[int, int, int], ...],
    visual_raster: np.ndarray,
) -> tuple[
    float,
    float,
    float,
    str,
    tuple[tuple[int, int, int], ...],
    str,
    bytes,
    str,
]:
    ys, xs = np.where(mask)
    if not len(xs):
        raise ValueError("Phase 10 semantic part rasterizes to an empty mask")
    if visual_raster.shape != (*mask.shape, 4) or visual_raster.dtype != np.uint8:
        raise ValueError("Phase 11 part visual raster must be uint8 RGBA")
    if not np.array_equal(visual_raster[..., 3] > 0, mask):
        raise ValueError("Phase 11 part visual raster alpha must match its union mask")
    # The complete RGBA bytes are part of the ordering key, not merely their digest.
    # Therefore the semantic identifier below can only break a serialization tie
    # when both parts paint exactly the same color at every occupied pixel. Swapping
    # such parts cannot change the final raster.
    visual_bytes = np.ascontiguousarray(visual_raster).tobytes()
    return (
        -float(len(xs)),
        _rounded(float(ys.mean())),
        _rounded(float(xs.mean())),
        _mask_digest(mask),
        colors,
        hashlib.sha256(visual_bytes).hexdigest(),
        visual_bytes,
        part,
    )


def _topological_parts(
    parts: set[str],
    edges: tuple[dict[str, Any], ...],
    raster_keys: Mapping[str, tuple[Any, ...]],
) -> tuple[str, ...]:
    incoming = {part: 0 for part in parts}
    outgoing = {part: set() for part in parts}
    for edge in edges:
        lower = edge["lower_part"]
        upper = edge["upper_part"]
        if upper not in outgoing[lower]:
            outgoing[lower].add(upper)
            incoming[upper] += 1
    ready = sorted(
        (part for part, count in incoming.items() if count == 0),
        key=lambda part: raster_keys[part],
    )
    ordered: list[str] = []
    while ready:
        visual_key = raster_keys[ready[0]][:-1]
        # Drain a complete equal-visual group before considering nodes it unlocks.
        # The final semantic-name field is serialization-only inside this group;
        # it cannot indirectly alter the placement of a visually different part.
        batch = [part for part in ready if raster_keys[part][:-1] == visual_key]
        ready = [part for part in ready if raster_keys[part][:-1] != visual_key]
        batch.sort(key=lambda part: raster_keys[part])
        ordered.extend(batch)
        newly_ready: list[str] = []
        for part in batch:
            for upper in sorted(outgoing[part], key=lambda item: raster_keys[item]):
                incoming[upper] -= 1
                if incoming[upper] == 0:
                    newly_ready.append(upper)
        ready.extend(newly_ready)
        ready.sort(key=lambda part: raster_keys[part])
    if len(ordered) != len(parts):
        raise ValueError("Phase 5 occlusion relations contain a composition cycle")
    return tuple(ordered)


def _geometry_key(
    record: Mapping[str, Any], mask: np.ndarray
) -> tuple[float, float, float, str, bytes, tuple[int, int, int], str, str]:
    ys, xs = np.where(mask)
    if not len(xs):
        raise ValueError("Phase 10 selected primitive rasterizes to an empty mask")
    family = str(record["primitive_type"])
    color = tuple(int(value) for value in record["palette_color_rgb"])
    return (
        -float(len(xs)),
        _rounded(float(ys.mean())),
        _rounded(float(xs.mean())),
        _mask_digest(mask),
        np.packbits(mask, bitorder="little").tobytes(),
        color,
        family,
        str(record["primitive_id"]),
    )


def _reachable_pairs(
    parts: set[str], edges: tuple[dict[str, Any], ...]
) -> set[tuple[str, str]]:
    outgoing = {part: set() for part in parts}
    for edge in edges:
        outgoing[edge["lower_part"]].add(edge["upper_part"])
    reachable: set[tuple[str, str]] = set()
    for source in parts:
        pending = list(outgoing[source])
        seen: set[str] = set()
        while pending:
            target = pending.pop()
            if target in seen:
                continue
            seen.add(target)
            reachable.add((source, target))
            pending.extend(outgoing[target] - seen)
    return reachable


def _unresolved_depth_pairs(
    graph_payload: Mapping[str, Any],
    part_masks: Mapping[str, np.ndarray],
    edges: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    relations = graph_payload.get("relations", [])
    topology: dict[frozenset[str], set[str]] = {}
    for relation in relations:
        if not isinstance(relation, Mapping):
            continue
        source = relation.get("source_part")
        target = relation.get("target_part")
        kind = relation.get("relation_kind")
        if (
            isinstance(source, str)
            and isinstance(target, str)
            and isinstance(kind, str)
            and kind not in {"in_front_of", "behind"}
        ):
            topology.setdefault(frozenset((source, target)), set()).add(kind)

    parts = set(part_masks)
    reachable = _reachable_pairs(parts, edges)
    unresolved: list[dict[str, Any]] = []
    for first, second in combinations(sorted(parts), 2):
        if (first, second) in reachable or (second, first) in reachable:
            continue
        overlap = int(np.count_nonzero(part_masks[first] & part_masks[second]))
        if overlap == 0:
            continue
        unresolved.append(
            {
                "parts": [first, second],
                "overlap_pixel_count": overlap,
                "reason": "no-explicit-phase5-in-front-of-or-behind-relation",
                "supporting_non_depth_relations": sorted(
                    topology.get(frozenset((first, second)), set())
                ),
                "raster_tie_break": "per-pixel-phase10-mask-and-phase9-color-raster-v2",
            }
        )
    return tuple(unresolved)


def compose_semantic_scene(
    graph_payload: Mapping[str, Any],
    geometry_payload: Mapping[str, Any],
    *,
    policy: CompositionPolicy | None = None,
) -> SemanticCompositionResult:
    policy = policy or CompositionPolicy()
    if graph_payload.get("validation", {}).get("pass") is not True:
        raise ValueError("Phase 11 requires a passing Phase 5 graph")
    if geometry_payload.get("validation", {}).get("pass") is not True:
        raise ValueError("Phase 11 requires a passing Phase 10 geometry result")
    width5, height5 = _coordinate(graph_payload, phase=5)
    width10, height10 = _coordinate(geometry_payload, phase=10)
    if (width5, height5) != (width10, height10):
        raise ValueError("Phase 5 and Phase 10 coordinate spaces differ")

    candidates = _unique_records(
        geometry_payload.get("primitive_candidates"),
        "candidate_id",
        label="Phase 10 primitive candidates",
    )
    selected = _unique_records(
        geometry_payload.get("selected_primitives"),
        "primitive_id",
        label="Phase 10 selected primitives",
    )
    if not selected:
        raise ValueError("Phase 11 requires selected Phase 10 primitives")
    omitted = set(geometry_payload.get("omitted_mass_ids", []))
    selected_mass_ids: set[str] = set()
    masks: dict[str, np.ndarray] = {}
    normalized: list[dict[str, Any]] = []
    selected_parts: set[str] = set()
    for primitive_id, item in selected.items():
        candidate_id = item.get("candidate_id")
        candidate = candidates.get(str(candidate_id))
        if candidate is None:
            raise ValueError("Phase 10 selection references a missing candidate")
        mass_id = item.get("mass_id")
        if not isinstance(mass_id, str) or not mass_id or mass_id in selected_mass_ids:
            raise ValueError("Phase 10 selected mass IDs must be present and unique")
        selected_mass_ids.add(mass_id)
        if mass_id in omitted:
            raise ValueError("Phase 11 refuses Phase 8 prune resurrection")
        for field in (
            "mass_id",
            "semantic_part_id",
            "binding_status",
            "primitive_type",
            "palette_id",
        ):
            if item.get(field) != candidate.get(field):
                raise ValueError(f"Phase 10 selection/candidate {field} drift")
        if candidate.get("action") not in {"protect", "keep"}:
            raise ValueError("Phase 11 accepts only active Phase 8 actions")
        part_raw = item.get("semantic_part_id")
        status = item.get("binding_status")
        if status == "bound":
            if not isinstance(part_raw, str) or not part_raw:
                raise ValueError("bound Phase 10 primitive requires semantic owner")
            part = part_raw
            selected_parts.add(part)
        elif status == "unbound" and part_raw is None:
            part = UNBOUND_PART
        else:
            raise ValueError("Phase 10 binding status and semantic owner disagree")
        color_raw = item.get("palette_color_rgb")
        if (
            not isinstance(color_raw, list)
            or len(color_raw) != 3
            or any(not isinstance(value, int) or not 0 <= value <= 255 for value in color_raw)
        ):
            raise ValueError("Phase 10 selected palette color must be RGB")
        mask = rasterize_primitive_candidate(candidate, width=width10, height=height10)
        expected_pixels = int(candidate.get("candidate_pixel_count", -1))
        if int(np.count_nonzero(mask)) != expected_pixels:
            raise ValueError("Phase 10 primitive geometry does not reproduce its pixel count")
        masks[primitive_id] = mask
        normalized.append(
            {
                "primitive_id": primitive_id,
                "candidate_id": candidate_id,
                "mass_id": mass_id,
                "semantic_part_id": part_raw,
                "composition_part": part,
                "binding_status": status,
                "phase8_action": candidate["action"],
                "primitive_type": item["primitive_type"],
                "parameters": candidate["parameters"],
                "palette_id": item["palette_id"],
                "palette_color_rgb": list(color_raw),
                "source_pixel_count": int(candidate.get("source_pixel_count", 0)),
                "candidate_pixel_count": expected_pixels,
                "phase10_total_cost": item.get("total_cost"),
            }
        )

    edges = _relation_edges(graph_payload, selected_parts)
    all_parts = selected_parts | ({UNBOUND_PART} if any(item["composition_part"] == UNBOUND_PART for item in normalized) else set())
    part_masks: dict[str, np.ndarray] = {
        part: np.zeros((height10, width10), dtype=bool) for part in all_parts
    }
    part_colors: dict[str, set[tuple[int, int, int]]] = {
        part: set() for part in all_parts
    }
    for item in normalized:
        part = item["composition_part"]
        part_masks[part] |= masks[item["primitive_id"]]
        part_colors[part].add(tuple(item["palette_color_rgb"]))
    part_visual_rasters: dict[str, np.ndarray] = {
        part: np.zeros((height10, width10, 4), dtype=np.uint8) for part in all_parts
    }
    for item in sorted(
        normalized,
        key=lambda record: _geometry_key(record, masks[record["primitive_id"]]),
    ):
        part = item["composition_part"]
        mask = masks[item["primitive_id"]]
        part_visual_rasters[part][mask, :3] = np.asarray(
            item["palette_color_rgb"], dtype=np.uint8
        )
        part_visual_rasters[part][mask, 3] = 255
    raster_keys = {
        part: _part_raster_key(
            part,
            part_masks[part],
            tuple(sorted(part_colors[part])),
            part_visual_rasters[part],
        )
        for part in all_parts
    }
    part_order = _topological_parts(all_parts, edges, raster_keys)
    unresolved = _unresolved_depth_pairs(graph_payload, part_masks, edges)
    part_index = {part: index for index, part in enumerate(part_order)}
    normalized.sort(
        key=lambda item: (
            part_index[item["composition_part"]],
            _geometry_key(item, masks[item["primitive_id"]]),
        )
    )

    incoming_relations: dict[str, list[str]] = {part: [] for part in all_parts}
    outgoing_relations: dict[str, list[str]] = {part: [] for part in all_parts}
    for edge in edges:
        incoming_relations[edge["upper_part"]].extend(edge["relation_ids"])
        outgoing_relations[edge["lower_part"]].extend(edge["relation_ids"])

    composed: list[dict[str, Any]] = []
    owner = np.full((height10, width10), -1, dtype=np.int32)
    for z_index, item in enumerate(normalized):
        part = item["composition_part"]
        basis_ids = sorted(set(incoming_relations[part] + outgoing_relations[part]))
        record = dict(item)
        record["raster_index"] = z_index
        record["depth_basis"] = {
            "explicit_graph_relation_ids": basis_ids,
            "part_order": (
                "explicit-phase5-depth-graph"
                if basis_ids
                else "deterministic-raster-tie-break-unresolved-depth"
            ),
            "intra_part": "per-pixel-mask-and-palette-color-key",
        }
        composed.append(record)
        owner[masks[item["primitive_id"]]] = z_index

    visible_by_part: dict[str, int] = {part: 0 for part in all_parts}
    for index, item in enumerate(composed):
        visible_by_part[item["composition_part"]] += int(
            np.count_nonzero(masks[item["primitive_id"]] & (owner == index))
        )
    critical_occluded = sorted(
        part
        for part in policy.critical_visible_parts
        if part in selected_parts and visible_by_part.get(part, 0) == 0
    )
    order_violations = [
        edge
        for edge in edges
        if part_index[edge["lower_part"]] >= part_index[edge["upper_part"]]
    ]
    validation = {
        "pass": not order_violations and not critical_occluded,
        "selected_primitive_count": len(composed),
        "phase10_selected_primitive_count": len(selected),
        "selected_set_change_count": 0,
        "primitive_geometry_change_count": 0,
        "semantic_owner_change_count": 0,
        "phase8_action_change_count": 0,
        "phase9_palette_change_count": 0,
        "prune_resurrection_count": 0,
        "generated_or_inpainted_pixel_count": 0,
        "applied_graph_edge_count": len(edges),
        "implicit_depth_edge_count": 0,
        "containment_depth_edge_count": 0,
        "non_explicit_depth_edge_count": 0,
        "graph_order_violations": order_violations,
        "unresolved_depth_pair_count": len(unresolved),
        "fully_occluded_critical_parts": critical_occluded,
        "visible_pixels_by_part": {
            part: visible_by_part[part] for part in sorted(visible_by_part)
        },
        "region_id_only_ordering": False,
        "mass_id_only_ordering": False,
        "observed_phase10_geometry_only": True,
        "semantic_identifier_visual_authority": False,
        "serialization_tie_requires_identical_part_raster": True,
    }
    return SemanticCompositionResult(
        width=width10,
        height=height10,
        primitives=tuple(composed),
        part_raster_order=part_order,
        applied_graph_edges=edges,
        unresolved_depth_pairs=unresolved,
        validation=validation,
        policy=policy,
        primitive_masks=masks,
    )
