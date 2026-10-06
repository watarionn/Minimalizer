from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

import cv2
import numpy as np

from minimalizer_zerobase.production.feature_survival_gate import (
    FeatureSignature,
    extract_feature_signatures,
)

MISSING_SIGNATURE_ATTRIBUTION_VERSION = "sa7.36-v2"
MIN_COMPONENT_FRACTION_OF_MISSING = .10
MIN_COMPONENT_PIXELS = 4


def _signature_distance(a: FeatureSignature, b: FeatureSignature) -> float:
    cd = np.linalg.norm(np.asarray(a.rgb, float) - np.asarray(b.rgb, float)) / 441.673
    sd = ((a.cx - b.cx) ** 2 + (a.cy - b.cy) ** 2) ** .5 / 1.414214
    return float(.72 * cd + .28 * sd)


@dataclass(frozen=True)
class RoleOverlap:
    role: str
    pixels: int
    ratio: float


@dataclass(frozen=True)
class MissingSignatureAttribution:
    version: str
    missing_signature: FeatureSignature
    source_support_signature: FeatureSignature
    source_support_distance: float
    component_signature: FeatureSignature
    component_distance: float
    source_component_area: int
    role_overlaps: tuple[RoleOverlap, ...]
    primary_role: str | None
    primary_overlap_ratio: float

    def to_dict(self) -> dict:
        return asdict(self)


def _quantized_rgb(image: np.ndarray, step: int = 32) -> np.ndarray:
    a = np.asarray(image, dtype=np.uint8)
    q = (a.astype(np.int16) // step) * step + step // 2
    return np.minimum(255, q).astype(np.uint8)


def _component_candidates(
    source: np.ndarray,
    subject: np.ndarray,
    missing_signature: FeatureSignature,
) -> tuple[tuple[FeatureSignature, np.ndarray, int], ...]:
    h, w = subject.shape
    subject_area = max(1, int(subject.sum()))
    minimum_area = max(
        MIN_COMPONENT_PIXELS,
        int(round(missing_signature.area_ratio * subject_area * MIN_COMPONENT_FRACTION_OF_MISSING)),
    )

    quantized = _quantized_rgb(source)
    colors = np.unique(quantized[subject].reshape(-1, 3), axis=0)
    rows = []

    for color in colors:
        raw = np.all(quantized == color, axis=2) & subject
        count, labels, stats, centroids = cv2.connectedComponentsWithStats(
            raw.astype(np.uint8), 8
        )
        for label in range(1, count):
            area = int(stats[label, cv2.CC_STAT_AREA])
            if area < minimum_area:
                continue
            cx = float(centroids[label][0] / max(1, w - 1))
            cy = float(centroids[label][1] / max(1, h - 1))
            signature = FeatureSignature(
                tuple(int(v) for v in color),
                float(area / subject_area),
                cx,
                cy,
            )
            rows.append((signature, labels == label, area))

    return tuple(rows)


def attribute_missing_signature(
    *,
    missing_signature: FeatureSignature,
    source_rgb: np.ndarray,
    subject_mask: np.ndarray,
    semantic_masks: Mapping[str, np.ndarray],
    match_threshold: float = .20,
) -> MissingSignatureAttribution:
    """Map one canonical missing signature back to source semantic evidence.

    The canonical source-signature test first proves that the missing adopted-
    baseline signature is supported by the source under the same gate metric.
    Semantic ownership is then localized with connected quantized-color
    components instead of an aggregate color centroid. Golden is absent.
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

    masks = {
        role: np.asarray(mask, dtype=bool)
        for role, mask in semantic_masks.items()
    }
    if any(mask.shape != (h, w) for mask in masks.values()):
        raise ValueError("semantic mask shape mismatch")

    source_signatures = extract_feature_signatures(source, subject)
    if not source_signatures:
        raise ValueError("source has no feature signatures")

    support_signature = min(
        source_signatures,
        key=lambda candidate: _signature_distance(missing_signature, candidate),
    )
    support_distance = _signature_distance(missing_signature, support_signature)
    if support_distance > match_threshold:
        raise ValueError("missing signature is not source-supported")

    components = _component_candidates(source, subject, missing_signature)
    if not components:
        raise ValueError("no source component is large enough for attribution")

    component_signature, component, area = min(
        components,
        key=lambda row: (
            _signature_distance(missing_signature, row[0]),
            -row[2],
            row[0].rgb,
            row[0].cy,
            row[0].cx,
        ),
    )
    component_distance = _signature_distance(missing_signature, component_signature)
    if component_distance > match_threshold:
        raise ValueError("no source component matches the missing signature")

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
        source_support_signature=support_signature,
        source_support_distance=support_distance,
        component_signature=component_signature,
        component_distance=component_distance,
        source_component_area=area,
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
