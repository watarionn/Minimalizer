from __future__ import annotations

import numpy as np

from minimalize_engine.v2.contour.types import ContourSimplificationResult
from minimalize_engine.v2.palette.hierarchy import (
    build_palette_hierarchy,
    build_palette_relationships,
)
from minimalize_engine.v2.palette.sampling import ciede2000, sample_region_colors
from minimalize_engine.v2.palette.types import (
    PaletteConfig,
    PaletteConsolidationMetrics,
    PaletteConsolidationResult,
    PaletteEntry,
    PaletteHierarchy,
    PaletteRelationship,
    RegionColorSample,
)
from minimalize_engine.v2.primitive.types import PrimitiveFittingResult
from minimalize_engine.v2.region_merge.types import RegionSelection
from minimalize_engine.v2.types import CharacteristicContext, ImageBundle, RegionId


def _desired_palette_count(
    samples: dict[RegionId, RegionColorSample],
    target: tuple[int, int],
    config: PaletteConfig,
) -> int:
    lower, upper = target
    if config.mode == "fixed":
        desired = lower
    elif config.mode == "characteristic":
        anchor_count = len({anchor_id for sample in samples.values() for anchor_id in sample.anchor_ids})
        desired = max(upper, anchor_count)
    elif config.mode == "area":
        desired = lower
    else:
        desired = (lower + upper) // 2
    return max(1, min(int(desired), len(samples)))


def _cut_hierarchy(hierarchy: PaletteHierarchy, desired_count: int) -> set[int]:
    active = set(hierarchy.leaf_ids)
    if len(active) <= desired_count:
        return active
    for node_id in hierarchy.merge_sequence:
        if len(active) <= desired_count:
            break
        node = hierarchy.nodes[node_id]
        assert node.left_id is not None and node.right_id is not None
        if node.left_id not in active or node.right_id not in active:
            raise ValueError("palette merge sequence is not replayable")
        active.remove(node.left_id)
        active.remove(node.right_id)
        active.add(node_id)
    return active


def _region_to_node(
    selected: set[int], hierarchy: PaletteHierarchy
) -> dict[RegionId, int]:
    mapping: dict[RegionId, int] = {}
    for node_id in selected:
        for region_id in hierarchy.nodes[node_id].member_regions:
            if region_id in mapping:
                raise ValueError("palette cut assigns a region more than once")
            mapping[region_id] = node_id
    return mapping


def _relationship_is_broken(
    relationship: PaletteRelationship,
    mapping: dict[RegionId, int],
    hierarchy: PaletteHierarchy,
    config: PaletteConfig,
) -> bool:
    node_a = hierarchy.nodes[mapping[relationship.region_a]]
    node_b = hierarchy.nodes[mapping[relationship.region_b]]
    assigned_delta_e = float(ciede2000(node_a.lab, node_b.lab))
    assigned_delta_l = float(node_a.lab[0] - node_b.lab[0])
    if "characteristic_anchor" in relationship.reasons:
        if mapping[relationship.region_a] == mapping[relationship.region_b]:
            return True
    if (
        relationship.original_delta_e >= config.contrast_original_delta_e
        and assigned_delta_e <= config.contrast_assigned_delta_e
    ):
        return True
    if abs(relationship.original_delta_l) >= config.significant_delta_l:
        if relationship.original_delta_l * assigned_delta_l < 0.0:
            return True
    return False


def _split_selected_node(selected: set[int], node_id: int, hierarchy: PaletteHierarchy) -> bool:
    node = hierarchy.nodes[node_id]
    if node.left_id is None or node.right_id is None:
        return False
    selected.remove(node_id)
    selected.add(node.left_id)
    selected.add(node.right_id)
    return True


def _repair_relationships(
    selected: set[int],
    hierarchy: PaletteHierarchy,
    samples: dict[RegionId, RegionColorSample],
    relationships: tuple[PaletteRelationship, ...],
    config: PaletteConfig,
) -> tuple[set[int], int]:
    repaired = 0
    maximum_steps = max(len(hierarchy.nodes) * 2, 1)
    for _ in range(maximum_steps):
        mapping = _region_to_node(selected, hierarchy)
        broken = next(
            (item for item in relationships if _relationship_is_broken(item, mapping, hierarchy, config)),
            None,
        )
        if broken is None:
            return selected, repaired
        node_a_id = mapping[broken.region_a]
        node_b_id = mapping[broken.region_b]
        if node_a_id == node_b_id:
            if not _split_selected_node(selected, node_a_id, hierarchy):
                raise ValueError("protected relationship collapsed inside a palette leaf")
            repaired += 1
            continue

        options: list[tuple[float, int]] = []
        for region_id, node_id in (
            (broken.region_a, node_a_id),
            (broken.region_b, node_b_id),
        ):
            node = hierarchy.nodes[node_id]
            if node.left_id is None:
                continue
            error = float(ciede2000(samples[region_id].lab, node.lab))
            options.append((error, node_id))
        if not options:
            raise ValueError("protected relationship cannot be repaired by hierarchy splitting")
        options.sort(key=lambda item: (-item[0], item[1]))
        if not _split_selected_node(selected, options[0][1], hierarchy):
            raise ValueError("failed to split selected palette node")
        repaired += 1
    raise ValueError("palette relationship repair exceeded deterministic step limit")


