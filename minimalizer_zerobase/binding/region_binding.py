from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import cv2
import numpy as np
import skimage
from skimage.segmentation import slic

from minimalizer_zerobase.parts.decomposition import DISPLAY_PRIORITY, PART_NAMES

MAX_RGB_DISTANCE = float(np.sqrt(3.0 * (255.0**2)))
CLOTHING_PARTS = {
    "torso",
    "major_clothing",
    "left_arm",
    "right_arm",
    "lower_body",
}


def _rounded(value: float) -> float:
    return round(float(value), 6)


@dataclass(frozen=True)
class BindingPolicy:
    n_segments: int = 180
    compactness: float = 12.0
    minimum_part_overlap: float = 0.55
    minimum_winner_margin: float = 0.15
    ambiguity_overlap: float = 0.20
    minimum_decision_score: float = 0.58
    minimum_decision_margin: float = 0.08
    minimum_graph_support: float = 0.45
    minimum_spatial_support: float = 0.35
    semantic_split_override_min_overlap: float = 0.90

    def __post_init__(self) -> None:
        if self.n_segments < 2:
            raise ValueError("n_segments must be at least 2")
        if self.compactness <= 0:
            raise ValueError("compactness must be positive")
        for name in (
            "minimum_part_overlap",
            "minimum_winner_margin",
            "ambiguity_overlap",
            "minimum_decision_score",
            "minimum_decision_margin",
            "minimum_graph_support",
            "minimum_spatial_support",
            "semantic_split_override_min_overlap",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be 0..1")

    def to_dict(self) -> dict:
        return {
            "n_segments": self.n_segments,
            "compactness": _rounded(self.compactness),
            "minimum_part_overlap": _rounded(self.minimum_part_overlap),
            "minimum_winner_margin": _rounded(self.minimum_winner_margin),
            "ambiguity_overlap": _rounded(self.ambiguity_overlap),
            "minimum_decision_score": _rounded(self.minimum_decision_score),
            "minimum_decision_margin": _rounded(self.minimum_decision_margin),
            "minimum_graph_support": _rounded(self.minimum_graph_support),
            "minimum_spatial_support": _rounded(self.minimum_spatial_support),
            "semantic_split_override_min_overlap": _rounded(
                self.semantic_split_override_min_overlap
            ),
        }


@dataclass(frozen=True)
class RegionAdjacency:
    region_id: str
    shared_boundary_pixels: int

    def to_dict(self) -> dict:
        return {
            "region_id": self.region_id,
            "shared_boundary_pixels": self.shared_boundary_pixels,
        }


@dataclass(frozen=True)
class BindingCandidate:
    part_id: str
    exclusive_overlap_pixels: int
    raw_mask_overlap_pixels: int
    region_overlap_ratio: float
    parent_exclusive_overlap_pixels: int
    parent_raw_mask_overlap_pixels: int
    parent_region_overlap_ratio: float
    part_coverage_ratio: float
    boundary_contact_pixels: int
    boundary_support: float
    geometry_support: float
    color_distance_rgb: float
    color_support: float
    graph_relation_ids: tuple[str, ...]
    graph_support: float
    decision_score: float

    def to_dict(self) -> dict:
        return {
            "part_id": self.part_id,
            "exclusive_overlap_pixels": self.exclusive_overlap_pixels,
            "raw_mask_overlap_pixels": self.raw_mask_overlap_pixels,
            "region_overlap_ratio": _rounded(self.region_overlap_ratio),
            "parent_exclusive_overlap_pixels": self.parent_exclusive_overlap_pixels,
            "parent_raw_mask_overlap_pixels": self.parent_raw_mask_overlap_pixels,
            "parent_region_overlap_ratio": _rounded(self.parent_region_overlap_ratio),
            "part_coverage_ratio": _rounded(self.part_coverage_ratio),
            "boundary_contact_pixels": self.boundary_contact_pixels,
            "boundary_support": _rounded(self.boundary_support),
            "geometry_support": _rounded(self.geometry_support),
            "color_distance_rgb": _rounded(self.color_distance_rgb),
            "color_support": _rounded(self.color_support),
            "graph_relation_ids": list(self.graph_relation_ids),
            "graph_support": _rounded(self.graph_support),
            "decision_score": _rounded(self.decision_score),
        }


@dataclass(frozen=True)
class RegionBinding:
    region_id: str
    source_region_label: int
    parent_region_label: int
    parent_pixel_count: int
    parent_winner_part_id: str
    parent_winner_overlap_ratio: float
    parent_winner_margin: float
    parent_ambiguous: bool
    parent_ambiguity_reasons: tuple[str, ...]
    semantic_part_id: str | None
    binding_status: str
    binding_confidence: float
    decision_basis: str
    decision_reasons: tuple[str, ...]
    pixel_count: int
    bbox_xywh: tuple[int, int, int, int]
    centroid_xy: tuple[float, float]
    mean_rgb: tuple[float, float, float]
    std_rgb: tuple[float, float, float]
    pixel_runs: tuple[tuple[int, int, int], ...]
    adjacent_regions: tuple[RegionAdjacency, ...]
    candidates: tuple[BindingCandidate, ...]
    evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "region_id": self.region_id,
            "source_region_label": self.source_region_label,
            "parent_region_label": self.parent_region_label,
            "parent_pixel_count": self.parent_pixel_count,
            "parent_winner_part_id": self.parent_winner_part_id,
            "parent_winner_overlap_ratio": _rounded(
                self.parent_winner_overlap_ratio
            ),
            "parent_winner_margin": _rounded(self.parent_winner_margin),
            "parent_ambiguous": self.parent_ambiguous,
            "parent_ambiguity_reasons": list(self.parent_ambiguity_reasons),
            "semantic_part_id": self.semantic_part_id,
            "binding_status": self.binding_status,
            "binding_confidence": _rounded(self.binding_confidence),
            "decision_basis": self.decision_basis,
            "decision_reasons": list(self.decision_reasons),
            "pixel_count": self.pixel_count,
            "bbox_xywh": list(self.bbox_xywh),
            "centroid_xy": [_rounded(value) for value in self.centroid_xy],
            "mean_rgb": [_rounded(value) for value in self.mean_rgb],
            "std_rgb": [_rounded(value) for value in self.std_rgb],
            "pixel_runs": [list(run) for run in self.pixel_runs],
            "adjacent_regions": [item.to_dict() for item in self.adjacent_regions],
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class RegionBindingResult:
    width: int
    height: int
    regions: tuple[RegionBinding, ...]
    validation: dict
    policy: BindingPolicy
    region_labels: np.ndarray

    def to_dict(self) -> dict:
        return {
            "schema_version": "1.1",
            "coordinate_space": {
                "pixel_width": self.width,
                "pixel_height": self.height,
                "normalized_origin": "top-left",
                "normalized_range": [0.0, 1.0],
            },
            "region_generation": {
                "producer": "skimage.segmentation.slic",
                "producer_version": skimage.__version__,
                "role": "region-evidence-only",
                "mask_source": "phase04-semantic-mask-union",
                "semantic_boundary_policy": (
                    "split-with-parent-ambiguity-inheritance-v2"
                ),
                "visible_render_authority": False,
            },
            "binding_policy": self.policy.to_dict(),
            "regions": [region.to_dict() for region in self.regions],
            "validation": self.validation,
        }


def _normalize_inputs(
    rgb: np.ndarray,
    part_masks: Mapping[str, np.ndarray],
) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray]:
    image = np.asarray(rgb, dtype=np.uint8)
    if image.ndim != 3 or image.shape[2] < 3:
        raise ValueError("Phase 6 requires an RGB source image")
    image = image[..., :3].copy()
    missing = [name for name in PART_NAMES if name not in part_masks]
    if missing:
        raise ValueError(f"missing Phase 4 part masks: {missing}")
    masks: dict[str, np.ndarray] = {}
    for name in PART_NAMES:
        mask = np.asarray(part_masks[name])
        if mask.shape != image.shape[:2]:
            raise ValueError(f"part mask {name!r} must match the source dimensions")
        masks[name] = mask.astype(bool, copy=True)
    subject = np.logical_or.reduce([masks[name] for name in PART_NAMES])
    if not np.any(subject):
        raise ValueError("Phase 6 requires a non-empty Phase 4 subject")
    return image, masks, subject


