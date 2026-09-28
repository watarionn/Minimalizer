from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import numpy as np
from PIL import Image

from minimalizer_zerobase.analyzers.contracts import Provenance
from minimalizer_zerobase.core.serialization import CanonicalModel


@dataclass(frozen=True)
class SubjectMetadata(CanonicalModel):
    width: int
    height: int
    evidence_source: str
    evidence_provenance: Provenance
    mask_threshold: float
    foreground_ratio: float
    bbox_xywh: tuple[int, int, int, int]
    alpha_present: bool
    alpha_foreground_ratio: float | None
    alpha_informative: bool
    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("subject dimensions must be positive")
        if not 0.0 <= self.mask_threshold <= 1.0:
            raise ValueError("mask_threshold must be 0..1")
        if not 0.0 <= self.foreground_ratio <= 1.0:
            raise ValueError("foreground_ratio must be 0..1")


@dataclass(frozen=True)
class SubjectExtraction:
    mask: np.ndarray
    metadata: SubjectMetadata


ProbabilityProvider = Callable[[np.ndarray], tuple[np.ndarray, Provenance]]


def _bbox_xywh(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask > 0)
    if xs.size == 0:
        raise ValueError("subject mask is empty")
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return (x0, y0, x1 - x0, y1 - y0)


def alpha_is_informative(
    alpha: np.ndarray,
    *,
    threshold: int = 128,
    min_foreground_ratio: float = 0.01,
    max_foreground_ratio: float = 0.97,
) -> tuple[bool, float]:
    if alpha.dtype != np.uint8 or alpha.ndim != 2:
        raise ValueError("alpha must be uint8 HxW")
    ratio = float((alpha >= threshold).mean())
    informative = min_foreground_ratio <= ratio <= max_foreground_ratio
    return informative, ratio


def _remove_tiny_components(
    mask: np.ndarray,
    *,
    minimum_area_ratio: float,
) -> np.ndarray:
    if minimum_area_ratio <= 0:
        return mask.copy()
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    minimum_area = max(1, int(round(mask.size * minimum_area_ratio)))
    kept = np.zeros_like(mask)
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area >= minimum_area:
            kept[labels == label] = 255
    if not np.any(kept):
        return mask.copy()
    return kept


def extract_canonical_subject(
    image: Image.Image,
    *,
    probability_provider: ProbabilityProvider | None = None,
    mask_threshold: float = 0.5,
    minimum_component_area_ratio: float = 0.0002,
    max_alpha_foreground_ratio: float = 0.97,
) -> SubjectExtraction:
    if not 0.0 < mask_threshold < 1.0:
        raise ValueError("mask_threshold must be between 0 and 1")
    alpha_present = "A" in image.getbands()
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]
    alpha_informative = False
    alpha_ratio: float | None = None
    if alpha_present:
        alpha_informative, alpha_ratio = alpha_is_informative(
            alpha,
            max_foreground_ratio=max_alpha_foreground_ratio,
        )

    if alpha_informative:
        probability = alpha.astype(np.float32) / 255.0
        provenance = Provenance(
            producer="minimalizer-zerobase2-subject",
            producer_version="1.0",
            model_id="source-alpha",
        )
        evidence_source = "source-alpha"
    else:
        if probability_provider is None:
            raise ValueError(
                "source alpha is absent/uninformative and no subject probability provider was supplied"
            )
        probability, provenance = probability_provider(rgb)
        probability = np.asarray(probability, dtype=np.float32)
        if probability.shape != alpha.shape:
            raise ValueError("subject probability must match source image dimensions")
        if not np.all(np.isfinite(probability)):
            raise ValueError("subject probability must be finite")
        probability = np.clip(probability, 0.0, 1.0)
        evidence_source = provenance.producer

    mask = np.where(probability >= mask_threshold, 255, 0).astype(np.uint8)
    mask = _remove_tiny_components(
        mask,
        minimum_area_ratio=minimum_component_area_ratio,
    )
    foreground_ratio = float((mask > 0).mean())
    if foreground_ratio <= 0.0:
        raise ValueError("canonical subject extraction produced an empty mask")
    metadata = SubjectMetadata(
        width=int(mask.shape[1]),
        height=int(mask.shape[0]),
        evidence_source=evidence_source,
        evidence_provenance=provenance,
        mask_threshold=float(mask_threshold),
        foreground_ratio=foreground_ratio,
        bbox_xywh=_bbox_xywh(mask),
        alpha_present=alpha_present,
        alpha_foreground_ratio=alpha_ratio,
        alpha_informative=alpha_informative,
    )
    return SubjectExtraction(mask=mask, metadata=metadata)