def _entries_and_assignments(
    selected: set[int],
    hierarchy: PaletteHierarchy,
) -> tuple[dict[int, PaletteEntry], dict[RegionId, int]]:
    entries: dict[int, PaletteEntry] = {}
    assignments: dict[RegionId, int] = {}
    for node_id in sorted(selected):
        node = hierarchy.nodes[node_id]
        entries[node_id] = PaletteEntry(
            palette_id=node_id,
            member_regions=node.member_regions,
            representative_region_id=node.representative_region_id,
            lab=node.lab,
            rgb=node.rgb,
            source_xy=node.source_xy,
            anchor_ids=node.anchor_ids,
        )
        for region_id in node.member_regions:
            assignments[region_id] = node_id
    return entries, assignments


def _max_assignment_delta_e(
    assignments: dict[RegionId, int],
    entries: dict[int, PaletteEntry],
    samples: dict[RegionId, RegionColorSample],
) -> float:
    return max(
        float(ciede2000(samples[region_id].lab, entries[palette_id].lab))
        for region_id, palette_id in assignments.items()
    )


def _standard_subject_class(
    ratio: float,
    confidence: float,
    config: PaletteConfig,
) -> int:
    if confidence < config.subject_confidence_threshold:
        return 0
    if ratio >= config.subject_high_threshold:
        return 1
    if ratio <= config.subject_low_threshold:
        return -1
    return 0


def _build_subject_classes(
    bundle: ImageBundle,
    selection: RegionSelection,
    samples: dict[RegionId, RegionColorSample],
    config: PaletteConfig,
) -> dict[RegionId, int] | None:
    if bundle.subject_prob is None:
        return None

    stats: dict[RegionId, tuple[float, float]] = {}
    classes: dict[RegionId, int] = {}
    for region_id in sorted(selection.region_ids):
        mask = selection.labels == region_id
        ratio = float(np.mean(bundle.subject_prob[mask], dtype=np.float64))
        confidence = 1.0 if bundle.subject_confidence is None else float(
            np.mean(bundle.subject_confidence[mask], dtype=np.float64)
        )
        stats[region_id] = (ratio, confidence)
        classes[region_id] = _standard_subject_class(ratio, confidence, config)

    confident_background = [
        region_id for region_id, value in classes.items() if value == -1
    ]
    if not confident_background:
        return classes

    for region_id in sorted(selection.region_ids):
        if classes[region_id] != 0:
            continue
        ratio, confidence = stats[region_id]
        if (
            confidence < config.subject_rescue_confidence_threshold
            or confidence >= config.subject_confidence_threshold
            or ratio < config.subject_rescue_high_threshold
        ):
            continue
        closest_background_delta_e = min(
            float(ciede2000(samples[region_id].lab, samples[background_id].lab))
            for background_id in confident_background
        )
        if closest_background_delta_e <= config.subject_rescue_color_delta_e:
            classes[region_id] = 1
    return classes

def consolidate_palette(
    bundle: ImageBundle,
    selection: RegionSelection,
    contour_result: ContourSimplificationResult,
    primitive_result: PrimitiveFittingResult,
    *,
    characteristic: CharacteristicContext | None = None,
    config: PaletteConfig,
) -> PaletteConsolidationResult:
    expected = set(selection.region_ids)
    if set(primitive_result.primitives) != expected:
        raise ValueError("primitive result regions must match selection")
    samples = sample_region_colors(
        bundle,
        selection,
        contour_result,
        characteristic=characteristic,
        config=config,
    )
    relationships = build_palette_relationships(
        bundle,
        selection,
        contour_result,
        samples,
        characteristic=characteristic,
        config=config,
    )
    subject_classes = _build_subject_classes(
        bundle,
        selection,
        samples,
        config,
    )
    hierarchy = build_palette_hierarchy(
        samples,
        relationships,
        characteristic=characteristic,
        config=config,
        subject_classes=subject_classes,
    )
    target = config.target_range(selection.preset)
    desired = _desired_palette_count(samples, target, config)
    selected = _cut_hierarchy(hierarchy, desired)
    selected, repaired = _repair_relationships(
        selected,
        hierarchy,
        samples,
        relationships,
        config,
    )
    entries, assignments = _entries_and_assignments(selected, hierarchy)
    metrics = PaletteConsolidationMetrics(
        region_count=len(samples),
        palette_count=len(entries),
        target_min=target[0],
        target_max=target[1],
        protected_relationship_count=len(relationships),
        repaired_split_count=repaired,
        max_assignment_delta_e=_max_assignment_delta_e(assignments, entries, samples),
    )
    return PaletteConsolidationResult(
        entries=entries,
        region_to_palette=assignments,
        region_samples=samples,
        relationships=relationships,
        hierarchy=hierarchy,
        selected_node_ids=frozenset(selected),
        metrics=metrics,
    )