def _exclusive_part_labels(
    masks: Mapping[str, np.ndarray],
    subject: np.ndarray,
) -> np.ndarray:
    labels = np.full(subject.shape, -1, dtype=np.int16)
    for name in DISPLAY_PRIORITY:
        labels[np.asarray(masks[name], dtype=bool) & subject] = PART_NAMES.index(name)
    if np.any(subject & (labels < 0)):
        raise ValueError("Phase 4 masks do not cover their own subject union")
    return labels


def _pixel_runs(mask: np.ndarray) -> tuple[tuple[int, int, int], ...]:
    runs: list[tuple[int, int, int]] = []
    for y in np.flatnonzero(np.any(mask, axis=1)):
        xs = np.flatnonzero(mask[y])
        if xs.size == 0:
            continue
        start = previous = int(xs[0])
        for value in xs[1:]:
            x = int(value)
            if x != previous + 1:
                runs.append((int(y), start, previous + 1))
                start = x
            previous = x
        runs.append((int(y), start, previous + 1))
    return tuple(runs)


def _relation_lookup(
    graph_payload: Mapping,
) -> dict[tuple[str, str], tuple[tuple[str, float, str], ...]]:
    lookup: dict[tuple[str, str], list[tuple[str, float, str]]] = {}
    for relation in graph_payload.get("relations", []):
        source = str(relation.get("source_part", ""))
        target = str(relation.get("target_part", ""))
        relation_id = str(relation.get("relation_id", ""))
        relation_kind = str(relation.get("relation_kind", ""))
        confidence = max(0.0, min(1.0, float(relation.get("confidence", 0.0))))
        if source in PART_NAMES and target in PART_NAMES and relation_id:
            record = (relation_id, confidence, relation_kind)
            lookup.setdefault((source, target), []).append(record)
            lookup.setdefault((target, source), []).append(record)
    return {
        key: tuple(sorted(values, key=lambda item: item[0]))
        for key, values in lookup.items()
    }


