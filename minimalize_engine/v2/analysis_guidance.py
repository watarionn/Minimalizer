from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.types import ImageBundle, LabelMap, RegionId

SemanticRegions = dict[RegionId, tuple[str, float]]


def _validate_probability_map(name: str, value: NDArray[np.float32]) -> None:
    if value.dtype != np.float32 or value.ndim != 2:
        raise ValueError(f"{name} must be a float32 2D array")
    if not np.all(np.isfinite(value)) or np.any((value < 0.0) | (value > 1.0)):
        raise ValueError(f"{name} values must be finite and within [0, 1]")


@dataclass(frozen=True, slots=True)
class SemanticGuide:
    labels: tuple[str, ...]
    confidence_maps: NDArray[np.float32]
    provider: str
    model: str

    def __post_init__(self) -> None:
        if not self.labels or any(not label for label in self.labels):
            raise ValueError("semantic labels must be non-empty")
        if len(self.labels) != len(set(self.labels)):
            raise ValueError("semantic labels must be unique")
        if not self.provider or not self.model:
            raise ValueError("semantic provider and model must be non-empty")
        maps = self.confidence_maps
        if maps.dtype != np.float32 or maps.ndim != 3:
            raise ValueError("semantic confidence_maps must be float32 with shape (C, H, W)")
        if maps.shape[0] != len(self.labels) or maps.shape[1] <= 0 or maps.shape[2] <= 0:
            raise ValueError("semantic confidence_maps channels must match labels")
        if not np.all(np.isfinite(maps)) or np.any((maps < 0.0) | (maps > 1.0)):
            raise ValueError("semantic confidence maps must be finite and within [0, 1]")

    @property
    def source_shape(self) -> tuple[int, int]:
        return int(self.confidence_maps.shape[1]), int(self.confidence_maps.shape[2])


@dataclass(frozen=True, slots=True)
class AnalysisGuidance:
    subject_prob: NDArray[np.float32] | None = None
    subject_confidence: NDArray[np.float32] | None = None
    semantic: SemanticGuide | None = None
    subject_provider: str | None = None
    subject_model: str | None = None

    def __post_init__(self) -> None:
        maps: list[NDArray[np.float32]] = []
        for name in ("subject_prob", "subject_confidence"):
            value = getattr(self, name)
            if value is not None:
                _validate_probability_map(name, value)
                maps.append(value)
        if maps and any(value.shape != maps[0].shape for value in maps[1:]):
            raise ValueError("subject guidance maps must have matching shapes")
        if self.semantic is not None:
            if maps and self.semantic.source_shape != maps[0].shape:
                raise ValueError("subject and semantic guidance must share source resolution")
        has_subject = self.subject_prob is not None or self.subject_confidence is not None
        if has_subject and (not self.subject_provider or not self.subject_model):
            raise ValueError("subject guidance requires provider and model metadata")

    def validate_source_shape(self, source_shape: tuple[int, int]) -> None:
        if self.subject_prob is not None and self.subject_prob.shape != source_shape:
            raise ValueError(f"subject guidance must have source shape {source_shape}")
        if self.subject_confidence is not None and self.subject_confidence.shape != source_shape:
            raise ValueError(f"subject guidance must have source shape {source_shape}")
        if self.semantic is not None and self.semantic.source_shape != source_shape:
            raise ValueError(f"semantic guidance must have source shape {source_shape}")


def _resize_confidence_maps(
    confidence_maps: NDArray[np.float32],
    target_shape: tuple[int, int],
) -> NDArray[np.float32]:
    source_shape = confidence_maps.shape[1:]
    if source_shape == target_shape:
        return confidence_maps.copy()
    target_h, target_w = target_shape
    interpolation = cv2.INTER_AREA if target_h <= source_shape[0] and target_w <= source_shape[1] else cv2.INTER_LINEAR
    resized = [cv2.resize(channel, (target_w, target_h), interpolation=interpolation) for channel in confidence_maps]
    return np.clip(np.stack(resized), 0.0, 1.0).astype(np.float32)


def semantic_regions_from_guide(
    bundle: ImageBundle,
    labels: LabelMap,
    guide: SemanticGuide | None,
) -> SemanticRegions | None:
    if guide is None:
        return None
    if guide.source_shape != bundle.source_rgb.shape[:2]:
        raise ValueError("semantic guide must match source image resolution")
    labels32 = np.asarray(labels, dtype=np.int32)
    if labels32.shape != bundle.analysis_rgb.shape[:2]:
        raise ValueError("region labels must match analysis resolution")

    confidence_maps = _resize_confidence_maps(guide.confidence_maps, labels32.shape)
    flat_labels = labels32.ravel()
    region_ids = np.unique(flat_labels).astype(np.int64)
    max_id = int(region_ids[-1])
    counts = np.bincount(flat_labels, minlength=max_id + 1).astype(np.float64)

    means = np.empty((len(guide.labels), max_id + 1), dtype=np.float64)
    for index, confidence in enumerate(confidence_maps):
        sums = np.bincount(flat_labels, weights=confidence.ravel(), minlength=max_id + 1)
        means[index] = np.divide(sums, counts, out=np.zeros_like(sums), where=counts > 0)

    result: SemanticRegions = {}
    for region_id in region_ids:
        rid = int(region_id)
        class_index = int(np.argmax(means[:, rid]))
        result[rid] = (guide.labels[class_index], float(means[class_index, rid]))
    return result
