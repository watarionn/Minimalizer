from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import cv2

from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.semantic_abstraction.anatomy_guard import (
    AnatomyGuardResult,
    anatomy_integrity_gate,
)
from minimalizer_zerobase.semantic_abstraction.evidence_adapter import (
    build_semantic_abstraction_evidence,
)
from minimalizer_zerobase.structure.graph import (
    build_structural_layout_graph,
    graph_validation,
)

SA10_STRUCTURAL_HARD_EVIDENCE_VERSION = "sa10.18-v1"
_ARM_MIN_RECALL = 0.50
_FACE_HEAD_MIN_BBOX_IOU = 0.70
_FACE_HEAD_AREA_RATIO = (0.55, 1.80)
_OUTER_BOUNDARY_MIN_RECALL = 0.90


def _canonical_material_mask(mask: np.ndarray) -> np.ndarray:
    """Normalize segmentation noise while preserving material topology.

    A one-pixel speck or pin-hole is not a material component/hole.  Larger
    components and holes are retained, including disconnected anatomy that
    must remain visible.  The area cutoff is derived only from the mask area
    and is therefore deterministic and independent of part ordering.
    """
    binary = (np.asarray(mask) > 0).astype(np.uint8)
    if binary.ndim != 2:
        raise ValueError("material masks must be 2D")
    foreground_area = int(binary.sum())
    cutoff = max(2, int(round(foreground_area * 0.001)))

    components, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    cleaned = np.zeros_like(binary)
    for label in range(1, components):
        if int(stats[label, cv2.CC_STAT_AREA]) >= cutoff:
            cleaned[labels == label] = 1

    # Work on the padded background so only enclosed holes are considered.
    padded = cv2.copyMakeBorder(cleaned, 1, 1, 1, 1, cv2.BORDER_CONSTANT)
    background_count, background_labels, background_stats, _ = (
        cv2.connectedComponentsWithStats(1 - padded, 8)
    )
    for label in range(1, background_count):
        # Border-connected background is not a hole.
        x, y, w, h, area = background_stats[label]
        touches_border = x == 0 or y == 0 or x + w == padded.shape[1] or y + h == padded.shape[0]
        if not touches_border and int(area) < cutoff:
            cleaned[background_labels[1:-1, 1:-1] == label] = 1
    return cleaned.astype(bool)


def _mask_topology(mask: np.ndarray) -> dict:
    """Return source-derived 8-connected component/hole/Euler evidence."""
    binary = (np.asarray(mask) > 0).astype(np.uint8)
    components, _, _, _ = cv2.connectedComponentsWithStats(binary, 8)
    padded = cv2.copyMakeBorder(binary, 1, 1, 1, 1, cv2.BORDER_CONSTANT)
    background, _, _, _ = cv2.connectedComponentsWithStats(1 - padded, 8)
    component_count = max(0, int(components) - 1)
    hole_count = max(0, int(background) - 1)
    return {
        "components": component_count,
        "holes": hole_count,
        "euler_characteristic": component_count - hole_count,
    }


_NON_SEMANTIC_TOPOLOGY_PARTS = frozenset({"unknown", "__unbound__"})


def _coverage_role(name: str) -> str:
    """Describe why a non-semantic mask exists in the source contract."""
    if name == "unknown":
        # Phase 4 unknown is subject & ~assigned: observed evidence with no
        # semantic owner, never an owner that Phase 11 may be required to
        # reproduce.
        return "observed-unassigned"
    if name == "__unbound__":
        return "observed-unassigned"
    return "semantic-owner"

def _topology_evidence(masks: Mapping[str, np.ndarray]) -> dict:
    semantic_masks = {
        name: mask
        for name, mask in sorted(masks.items())
        if name not in _NON_SEMANTIC_TOPOLOGY_PARTS
    }
    raw_per_part = {name: _mask_topology(mask) for name, mask in semantic_masks.items()}
    canonical_masks = {
        name: _canonical_material_mask(mask) for name, mask in semantic_masks.items()
    }
    per_part = {name: _mask_topology(mask) for name, mask in canonical_masks.items()}
    union = (
        np.logical_or.reduce(list(canonical_masks.values()))
        if semantic_masks
        else np.zeros((1, 1), dtype=bool)
    )
    non_semantic = {
        name: {
            "coverage_role": _coverage_role(name),
            "pixel_count": int(np.count_nonzero(mask)),
            "excluded_from_semantic_topology": True,
        }
        for name, mask in sorted(masks.items())
        if name in _NON_SEMANTIC_TOPOLOGY_PARTS
    }
    raw_union = (
        np.logical_or.reduce(list(semantic_masks.values()))
        if semantic_masks else np.zeros((1, 1), dtype=bool)
    )
    return {
        "per_part": per_part,
        "union": _mask_topology(union),
        "raw_per_part": raw_per_part,
        "raw_union": _mask_topology(raw_union),
        "non_semantic_coverage": non_semantic,
        "semantic_union_definition": "union of semantic-owner masks only",
    }