def _adjacency_counts(labels: np.ndarray) -> dict[int, dict[int, int]]:
    counts: dict[int, dict[int, int]] = {}
    for first, second in (
        (labels[:, :-1], labels[:, 1:]),
        (labels[:-1, :], labels[1:, :]),
    ):
        changed = (first != second) & (first >= 0) & (second >= 0)
        pairs = zip(first[changed].tolist(), second[changed].tolist())
        for left, right in pairs:
            a, b = int(left), int(right)
            counts.setdefault(a, {})[b] = counts.setdefault(a, {}).get(b, 0) + 1
            counts.setdefault(b, {})[a] = counts.setdefault(b, {}).get(a, 0) + 1
    return counts


def _part_color_means(
    rgb: np.ndarray,
    exclusive_labels: np.ndarray,
) -> dict[str, np.ndarray]:
    means: dict[str, np.ndarray] = {}
    for index, name in enumerate(PART_NAMES):
        pixels = rgb[exclusive_labels == index]
        if pixels.size:
            means[name] = pixels.astype(np.float64).mean(axis=0)
    return means


def _part_geometry(
    exclusive_labels: np.ndarray,
) -> dict[str, tuple[np.ndarray, float]]:
    geometry: dict[str, tuple[np.ndarray, float]] = {}
    for index, name in enumerate(PART_NAMES):
        ys, xs = np.where(exclusive_labels == index)
        if xs.size == 0:
            continue
        centroid = np.asarray([float(xs.mean()), float(ys.mean())], dtype=np.float64)
        diagonal = max(
            float(np.hypot(int(xs.max()) - int(xs.min()) + 1, int(ys.max()) - int(ys.min()) + 1)),
            1.0,
        )
        geometry[name] = (centroid, diagonal)
    return geometry


