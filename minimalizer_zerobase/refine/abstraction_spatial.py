from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import cv2
import numpy as np


@dataclass(frozen=True)
class AbstractionSpatialDescriptor:
    coverage: float
    centroid: tuple[float, float] | None
    bbox: tuple[float, float, float, float] | None
    occupancy: tuple[float, ...]


@dataclass(frozen=True)
class AbstractionSpatialSimilarity:
    coverage: float
    centroid: float
    bbox: float
    occupancy: float
    score: float


def _mask_descriptor(mask: np.ndarray, *, grid_size: int = 8) -> AbstractionSpatialDescriptor:
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim != 2:
        raise ValueError("mask must be 2D")
    h, w = mask.shape
    if h <= 0 or w <= 0 or grid_size <= 0:
        raise ValueError("invalid mask or grid size")
    ys, xs = np.nonzero(mask)
    coverage = float(mask.mean())
    if len(xs) == 0:
        centroid = None
        bbox = None
    else:
        centroid = (float(xs.mean() / max(w - 1, 1)), float(ys.mean() / max(h - 1, 1)))
        bbox = (
            float(xs.min() / max(w - 1, 1)),
            float(ys.min() / max(h - 1, 1)),
            float(xs.max() / max(w - 1, 1)),
            float(ys.max() / max(h - 1, 1)),
        )
    resized = cv2.resize(mask.astype(np.float32), (grid_size, grid_size), interpolation=cv2.INTER_AREA)
    return AbstractionSpatialDescriptor(
        coverage=coverage,
        centroid=centroid,
        bbox=bbox,
        occupancy=tuple(float(v) for v in resized.reshape(-1)),
    )


def descriptors_from_confidence_npz(
    path: str | Path,
    *,
    active_threshold: float = 0.20,
    grid_size: int = 8,
) -> Mapping[str, AbstractionSpatialDescriptor]:
    with np.load(Path(path), allow_pickle=False) as data:
        labels = tuple(str(v) for v in data["labels"].tolist())
        confidence = np.asarray(data["confidence"], dtype=np.float32)
    if confidence.ndim != 3 or confidence.shape[0] != len(labels):
        raise ValueError("confidence evidence must be [label,height,width]")
    if len(set(labels)) != len(labels):
        raise ValueError("confidence evidence labels must be unique")
    result = {}
    for index, label in enumerate(labels):
        channel = confidence[index]
        if not np.isfinite(channel).all():
            raise ValueError(f"non-finite confidence evidence for {label}")
        result[label] = _mask_descriptor(channel >= active_threshold, grid_size=grid_size)
    return result


def _coverage_similarity(a: float, b: float) -> float:
    if a == 0.0 and b == 0.0:
        return 1.0
    return max(0.0, min(1.0, min(a, b) / max(a, b, 1e-9)))


def _centroid_similarity(a: tuple[float, float] | None, b: tuple[float, float] | None) -> float:
    if a is None and b is None:
        return 1.0
    if a is None or b is None:
        return 0.0
    distance = float(np.linalg.norm(np.asarray(a) - np.asarray(b)))
    return max(0.0, 1.0 - distance / np.sqrt(2.0))


def _bbox_similarity(a: tuple[float, float, float, float] | None, b: tuple[float, float, float, float] | None) -> float:
    if a is None and b is None:
        return 1.0
    if a is None or b is None:
        return 0.0
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0, ix1, iy1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    intersection = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    area_a = max(0.0, ax1 - ax0) * max(0.0, ay1 - ay0)
    area_b = max(0.0, bx1 - bx0) * max(0.0, by1 - by0)
    union = area_a + area_b - intersection
    return 1.0 if union <= 1e-12 else intersection / union


def _occupancy_similarity(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    if len(a) != len(b):
        raise ValueError("occupancy grids must share dimensions")
    av, bv = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    return float(max(0.0, min(1.0, 1.0 - np.abs(av - bv).mean())))


def abstraction_similarity(
    reference: AbstractionSpatialDescriptor,
    candidate: AbstractionSpatialDescriptor,
) -> AbstractionSpatialSimilarity:
    coverage = _coverage_similarity(reference.coverage, candidate.coverage)
    centroid = _centroid_similarity(reference.centroid, candidate.centroid)
    bbox = _bbox_similarity(reference.bbox, candidate.bbox)
    occupancy = _occupancy_similarity(reference.occupancy, candidate.occupancy)
    score = 0.15 * coverage + 0.25 * centroid + 0.20 * bbox + 0.40 * occupancy
    return AbstractionSpatialSimilarity(coverage, centroid, bbox, occupancy, score)


def compare_confidence_npz(
    reference_path: str | Path,
    candidate_path: str | Path,
    *,
    active_threshold: float = 0.20,
    grid_size: int = 8,
) -> Mapping[str, AbstractionSpatialSimilarity]:
    reference = descriptors_from_confidence_npz(reference_path, active_threshold=active_threshold, grid_size=grid_size)
    candidate = descriptors_from_confidence_npz(candidate_path, active_threshold=active_threshold, grid_size=grid_size)
    return {
        label: abstraction_similarity(descriptor, candidate[label])
        for label, descriptor in reference.items()
        if label in candidate
    }