def _relation_key(row) -> tuple[str, str, str]:
    return (row.source_part, row.relation_kind, row.target_part)


def _normalize_masks(
    masks: Mapping[str, np.ndarray],
    *,
    shape: tuple[int, int],
) -> dict[str, np.ndarray]:
    return {
        name: (
            np.asarray(masks[name]).astype(bool)
            if name in masks
            else np.zeros(shape, dtype=bool)
        )
        for name in PART_NAMES
    }


@dataclass(frozen=True)
class StructuralHardEvidenceReport:
    anatomy: AnatomyGuardResult
    source_topology_validation: dict
    candidate_topology_validation: dict
    anatomy_pass: bool
    topology_pass: bool
    missing_required_relations: tuple[str, ...]
    source_anatomy: dict
    source_silhouette: dict
    source_topology: dict
    candidate_topology: dict
    topology_mismatches: tuple[str, ...]
    missing_source_relations: tuple[str, ...]
    version: str = SA10_STRUCTURAL_HARD_EVIDENCE_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "anatomy": {
                "status": "AVAILABLE",
                "passed": self.anatomy_pass,
                "details": self.anatomy.to_dict(),
            },
            "topology": {
                "status": "AVAILABLE",
                "passed": self.topology_pass,
                "source_validation": self.source_topology_validation,
                "candidate_validation": self.candidate_topology_validation,
                "missing_required_relations": list(self.missing_required_relations),
                "source_evidence": self.source_topology,
                "candidate_evidence": self.candidate_topology,
                "mismatches": list(self.topology_mismatches),
                "missing_source_relations": list(self.missing_source_relations),
            },
            "phase14_metric_relabeling": False,
            "source_anatomy": self.source_anatomy,
            "source_silhouette": self.source_silhouette,
        }