def _parent_overlap_evidence(
    parent_mask: np.ndarray,
    exclusive_labels: np.ndarray,
    policy: BindingPolicy,
) -> tuple[dict[str, int], str, float, float, tuple[str, ...]]:
    parent_pixel_count = max(int(np.count_nonzero(parent_mask)), 1)
    counts = {
        name: int(np.count_nonzero(parent_mask & (exclusive_labels == index)))
        for index, name in enumerate(PART_NAMES)
    }
    ordered = sorted(
        counts.items(),
        key=lambda item: (-item[1], PART_NAMES.index(item[0])),
    )
    winner, winner_pixels = ordered[0]
    second_pixels = ordered[1][1] if len(ordered) > 1 else 0
    winner_ratio = winner_pixels / float(parent_pixel_count)
    winner_margin = (winner_pixels - second_pixels) / float(parent_pixel_count)
    ratios = {name: count / float(parent_pixel_count) for name, count in counts.items()}
    reasons: list[str] = []
    if winner_ratio < policy.minimum_part_overlap:
        reasons.append("parent-winner-overlap-below-threshold")
    if winner_margin < policy.minimum_winner_margin:
        reasons.append("parent-winner-margin-below-threshold")
    hair_ratio = ratios.get("hair", 0.0)
    clothing_ratio = max((ratios.get(name, 0.0) for name in CLOTHING_PARTS), default=0.0)
    if hair_ratio >= policy.ambiguity_overlap and clothing_ratio >= policy.ambiguity_overlap:
        reasons.append("parent-crosses-hair-clothing-semantic-boundary")
    return counts, winner, winner_ratio, winner_margin, tuple(reasons)


def _split_at_semantic_boundaries(
    labels: np.ndarray,
    exclusive_labels: np.ndarray,
    subject: np.ndarray,
) -> tuple[np.ndarray, dict[int, int]]:
    refined = np.full(labels.shape, -1, dtype=np.int32)
    parents: dict[int, int] = {}
    next_label = 0
    for parent_label in sorted(int(value) for value in np.unique(labels[subject])):
        parent_mask = labels == parent_label
        for part_index in range(len(PART_NAMES)):
            fragment = parent_mask & (exclusive_labels == part_index)
            if not np.any(fragment):
                continue
            component_count, components = cv2.connectedComponents(
                fragment.astype(np.uint8),
                connectivity=8,
            )
            for component_index in range(1, component_count):
                component = components == component_index
                if not np.any(component):
                    continue
                refined[component] = next_label
                parents[next_label] = parent_label
                next_label += 1
    if np.any(refined[subject] < 0):
        raise ValueError("semantic boundary split lost Phase 4 subject pixels")
    return refined, parents


