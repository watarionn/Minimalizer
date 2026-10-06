from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

import cv2
import numpy as np

from minimalizer_zerobase.production.feature_survival_gate import (
    FeatureSignature,
    extract_feature_signatures,
    _signature_distance,
)

MISSING_SIGNATURE_ATTRIBUTION_VERSION = "sa7.36-v1"


@dataclass(frozen=True)
class RoleOverlap:
    role: str
    pixels: int
    ratio: float


@dataclass(frozen=True)
class MissingSignatureAttribution:
    version: str
    missing_signature: FeatureSignature
    source_signature: FeatureSignature
    source_signature_distance: float
    source_component_area: int
    source_component_cx: float
    source_component_cy: float
    component_distance_to_source_signature: float
    role_overlaps: tuple[RoleOverlap, ...]
    primary_role: str | None
    primary_overlap_ratio: float

    def to_dict(self) -> dict:
        return asdict(self)


def _quantized_rgb(image: np.ndarray, step: int = 32) -> np.ndarray:
    a = np.asarray(image, dtype=np.uint8)
    # Use integer widening before addition so 255 stays 255 instead of wrapping.
    q = (a.astype(np.int16) // step) * step + step // 2
    return np.minimum(255, q).astype(np.uint8)


def _nearest_component(
    mask: np.ndarray,
    *,
    target_cx: float,
    target_cy: float,
) -> tuple[np.ndarray, int, float, float, float]:
    h, w = mask.shape
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8), 8
    )
    if count <= 1:
        raise ValueError("source-supported signature has no connected source component")

    candidates = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area <= 0:
            continue
        cx = float(centroids[label][0] / max(1, w - 1))
        cy = float(centroids[label][1] / max(1, h - 1))
        distance = float(((cx - target_cx) ** 2 + (cy - target_cy) ** 2) ** .5)
        candidates.append((distance, -area, label, area, cx, cy))

    if not candidates:
        raise ValueError("source-supported signature has no usable source component")

    distance, _, label, area, cx, cy = min(candidates)
    return labels == label, area, cx, cy, distance


def attribute_missing_signature(
    *,
    missing_signature: FeatureSignature,
    source_rgb: np.ndarray,
    subject_mask: np.ndarray,
    semantic_masks: Mapping[str, np.ndarray],
    match_threshold: float = .20,
) -> MissingSignatureAttribution:
    """Map one canonical missing signature back to source semantic evidence.

    This is evaluation evidence only. It uses the original source image,
    source-derived subject mask, and source semantic masks. Golden is absent.

    The missing baseline signature is first matched to the nearest source
    signature under the same color/spatial metric as Feature Survival. The
    nearest connected source component for that source signature is then
    intersected with semantic masks to expose likely semantic ownership.
    """
    source = np.asarray(source_rgb, dtype=np.uint8)
    subject = np.asarray(subject_mask, dtype=bool)

    if source.ndim != 3 or source.shape[2] != 3:
        raise ValueError("source_rgb must be HxWx3")
    h, w = source.shape[:2]
    if subject.shape != (h, w):
        raise ValueError("subject mask shape mismatch")
    if not np.any(subject):
        raise ValueError("subject mask is empty")

    masks = {role: np.asarray(mask, dtype=bool) for role, mask in semantic_masks.items()}
    if any(mask.shape != (h, w) for mask in masks.values()):
        raise ValueError("semantic mask shape mismatch")

    source_signatures = extract_feature_signatures(source, subject)
    if not source_signatures:
        raise ValueError("source has no feature signatures")

    source_signature = min(
        source_signatures,
        key=lambda candidate: _signature_distance(missing_signature, candidate),
    )
    source_distance = float(
        _signature_distance(missing_signature, source_signature)
    )
    if source_distance > match_threshold:
        raise ValueError("missing signature is not source-supported")

    quantized = _quantized_rgb(source)
    target = np.asarray(source_signature.rgb, dtype=np.uint8)
    support = np.all(quantized == target, axis=2) & subject

    component, area, cx, cy, component_distance = _nearest_component(
        support,
        target_cx=source_signature.cx,
        target_cy=source_signature.cy,
    )

    overlaps = []
    for role in sorted(masks):
        pixels = int((component & masks[role]).sum())
        if pixels <= 0:
            continue
        overlaps.append(RoleOverlap(role, pixels, float(pixels / area)))

    overlaps.sort(key=lambda row: (-row.ratio, row.role))
    overlap_tuple = tuple(overlaps)
    primary = overlap_tuple[0] if overlap_tuple else None

    return MissingSignatureAttribution(
        version=MISSING_SIGNATURE_ATTRIBUTION_VERSION,
        missing_signature=missing_signature,
        source_signature=source_signature,
        source_signature_distance=source_distance,
        source_component_area=area,
        source_component_cx=cx,
        source_component_cy=cy,
        component_distance_to_source_signature=component_distance,
        role_overlaps=overlap_tuple,
        primary_role=primary.role if primary else None,
        primary_overlap_ratio=primary.ratio if primary else 0.0,
    )


def attribute_missing_signatures(
    *,
    missing_signatures: tuple[FeatureSignature, ...],
    source_rgb: np.ndarray,
    subject_mask: np.ndarray,
    semantic_masks: Mapping[str, np.ndarray],
    match_threshold: float = .20,
) -> tuple[MissingSignatureAttribution, ...]:
    return tuple(
        attribute_missing_signature(
            missing_signature=signature,
            source_rgb=source_rgb,
            subject_mask=subject_mask,
            semantic_masks=semantic_masks,
            match_threshold=match_threshold,
        )
        for signature in missing_signatures
    )