def _bbox(mask):
    ys, xs = np.where(mask)
    return None if len(xs) == 0 else (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def _bbox_iou(a, b):
    if a is None or b is None:
        return 0.0
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - inter
    return float(inter / max(union, 1))


def _source_bound_geometry(source, candidate):
    anatomy, failures = {}, []
    for part in ("left_arm", "right_arm"):
        src = source[part]
        if not np.any(src):
            anatomy[part] = {"source_visible": False, "passed": True}
            continue
        recall = int(np.count_nonzero(src & candidate[part])) / max(int(src.sum()), 1)
        passed = recall >= _ARM_MIN_RECALL
        anatomy[part] = {"source_visible": True, "recall": recall, "minimum": _ARM_MIN_RECALL, "passed": passed}
        if not passed:
            failures.append(f"{part}:source-visible-part-disappearance")
    for part in ("face", "head"):
        src = source[part]
        if not np.any(src):
            continue
        cand = candidate[part]
        ratio = int(cand.sum()) / max(int(src.sum()), 1)
        iou = _bbox_iou(_bbox(src), _bbox(cand))
        passed = bool(cand.any() and iou >= _FACE_HEAD_MIN_BBOX_IOU and _FACE_HEAD_AREA_RATIO[0] <= ratio <= _FACE_HEAD_AREA_RATIO[1])
        anatomy[part] = {"source_visible": True, "bbox_iou": iou, "minimum_bbox_iou": _FACE_HEAD_MIN_BBOX_IOU, "area_ratio": ratio, "area_ratio_range": list(_FACE_HEAD_AREA_RATIO), "passed": passed}
        if not passed:
            failures.append(f"{part}:source-geometry-drift")
    anatomy["failures"], anatomy["passed"] = failures, not failures
    source_outer = np.logical_or.reduce(list(source.values()))
    candidate_outer = np.logical_or.reduce(list(candidate.values()))
    kernel = np.ones((3, 3), np.uint8)
    source_edge = cv2.morphologyEx(source_outer.astype(np.uint8), cv2.MORPH_GRADIENT, kernel).astype(bool)
    candidate_edge = cv2.morphologyEx(candidate_outer.astype(np.uint8), cv2.MORPH_GRADIENT, kernel).astype(bool)
    recall = int(np.count_nonzero(source_edge & candidate_edge)) / max(int(source_edge.sum()), 1)
    return anatomy, {"source_boundary_pixels": int(source_edge.sum()), "candidate_boundary_pixels": int(candidate_edge.sum()), "boundary_recall": recall, "minimum_boundary_recall": _OUTER_BOUNDARY_MIN_RECALL, "passed": recall >= _OUTER_BOUNDARY_MIN_RECALL}


def evaluate_structural_hard_evidence(
    *,
    source_masks: Mapping[str, np.ndarray],
    candidate_masks: Mapping[str, np.ndarray],
    accessory_kind: str = "none",
    accessory_confidence: float = 0.0,
) -> StructuralHardEvidenceReport:
    source_any = next((np.asarray(v) for v in source_masks.values()), None)
    candidate_any = next((np.asarray(v) for v in candidate_masks.values()), None)
    if source_any is None or candidate_any is None:
        raise ValueError("source and candidate masks are required")
    if source_any.ndim != 2 or candidate_any.ndim != 2:
        raise ValueError("2D masks are required")
    if source_any.shape != candidate_any.shape:
        raise ValueError("source/candidate mask frames must align")

    shape = source_any.shape
    source = _normalize_masks(source_masks, shape=shape)
    candidate = _normalize_masks(candidate_masks, shape=shape)

    source_graph = build_structural_layout_graph(
        source,
        accessory_kind=accessory_kind,
        accessory_confidence=accessory_confidence,
    )
    candidate_graph = build_structural_layout_graph(
        candidate,
        accessory_kind=accessory_kind,
        accessory_confidence=accessory_confidence,
    )
    source_validation = graph_validation(source_graph)
    candidate_validation = graph_validation(candidate_graph)

    baseline_plan = build_semantic_abstraction_evidence(
        part_masks=source,
        graph=source_graph,
    )
    candidate_plan = build_semantic_abstraction_evidence(
        part_masks=candidate,
        graph=candidate_graph,
    )
    anatomy = anatomy_integrity_gate(baseline_plan, candidate_plan)

    candidate_relations = {
        (row.source_part, row.relation_kind, row.target_part)
        for row in candidate_graph.relations
        if row.confidence >= 0.5
    }
    missing_required_relations = tuple(sorted(
        f"{row.source_part}:{row.relation_kind}:{row.target_part}"
        for row in source_graph.relations
        if row.confidence >= 0.5
        and (row.source_part, row.relation_kind, row.target_part)
        not in candidate_relations
    ))
    source_topology = _topology_evidence(source)
    candidate_topology = _topology_evidence(candidate)
    topology_mismatches = tuple(sorted(
        f"{name}:{field}:{source_topology['per_part'][name][field]}!={candidate_topology['per_part'][name][field]}"
        for name in source_topology["per_part"]
        for field in ("components", "holes", "euler_characteristic")
        if source_topology["per_part"][name][field] != candidate_topology["per_part"][name][field]
    ))
    topology_mismatches += tuple(sorted(
        f"union:{field}:{source_topology['union'][field]}!={candidate_topology['union'][field]}"
        for field in ("components", "holes", "euler_characteristic")
        if source_topology["union"][field] != candidate_topology["union"][field]
    ))
    missing_source_relations = tuple(sorted(
        f"{row.source_part}:{row.relation_kind}:{row.target_part}"
        for row in source_graph.relations
        if row.confidence >= 0.5 and _relation_key(row) not in candidate_relations
    ))
    source_anatomy, source_silhouette = _source_bound_geometry(source, candidate)

    return StructuralHardEvidenceReport(
        anatomy=anatomy,
        source_topology_validation=source_validation,
        candidate_topology_validation=candidate_validation,
        anatomy_pass=anatomy.passed,
        topology_pass=bool(
            source_validation["pass"] and candidate_validation["pass"]
            and not missing_required_relations
            and not topology_mismatches
            and not missing_source_relations
        ),
        missing_required_relations=missing_required_relations,
        source_anatomy=source_anatomy,
        source_silhouette=source_silhouette,
        source_topology=source_topology,
        candidate_topology=candidate_topology,
        topology_mismatches=topology_mismatches,
        missing_source_relations=missing_source_relations,
    )
