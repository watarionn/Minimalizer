from __future__ import annotations

from collections.abc import Mapping

import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.types import (
    CharacteristicContext,
    CharacteristicSupport,
    ImageBundle,
    LabelMap,
    RegionAnnotation,
    RegionId,
)

SemanticRegions = Mapping[RegionId, tuple[str, float]]
StructuralRegions = Mapping[RegionId, tuple[str, float]]


def _validate_initial_labels(bundle: ImageBundle, labels: LabelMap) -> NDArray[np.int32]:
    array = np.asarray(labels)
    if array.dtype != np.int32:
        raise ValueError("initial labels must have dtype int32")
    if array.ndim != 2 or array.shape != bundle.analysis_rgb.shape[:2]:
        raise ValueError("initial labels must match analysis resolution")
    if array.size == 0 or np.any(array < 0):
        raise ValueError("initial labels must be non-empty and non-negative")
    region_ids = np.unique(array)
    expected = np.arange(region_ids.size, dtype=np.int32)
    if not np.array_equal(region_ids, expected):
        raise ValueError("initial labels must be sequential from 0")
    return array


def _characteristic_supports(
    labels: NDArray[np.int32],
    characteristic: CharacteristicContext | None,
) -> dict[RegionId, tuple[CharacteristicSupport, ...]]:
    region_ids = np.unique(labels)
    empty = {int(region_id): () for region_id in region_ids}
    if characteristic is None or characteristic.anchor_map is None:
        return empty

    anchor_map = characteristic.anchor_map
    if anchor_map.shape != labels.shape:
        raise ValueError("anchor_map must match analysis resolution")
    if np.any(anchor_map < -1):
        raise ValueError("anchor_map may only use -1 or known anchor ids")

    anchors = {anchor.id: anchor for anchor in characteristic.anchors}
    used_anchor_ids = set(int(value) for value in np.unique(anchor_map) if value >= 0)
    unknown = used_anchor_ids - set(anchors)
    if unknown:
        raise ValueError(f"anchor_map references unknown anchor ids: {sorted(unknown)}")

    confidence_map = characteristic.confidence_map
    if confidence_map is not None:
        if confidence_map.shape != labels.shape:
            raise ValueError("confidence_map must match analysis resolution")
        if not np.all(np.isfinite(confidence_map)) or np.any((confidence_map < 0.0) | (confidence_map > 1.0)):
            raise ValueError("confidence_map values must be finite and within [0, 1]")

    result: dict[RegionId, tuple[CharacteristicSupport, ...]] = {}
    for region_id in region_ids:
        region_mask = labels == region_id
        supports: list[CharacteristicSupport] = []
        for anchor_id in sorted(used_anchor_ids):
            mask = region_mask & (anchor_map == anchor_id)
            count = int(np.count_nonzero(mask))
            if count == 0:
                continue
            anchor_confidence = anchors[anchor_id].confidence
            if confidence_map is None:
                confidence = anchor_confidence
            else:
                local_confidence = float(np.mean(confidence_map[mask], dtype=np.float64))
                confidence = anchor_confidence * local_confidence
            supports.append(
                CharacteristicSupport(
                    anchor_id=anchor_id,
                    support_mass=float(count),
                    confidence=confidence,
                )
            )
        result[int(region_id)] = tuple(supports)
    return result


def annotate_initial_regions(
    bundle: ImageBundle,
    labels: LabelMap,
    *,
    characteristic: CharacteristicContext | None = None,
    semantic: SemanticRegions | None = None,
    structural: StructuralRegions | None = None,
) -> Mapping[RegionId, RegionAnnotation]:
    labels32 = _validate_initial_labels(bundle, labels)
    supports = _characteristic_supports(labels32, characteristic)

    semantic = semantic or {}
    structural = structural or {}
    valid_ids = set(int(value) for value in np.unique(labels32))
    unknown_semantic = set(semantic) - valid_ids
    if unknown_semantic:
        raise ValueError(f"semantic annotations reference unknown regions: {sorted(unknown_semantic)}")
    unknown_structural = set(structural) - valid_ids
    if unknown_structural:
        raise ValueError(
            f"structural annotations reference unknown regions: {sorted(unknown_structural)}"
        )

    annotations: dict[RegionId, RegionAnnotation] = {}
    for region_id in sorted(valid_ids):
        semantic_tag: str | None = None
        semantic_confidence = 0.0
        if region_id in semantic:
            semantic_tag, semantic_confidence = semantic[region_id]
            if not isinstance(semantic_tag, str) or not semantic_tag:
                raise ValueError("semantic tags must be non-empty strings")
            semantic_confidence = float(semantic_confidence)
        structure_tag: str | None = None
        structure_confidence = 0.0
        if region_id in structural:
            structure_tag, structure_confidence = structural[region_id]
            if not isinstance(structure_tag, str) or not structure_tag:
                raise ValueError("structural tags must be non-empty strings")
            structure_confidence = float(structure_confidence)
        annotations[region_id] = RegionAnnotation(
            characteristic_supports=supports[region_id],
            semantic_tag=semantic_tag,
            semantic_confidence=semantic_confidence,
            structure_tag=structure_tag,
            structure_confidence=structure_confidence,
        )
    return annotations
