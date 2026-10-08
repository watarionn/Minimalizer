"""GC001 real Phase12 owner-aware contour evaluation (research-only).

Reads the selected 11-primitive scene and source Phase04 part masks. Never
changes production geometry or emits an editable/painted candidate image.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from minimalizer_zerobase.reviewed_sa10.source_contour_optimizer import (
    optimize_existing_owner_contour,
)
from tools.run_sa1032_gc001_owner_audit import audit_records, scene_records

PROTECTED = ("face", "hair", "left_arm", "right_arm")
MUTABLE_RESEARCH = frozenset(("face", "hair"))


def read_part_mask(path: Path) -> np.ndarray:
    raster = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if raster is None:
        raise ValueError(f"missing or unreadable part mask: {path}")
    if raster.ndim == 2:
        return raster > 0
    if raster.ndim == 3 and raster.shape[2] == 4:
        return raster[:, :, 3] > 0
    if raster.ndim == 3 and raster.shape[2] == 3:
        return cv2.cvtColor(raster, cv2.COLOR_BGR2GRAY) > 0
    raise ValueError(f"unsupported mask format: {path}")


def mask_topology(mask: np.ndarray) -> list[int]:
    _, hierarchy = cv2.findContours(
        mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
    )
    if hierarchy is None:
        return [0, 0]
    parents = hierarchy[0][:, 3]
    return [int(np.count_nonzero(parents == -1)), int(np.count_nonzero(parents != -1))]


def rasterize_primitive(primitive: dict, shape: tuple[int, int]) -> np.ndarray:
    """Replay contour-tree polygon rings by depth, retaining holes and islands."""
    parameters = primitive.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("primitive parameters missing")
    if parameters.get("hole_preservation") != "contour-tree-even-odd":
        raise ValueError("cannot certify primitive's hole rendering semantics")
    rings = parameters.get("rings")
    if not isinstance(rings, list) or not rings:
        raise ValueError("primitive lacks replayable contour-tree rings")
    canvas = np.zeros(shape, dtype=np.uint8)
    ordered: list[tuple[int, np.ndarray]] = []
    for ring in rings:
        if not isinstance(ring, dict) or not isinstance(ring.get("depth"), int):
            raise ValueError("invalid ring depth")
        depth = ring["depth"]
        points = np.asarray(ring.get("points"), dtype=np.float64)
        if depth < 0 or points.ndim != 2 or points.shape[1] != 2 or len(points) < 3:
            raise ValueError("unreplayable polygon ring")
        if not np.all(np.isfinite(points)):
            raise ValueError("invalid polygon coordinates")
        ordered.append((depth, np.rint(points).astype(np.int32)))
    for depth, points in sorted(ordered, key=lambda item: item[0]):
        cv2.fillPoly(canvas, [points], 1 if depth % 2 == 0 else 0)
    return canvas.astype(bool)


def compare_part(source: np.ndarray, existing: np.ndarray) -> dict:
    if source.ndim != 2 or existing.shape != source.shape:
        raise ValueError("part raster canvas mismatch")
    intersection = int(np.count_nonzero(source & existing))
    union = int(np.count_nonzero(source | existing))
    return {
        "source_pixels": int(np.count_nonzero(source)),
        "baseline_pixels": int(np.count_nonzero(existing)),
        "iou": intersection / union if union else 0.0,
        "missing_source_pixels": int(np.count_nonzero(source & ~existing)),
        "extra_baseline_pixels": int(np.count_nonzero(~source & existing)),
        "source_topology": mask_topology(source),
        "baseline_topology": mask_topology(existing),
        "topology_pass": mask_topology(source) == mask_topology(existing),
    }


def evaluate(
    scene: dict, source_masks: dict[str, np.ndarray], *,
    prior_benchmark: dict | None = None,
) -> dict:
    selected = scene.get("selected_name")
    records = scene_records(scene)
    owner_audit = audit_records(records)
    height = scene.get("coordinate_space", {}).get("pixel_height")
    width = scene.get("coordinate_space", {}).get("pixel_width")
    if not isinstance(height, int) or not isinstance(width, int) or min(height, width) <= 0:
        raise ValueError("missing valid scene coordinate space")
    if not isinstance(selected, str):
        raise ValueError("selected Phase12 candidate required")
    candidates = [c for c in scene["candidates"] if c.get("name") == selected]
    declared_count = candidates[0].get("metrics", {}).get("primitive_count")
    if declared_count is not None and declared_count != len(records):
        raise ValueError("candidate primitive count disagrees with metrics")

    result: dict = {
        "schema": "sa10.32-gc001-owner-contour-eval-v1",
        "phase12_candidate": selected,
        "phase12_primitive_count": len(records),
        "owner_audit": owner_audit,
        "parts": {},
        "prior_hard_failures": [],
        "promotion_authorized": False,
    }
    lookup: dict[str, list[dict]] = {}
    for primitive in records:
        owner = primitive.get("semantic_part_id")
        composition = primitive.get("composition_part")
        if owner and composition and owner != composition:
            raise ValueError("semantic owner conflicts with composition part")
        if owner in PROTECTED:
            lookup.setdefault(owner, []).append(primitive)

    candidate_count = 0
    for owner in PROTECTED:
        matches = lookup.get(owner, [])
        if len(matches) != 1 or owner not in source_masks:
            result["parts"][owner] = {"status": "HOLD_MISSING_OR_AMBIGUOUS_OWNER"}
            continue
        primitive = matches[0]
        source = np.asarray(source_masks[owner]).astype(bool)
        if source.shape != (height, width):
            result["parts"][owner] = {"status": "HOLD_CANVAS_MISMATCH"}
            continue
        if primitive.get("source_mask_replay") is not True:
            result["parts"][owner] = {"status": "HOLD_NO_SOURCE_REPLAY"}
            continue
        mask_owner = primitive.get("source_mask_owner")
        if mask_owner not in (None, owner):
            result["parts"][owner] = {"status": "HOLD_PROVENANCE_CONFLICT"}
            continue
        try:
            existing = rasterize_primitive(primitive, (height, width))
        except ValueError as exc:
            result["parts"][owner] = {"status": "HOLD_UNREPLAYABLE_GEOMETRY", "reason": str(exc)}
            continue
        metrics = compare_part(source, existing)
        metrics["primitive_id"] = primitive.get("primitive_id")
        metrics["component_count"] = len(primitive.get("parameters", {}).get("components", []))
        metrics["ring_count"] = len(primitive.get("parameters", {}).get("rings", []))
        if owner not in MUTABLE_RESEARCH:
            metrics["status"] = "OBSERVE_ONLY_PROTECTED_ARM"
        else:
            color = primitive.get("palette_color_rgb")
            material = json.dumps(color)
            decision = optimize_existing_owner_contour(
                owner=owner, existing_mask=existing, source_mask=source,
                existing_primitive_count=1, proposed_primitive_count=1,
                existing_material=material, proposed_material=material,
            )
            metrics["status"] = decision.status
            metrics["reason"] = decision.reason
            if decision.proposal is not None:
                candidate_count += 1
                metrics["proposal"] = {
                    "source_iou": decision.proposal.source_iou,
                    "baseline_source_iou": decision.proposal.existing_source_iou,
                    "baseline_candidate_iou": decision.proposal.candidate_existing_iou,
                    "vertices": decision.proposal.vertices,
                    "diagnostic_only": True,
                }
        result["parts"][owner] = metrics

    if prior_benchmark is not None:
        anatomy = prior_benchmark.get("baseline", {}).get("anatomy", {})
        result["prior_hard_failures"] = anatomy.get("hard_failures", [])
        result["prior_anatomy_gate"] = anatomy.get("gate")
    result["research_candidates"] = candidate_count
    result["status"] = (
        "HOLD_PREVIOUS_GLOBAL_HARD_GATE"
        if result["prior_hard_failures"] else
        "HOLD_OWNER_OR_GEOMETRY"
        if owner_audit["status"] != "OWNER_AUDIT_PASS" or
        any(result["parts"].get(owner, {}).get("status", "").startswith("HOLD") for owner in PROTECTED)
        else "HOLD_FULL_SCENE_GATES_REQUIRED"
    )
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--simplification", required=True, type=Path)
    p.add_argument("--masks", required=True, type=Path)
    p.add_argument("--benchmark", type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    scene = json.loads(args.simplification.read_text(encoding="utf-8-sig"))
    masks = {owner: read_part_mask(args.masks / f"{owner}.png") for owner in PROTECTED}
    benchmark = json.loads(args.benchmark.read_text(encoding="utf-8-sig")) if args.benchmark else None
    result = evaluate(scene, masks, prior_benchmark=benchmark)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
