from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import cv2
import numpy as np
import skimage
from skimage.segmentation import slic

from minimalizer_zerobase.parts.decomposition import DISPLAY_PRIORITY, PART_NAMES


def _rounded(value: float) -> float:
    return round(float(value), 6)


@dataclass(frozen=True)
class BindingPolicy:
    n_segments: int = 180
    compactness: float = 12.0
    minimum_part_overlap: float = 0.55
    minimum_winner_margin: float = 0.15
    ambiguity_overlap: float = 0.20

    def __post_init__(self) -> None:
        if self.n_segments < 2:
            raise ValueError("n_segments must be at least 2")
        if self.compactness <= 0:
            raise ValueError("compactness must be positive")
        for name in (
            "minimum_part_overlap",
            "minimum_winner_margin",
            "ambiguity_overlap",
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
    part_coverage_ratio: float
    boundary_contact_pixels: int
    color_distance_rgb: float
    graph_relation_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "part_id": self.part_id,
            "exclusive_overlap_pixels": self.exclusive_overlap_pixels,
            "raw_mask_overlap_pixels": self.raw_mask_overlap_pixels,
            "region_overlap_ratio": _rounded(self.region_overlap_ratio),
            "part_coverage_ratio": _rounded(self.part_coverage_ratio),
            "boundary_contact_pixels": self.boundary_contact_pixels,
            "color_distance_rgb": _rounded(self.color_distance_rgb),
            "graph_relation_ids": list(self.graph_relation_ids),
        }


@dataclass(frozen=True)
class RegionBinding:
    region_id: str
    source_region_label: int
    parent_region_label: int
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
            "schema_version": "1.0",
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
                "semantic_boundary_policy": "split-at-phase04-exclusive-boundaries-v1",
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


def _relation_lookup(graph_payload: Mapping) -> dict[tuple[str, str], tuple[str, ...]]:
    lookup: dict[tuple[str, str], list[str]] = {}
    for relation in graph_payload.get("relations", []):
        source = str(relation.get("source_part", ""))
        target = str(relation.get("target_part", ""))
        relation_id = str(relation.get("relation_id", ""))
        if source in PART_NAMES and target in PART_NAMES and relation_id:
            lookup.setdefault((source, target), []).append(relation_id)
            lookup.setdefault((target, source), []).append(relation_id)
    return {key: tuple(sorted(values)) for key, values in lookup.items()}


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

    source_labels = tuple(sorted(int(value) for value in np.unique(labels[subject])))
    if not source_labels:
        raise ValueError("Phase 6 requires at least one region")
    region_ids = {label: f"region-{index:04d}" for index, label in enumerate(source_labels)}
    adjacency = _adjacency_counts(labels)
    exclusive = _exclusive_part_labels(masks, subject)
    part_colors = _part_color_means(image, exclusive)
    relation_lookup = _relation_lookup(graph_payload)

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
        perimeter = region_mask & ~cv2.erode(
            region_mask.astype(np.uint8),
            np.ones((3, 3), dtype=np.uint8),
            iterations=1,
        ).astype(bool)

        overlapping_parts = [
            name
            for index, name in enumerate(PART_NAMES)
            if np.any(region_mask & (exclusive == index))
        ]
        context_parts = set(overlapping_parts)
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
            if exclusive_pixels == 0 and raw_pixels == 0:
                continue
            graph_ids = sorted(
                {
                    relation_id
                    for other in context_parts
                    if other != name
                    for relation_id in relation_lookup.get((name, other), ())
                }
            )
            part_pixels = max(int(np.count_nonzero(exclusive == index)), 1)
            part_mean = part_colors.get(name, mean_rgb_array)
            color_distance = float(np.linalg.norm(mean_rgb_array - part_mean))
            candidates.append(
                BindingCandidate(
                    part_id=name,
                    exclusive_overlap_pixels=exclusive_pixels,
                    raw_mask_overlap_pixels=raw_pixels,
                    region_overlap_ratio=exclusive_pixels / float(pixel_count),
                    part_coverage_ratio=exclusive_pixels / float(part_pixels),
                    boundary_contact_pixels=int(
                        np.count_nonzero(perimeter & (exclusive == index))
                    ),
                    color_distance_rgb=color_distance,
                    graph_relation_ids=tuple(graph_ids),
                )
            )
        candidates.sort(
            key=lambda item: (
                -item.exclusive_overlap_pixels,
                PART_NAMES.index(item.part_id),
            )
        )
        top = candidates[0]
        second_ratio = candidates[1].region_overlap_ratio if len(candidates) > 1 else 0.0
        margin = top.region_overlap_ratio - second_ratio
        reasons: list[str] = []
        if top.region_overlap_ratio < policy.minimum_part_overlap:
            reasons.append("winner-overlap-below-threshold")
        if margin < policy.minimum_winner_margin:
            reasons.append("winner-margin-below-threshold")
        ratios = {candidate.part_id: candidate.region_overlap_ratio for candidate in candidates}
        clothing_parts = {
            "torso",
            "major_clothing",
            "left_arm",
            "right_arm",
            "lower_body",
        }
        hair_ratio = ratios.get("hair", 0.0)
        clothing_ratio = max(
            (ratios.get(name, 0.0) for name in clothing_parts),
            default=0.0,
        )
        if (
            hair_ratio >= policy.ambiguity_overlap
            and clothing_ratio >= policy.ambiguity_overlap
        ):
            reasons.append("crosses-hair-clothing-semantic-boundary")
        is_bound = not reasons
        confidence = min(1.0, 0.8 * top.region_overlap_ratio + 0.2 * max(margin, 0.0))
        evidence_refs = {
            "derived:slic-region-mask",
            "derived:exclusive-phase04-overlap",
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
                parent_region_label=int(
                    parent_region_labels.get(source_label, source_label)
                    if parent_region_labels is not None
                    else source_label
                ),
                semantic_part_id=top.part_id if is_bound else None,
                binding_status="bound" if is_bound else "unbound",
                binding_confidence=confidence,
                decision_basis=(
                    "phase04-mask-overlap"
                    if is_bound
                    else "unbound-insufficient-semantic-evidence"
                ),
                decision_reasons=tuple(reasons or ["winner-cleared-overlap-and-margin"]),
                pixel_count=pixel_count,
                bbox_xywh=(x0, y0, x1 - x0, y1 - y0),
                centroid_xy=(float(xs.mean()), float(ys.mean())),
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
            or (
                region.candidates[0].region_overlap_ratio
                - (
                    region.candidates[1].region_overlap_ratio
                    if len(region.candidates) > 1
                    else 0.0
                )
                < policy.minimum_winner_margin
            )
        )
    ]
    crossing_unbound: list[str] = []
    crossing_forced: list[str] = []
    clothing_parts = {"torso", "major_clothing", "left_arm", "right_arm", "lower_body"}
    for region in bindings:
        ratios = {item.part_id: item.region_overlap_ratio for item in region.candidates}
        hair_ratio = ratios.get("hair", 0.0)
        clothing_ratio = max((ratios.get(name, 0.0) for name in clothing_parts), default=0.0)
        if hair_ratio >= policy.ambiguity_overlap and clothing_ratio >= policy.ambiguity_overlap:
            if region.binding_status == "unbound":
                crossing_unbound.append(region.region_id)
            else:
                crossing_forced.append(region.region_id)

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
        "color_only_binding_count": 0,
        "bound_pixel_ratio": _rounded(bound_pixels / float(total_subject_pixels)),
        "pass": (
            sum(region.pixel_count for region in bindings) == total_subject_pixels
            and not forced_low_confidence
            and not crossing_forced
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
    )