def bind_labeled_regions(
    rgb: np.ndarray,
    region_labels: np.ndarray,
    part_masks: Mapping[str, np.ndarray],
    graph_payload: Mapping,
    *,
    policy: BindingPolicy | None = None,
    parent_region_labels: Mapping[int, int] | None = None,
    parent_region_map: np.ndarray | None = None,
) -> RegionBindingResult:
    policy = policy or BindingPolicy()
    image, masks, subject = _normalize_inputs(rgb, part_masks)
    labels = np.asarray(region_labels)
    if labels.shape != subject.shape:
        raise ValueError("region labels must match the source dimensions")
    labels = labels.astype(np.int32, copy=True)
    if np.any(labels[~subject] >= 0):
        raise ValueError("region labels must not claim pixels outside the Phase 4 subject")
    if np.any(labels[subject] < 0):
        raise ValueError("every Phase 4 subject pixel must belong to a region")

    if parent_region_map is None:
        parent_labels_map = labels.copy()
    else:
        parent_labels_map = np.asarray(parent_region_map).astype(np.int32, copy=True)
        if parent_labels_map.shape != subject.shape:
            raise ValueError("parent region map must match the source dimensions")
        if np.any(parent_labels_map[~subject] >= 0):
            raise ValueError("parent region map must not claim pixels outside the subject")
        if np.any(parent_labels_map[subject] < 0):
            raise ValueError("every subject pixel must belong to a parent region")

    source_labels = tuple(sorted(int(value) for value in np.unique(labels[subject])))
    if not source_labels:
        raise ValueError("Phase 6 requires at least one region")
    region_ids = {label: f"region-{index:04d}" for index, label in enumerate(source_labels)}
    adjacency = _adjacency_counts(labels)
    exclusive = _exclusive_part_labels(masks, subject)
    part_colors = _part_color_means(image, exclusive)
    part_geometry = _part_geometry(exclusive)
    relation_lookup = _relation_lookup(graph_payload)
    part_relation_records: dict[str, set[tuple[str, float, str]]] = {
        name: set() for name in PART_NAMES
    }
    for (source_part, _), records in relation_lookup.items():
        part_relation_records[source_part].update(records)

    graph_parts = set(str(value) for value in graph_payload.get("present_parts", []))
    present_parts = {
        name for name in PART_NAMES if bool(np.any(masks[name])) and name != "unknown"
    }
    if graph_parts != present_parts:
        raise ValueError(
            "Phase 5 graph present_parts do not match non-empty Phase 4 semantic masks"
        )

    bindings: list[RegionBinding] = []
    total_subject_pixels = int(np.count_nonzero(subject))
    for source_label in source_labels:
        region_mask = labels == source_label
        ys, xs = np.where(region_mask)
        pixel_count = int(xs.size)
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        pixels = image[region_mask].astype(np.float64)
        mean_rgb_array = pixels.mean(axis=0)
        std_rgb_array = pixels.std(axis=0)
        region_centroid = np.asarray(
            [float(xs.mean()), float(ys.mean())], dtype=np.float64
        )
        perimeter = region_mask & ~cv2.erode(
            region_mask.astype(np.uint8),
            np.ones((3, 3), dtype=np.uint8),
            iterations=1,
        ).astype(bool)
        perimeter_pixel_count = max(int(np.count_nonzero(perimeter)), 1)

        parent_values = np.unique(parent_labels_map[region_mask])
        if parent_values.size != 1:
            raise ValueError("a refined region must map to exactly one parent region")
        parent_label = int(parent_values[0])
        if parent_region_labels is not None:
            declared_parent = int(parent_region_labels.get(source_label, parent_label))
            if declared_parent != parent_label:
                raise ValueError("parent region label mapping disagrees with parent map")
        parent_mask = parent_labels_map == parent_label
        parent_pixel_count = int(np.count_nonzero(parent_mask))
        (
            parent_exclusive_counts,
            parent_winner,
            parent_winner_ratio,
            parent_winner_margin,
            parent_ambiguity_reasons,
        ) = _parent_overlap_evidence(parent_mask, exclusive, policy)
        parent_ambiguous = bool(parent_ambiguity_reasons)

        overlapping_parts = [
            name
            for index, name in enumerate(PART_NAMES)
            if np.any(region_mask & (exclusive == index))
        ]
        context_parts = set(overlapping_parts)
        context_parts.update(
            name for name, count in parent_exclusive_counts.items() if count > 0
        )
        for adjacent_label in adjacency.get(source_label, {}):
            adjacent_mask = labels == adjacent_label
            adjacent_counts = [
                int(np.count_nonzero(adjacent_mask & (exclusive == index)))
                for index in range(len(PART_NAMES))
            ]
            if max(adjacent_counts, default=0) > 0:
                context_parts.add(PART_NAMES[int(np.argmax(adjacent_counts))])
        candidates: list[BindingCandidate] = []
        for index, name in enumerate(PART_NAMES):
            exclusive_pixels = int(np.count_nonzero(region_mask & (exclusive == index)))
            raw_pixels = int(np.count_nonzero(region_mask & masks[name]))
            parent_exclusive_pixels = parent_exclusive_counts[name]
            parent_raw_pixels = int(np.count_nonzero(parent_mask & masks[name]))
            if (
                exclusive_pixels == 0
                and raw_pixels == 0
                and parent_exclusive_pixels == 0
                and parent_raw_pixels == 0
            ):
                continue
            graph_records = {
                record
                for other in context_parts
                if other != name
                for record in relation_lookup.get((name, other), ())
            }
            graph_records.update(part_relation_records[name])
            graph_ids = sorted(record[0] for record in graph_records)
            graph_support = max((record[1] for record in graph_records), default=0.0)
            part_pixels = max(int(np.count_nonzero(exclusive == index)), 1)
            part_mean = part_colors.get(name, mean_rgb_array)
            color_distance = float(np.linalg.norm(mean_rgb_array - part_mean))
            color_support = max(0.0, 1.0 - color_distance / MAX_RGB_DISTANCE)
            boundary_contact = int(
                np.count_nonzero(perimeter & (exclusive == index))
            )
            boundary_support = boundary_contact / float(perimeter_pixel_count)
            if name in part_geometry:
                part_centroid, part_diagonal = part_geometry[name]
                geometry_distance = float(np.linalg.norm(region_centroid - part_centroid))
                geometry_support = max(0.0, 1.0 - geometry_distance / part_diagonal)
            else:
                geometry_support = 0.0
            region_overlap_ratio = exclusive_pixels / float(pixel_count)
            parent_overlap_ratio = parent_exclusive_pixels / float(parent_pixel_count)
            decision_score = (
                0.35 * region_overlap_ratio
                + 0.25 * parent_overlap_ratio
                + 0.15 * graph_support
                + 0.10 * boundary_support
                + 0.10 * geometry_support
                + 0.05 * color_support
            )
            candidates.append(
                BindingCandidate(
                    part_id=name,
                    exclusive_overlap_pixels=exclusive_pixels,
                    raw_mask_overlap_pixels=raw_pixels,
                    region_overlap_ratio=region_overlap_ratio,
                    parent_exclusive_overlap_pixels=parent_exclusive_pixels,
                    parent_raw_mask_overlap_pixels=parent_raw_pixels,
                    parent_region_overlap_ratio=parent_overlap_ratio,
                    part_coverage_ratio=exclusive_pixels / float(part_pixels),
                    boundary_contact_pixels=boundary_contact,
                    boundary_support=boundary_support,
                    geometry_support=geometry_support,
                    color_distance_rgb=color_distance,
                    color_support=color_support,
                    graph_relation_ids=tuple(graph_ids),
                    graph_support=graph_support,
                    decision_score=decision_score,
                )
            )
        candidates.sort(
            key=lambda item: (
                -item.region_overlap_ratio,
                -item.decision_score,
                PART_NAMES.index(item.part_id),
            )
        )
        top = candidates[0]
        second_score = candidates[1].decision_score if len(candidates) > 1 else 0.0
        decision_margin = top.decision_score - second_score
        reasons: list[str] = []
        if top.region_overlap_ratio < policy.minimum_part_overlap:
            reasons.append("child-winner-overlap-below-threshold")
        if top.decision_score < policy.minimum_decision_score:
            reasons.append("multi-evidence-score-below-threshold")
        if decision_margin < policy.minimum_decision_margin:
            reasons.append("multi-evidence-margin-below-threshold")
        if top.part_id == "unknown":
            reasons.append("unknown-semantic-owner-remains-unbound")

        requires_resolution = parent_ambiguous or top.part_id != parent_winner
        semantic_split_override = (
            requires_resolution
            and parent_region_labels is not None
            and top.part_id != "unknown"
            and top.region_overlap_ratio >= policy.semantic_split_override_min_overlap
            and top.decision_score >= policy.minimum_decision_score
            and decision_margin >= policy.minimum_decision_margin
            and top.graph_support >= policy.minimum_graph_support
            and max(top.boundary_support, top.geometry_support)
            >= policy.minimum_spatial_support
        )
        if (
            "parent-crosses-hair-clothing-semantic-boundary"
            in parent_ambiguity_reasons
            and (top.part_id == "hair" or top.part_id in CLOTHING_PARTS)
            and not semantic_split_override
        ):
            reasons.append("parent-crosses-hair-clothing-semantic-boundary")
        elif requires_resolution and not semantic_split_override:
            if top.graph_support < policy.minimum_graph_support:
                reasons.append("parent-ambiguity-lacks-graph-support")
            if (
                max(top.boundary_support, top.geometry_support)
                < policy.minimum_spatial_support
            ):
                reasons.append("parent-ambiguity-lacks-boundary-or-geometry-support")
        is_bound = not reasons
        confidence = min(1.0, top.decision_score)
        evidence_refs = {
            "derived:slic-region-mask",
            "derived:exclusive-phase04-overlap",
            "derived:parent-slic-overlap-and-margin",
            "derived:region-boundary-support",
            "derived:part-centroid-geometry-support",
            "source:rgb-color-statistics",
            f"phase04:part_masks/{top.part_id}.png",
        }
        if parent_region_labels is not None:
            evidence_refs.add("derived:semantic-boundary-split")
        evidence_refs.update(f"phase05:{value}" for value in top.graph_relation_ids)
        adjacent = tuple(
            RegionAdjacency(region_ids[other], count)
            for other, count in sorted(
                adjacency.get(source_label, {}).items(),
                key=lambda item: region_ids[item[0]],
            )
        )
        bindings.append(
            RegionBinding(
                region_id=region_ids[source_label],
                source_region_label=source_label,
                parent_region_label=parent_label,
                parent_pixel_count=parent_pixel_count,
                parent_winner_part_id=parent_winner,
                parent_winner_overlap_ratio=parent_winner_ratio,
                parent_winner_margin=parent_winner_margin,
                parent_ambiguous=parent_ambiguous,
                parent_ambiguity_reasons=parent_ambiguity_reasons,
                semantic_part_id=top.part_id if is_bound else None,
                binding_status="bound" if is_bound else "unbound",
                binding_confidence=confidence,
                decision_basis=(
                    "multi-evidence-region-binding"
                    if is_bound
                    else "unbound-insufficient-semantic-evidence"
                ),
                decision_reasons=tuple(
                    reasons
                    or [
                        (
                            "semantic-boundary-split-resolved-by-child-evidence"
                            if semantic_split_override
                            else (
                                "parent-ambiguity-resolved-by-graph-and-spatial-support"
                                if requires_resolution
                                else "parent-and-child-evidence-consistent"
                            )
                        )
                    ]
                ),
                pixel_count=pixel_count,
                bbox_xywh=(x0, y0, x1 - x0, y1 - y0),
                centroid_xy=(float(region_centroid[0]), float(region_centroid[1])),
                mean_rgb=tuple(float(value) for value in mean_rgb_array),
                std_rgb=tuple(float(value) for value in std_rgb_array),
                pixel_runs=_pixel_runs(region_mask),
                adjacent_regions=adjacent,
                candidates=tuple(candidates),
                evidence_refs=tuple(sorted(evidence_refs)),
            )
        )

    bound_pixels = sum(
        region.pixel_count for region in bindings if region.binding_status == "bound"
    )
    forced_low_confidence = [
        region.region_id
        for region in bindings
        if region.binding_status == "bound"
        and (
            region.candidates[0].region_overlap_ratio < policy.minimum_part_overlap
            or region.candidates[0].decision_score < policy.minimum_decision_score
            or (
                region.candidates[0].decision_score
                - (region.candidates[1].decision_score if len(region.candidates) > 1 else 0.0)
                < policy.minimum_decision_margin
            )
        )
    ]
    crossing_unbound: list[str] = []
    crossing_forced: list[str] = []
    semantic_split_override_bindings: list[str] = []
    for region in bindings:
        resolved_by_split = (
            "semantic-boundary-split-resolved-by-child-evidence"
            in region.decision_reasons
        )
        if resolved_by_split and region.binding_status == "bound":
            semantic_split_override_bindings.append(region.region_id)
        if (
            "parent-crosses-hair-clothing-semantic-boundary"
            in region.parent_ambiguity_reasons
            and (
                region.candidates[0].part_id == "hair"
                or region.candidates[0].part_id in CLOTHING_PARTS
            )
        ):
            if region.binding_status == "unbound":
                crossing_unbound.append(region.region_id)
            elif not resolved_by_split:
                crossing_forced.append(region.region_id)

    parent_ambiguous_regions = [
        region.region_id for region in bindings if region.parent_ambiguous
    ]
    parent_ambiguous_unbound = [
        region.region_id
        for region in bindings
        if region.parent_ambiguous and region.binding_status == "unbound"
    ]
    graph_supported_bindings = [
        region.region_id
        for region in bindings
        if region.binding_status == "bound"
        and region.candidates[0].graph_support >= policy.minimum_graph_support
    ]
    display_priority_only_bindings = [
        region.region_id
        for region in bindings
        if region.binding_status == "bound"
        and (
            region.parent_ambiguous
            or region.candidates[0].part_id != region.parent_winner_part_id
        )
        and region.candidates[0].graph_support < policy.minimum_graph_support
    ]

    validation = {
        "subject_pixel_count": total_subject_pixels,
        "region_pixel_count": sum(region.pixel_count for region in bindings),
        "subject_pixel_coverage": _rounded(
            sum(region.pixel_count for region in bindings) / float(total_subject_pixels)
        ),
        "outside_subject_claim_count": int(np.count_nonzero(labels[~subject] >= 0)),
        "forced_low_confidence_regions": forced_low_confidence,
        "hair_clothing_crossing_unbound_regions": crossing_unbound,
        "hair_clothing_forced_binding_regions": crossing_forced,
        "semantic_split_override_bindings": semantic_split_override_bindings,
        "parent_ambiguous_regions": parent_ambiguous_regions,
        "parent_ambiguous_unbound_regions": parent_ambiguous_unbound,
        "graph_supported_binding_regions": graph_supported_bindings,
        "display_priority_only_binding_regions": display_priority_only_bindings,
        "color_only_binding_count": 0,
        "bound_pixel_ratio": _rounded(bound_pixels / float(total_subject_pixels)),
        "pass": (
            sum(region.pixel_count for region in bindings) == total_subject_pixels
            and not forced_low_confidence
            and not crossing_forced
            and not display_priority_only_bindings
            and not np.any(labels[~subject] >= 0)
        ),
    }
    return RegionBindingResult(
        width=int(image.shape[1]),
        height=int(image.shape[0]),
        regions=tuple(bindings),
        validation=validation,
        policy=policy,
        region_labels=labels,
    )


def build_region_bindings(
    rgb: np.ndarray,
    part_masks: Mapping[str, np.ndarray],
    graph_payload: Mapping,
    *,
    policy: BindingPolicy | None = None,
) -> RegionBindingResult:
    policy = policy or BindingPolicy()
    image, masks, subject = _normalize_inputs(rgb, part_masks)
    labels = slic(
        image,
        n_segments=policy.n_segments,
        compactness=policy.compactness,
        start_label=0,
        convert2lab=True,
        enforce_connectivity=True,
        mask=subject,
        channel_axis=-1,
    )
    # SLIC can leave rare masked subject pixels unlabeled on fragmented
    # silhouettes. Assign those holes to the nearest observed SLIC region
    # before semantic splitting. No source pixels or semantics are generated.
    missing_parent = subject & (labels < 0)
    if np.any(missing_parent):
        known = subject & (labels >= 0)
        if not np.any(known):
            raise ValueError("SLIC produced no parent regions inside the subject")
        _, nearest = cv2.distanceTransformWithLabels(
            (~known).astype(np.uint8),
            cv2.DIST_L2,
            5,
            labelType=cv2.DIST_LABEL_PIXEL,
        )
        known_coords = np.argwhere(known)
        lookup = np.asarray(
            [labels[y, x] for y, x in known_coords],
            dtype=np.int32,
        )
        fill_ids = nearest[missing_parent] - 1
        labels[missing_parent] = lookup[np.clip(fill_ids, 0, len(lookup) - 1)]
    exclusive = _exclusive_part_labels(masks, subject)
    refined_labels, parent_labels = _split_at_semantic_boundaries(
        labels,
        exclusive,
        subject,
    )
    return bind_labeled_regions(
        image,
        refined_labels,
        masks,
        graph_payload,
        policy=policy,
        parent_region_labels=parent_labels,
        parent_region_map=labels,
    )
