from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

RegionId: TypeAlias = int
EdgeKey: TypeAlias = tuple[RegionId, RegionId]
BBox: TypeAlias = tuple[int, int, int, int]
LabelMap: TypeAlias = NDArray[np.int32]


def _validate_confidence(name: str, value: float) -> None:
    if not np.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and within [0, 1]")


def _validate_image_array(name: str, value: NDArray, *, dtype: np.dtype, shape: tuple[int, ...] | None = None) -> None:
    if value.dtype != dtype:
        raise ValueError(f"{name} must have dtype {dtype}")
    if shape is not None and value.shape != shape:
        raise ValueError(f"{name} must have shape {shape}")


@dataclass(frozen=True, slots=True)
class ImageBundle:
    source_rgb: NDArray[np.uint8]
    analysis_rgb: NDArray[np.uint8]
    structural_rgb: NDArray[np.uint8]
    analysis_lab: NDArray[np.float32]
    structural_lab: NDArray[np.float32]
    edge_raw: NDArray[np.float32]
    edge_structural: NDArray[np.float32]
    subject_prob: NDArray[np.float32] | None = None
    subject_confidence: NDArray[np.float32] | None = None
    alpha: NDArray[np.float32] | None = None
    scale_x: float = 1.0
    scale_y: float = 1.0

    def __post_init__(self) -> None:
        if self.source_rgb.ndim != 3 or self.source_rgb.shape[2] != 3:
            raise ValueError("source_rgb must have shape (H, W, 3)")
        if self.analysis_rgb.ndim != 3 or self.analysis_rgb.shape[2] != 3:
            raise ValueError("analysis_rgb must have shape (H, W, 3)")
        analysis_shape = self.analysis_rgb.shape
        h, w = analysis_shape[:2]
        _validate_image_array("source_rgb", self.source_rgb, dtype=np.dtype(np.uint8))
        _validate_image_array("analysis_rgb", self.analysis_rgb, dtype=np.dtype(np.uint8))
        _validate_image_array("structural_rgb", self.structural_rgb, dtype=np.dtype(np.uint8), shape=analysis_shape)
        _validate_image_array("analysis_lab", self.analysis_lab, dtype=np.dtype(np.float32), shape=(h, w, 3))
        _validate_image_array("structural_lab", self.structural_lab, dtype=np.dtype(np.float32), shape=(h, w, 3))
        _validate_image_array("edge_raw", self.edge_raw, dtype=np.dtype(np.float32), shape=(h, w))
        _validate_image_array("edge_structural", self.edge_structural, dtype=np.dtype(np.float32), shape=(h, w))
        for name in ("subject_prob", "subject_confidence", "alpha"):
            value = getattr(self, name)
            if value is not None:
                _validate_image_array(name, value, dtype=np.dtype(np.float32), shape=(h, w))
        if not np.isfinite(self.scale_x) or not np.isfinite(self.scale_y) or self.scale_x <= 0.0 or self.scale_y <= 0.0:
            raise ValueError("scale_x and scale_y must be finite and positive")


@dataclass(frozen=True, slots=True)
class CharacteristicAnchor:
    id: int
    lab: NDArray[np.float64]
    confidence: float

    def __post_init__(self) -> None:
        if self.id < 0:
            raise ValueError("anchor id must be non-negative")
        if self.lab.dtype != np.float64 or self.lab.shape != (3,) or not np.all(np.isfinite(self.lab)):
            raise ValueError("anchor lab must be finite float64 with shape (3,)")
        _validate_confidence("anchor confidence", self.confidence)


@dataclass(frozen=True, slots=True)
class CharacteristicContext:
    anchors: tuple[CharacteristicAnchor, ...]
    anchor_map: NDArray[np.int32] | None = None
    confidence_map: NDArray[np.float32] | None = None

    def __post_init__(self) -> None:
        anchor_ids = tuple(anchor.id for anchor in self.anchors)
        if len(anchor_ids) != len(set(anchor_ids)):
            raise ValueError("characteristic anchor ids must be unique")
        if self.anchor_map is not None and self.anchor_map.dtype != np.int32:
            raise ValueError("anchor_map must have dtype int32")
        if self.confidence_map is not None:
            if self.confidence_map.dtype != np.float32:
                raise ValueError("confidence_map must have dtype float32")
            if self.anchor_map is not None and self.confidence_map.shape != self.anchor_map.shape:
                raise ValueError("anchor_map and confidence_map must have matching shapes")


@dataclass(frozen=True, slots=True)
class CharacteristicSupport:
    anchor_id: int
    support_mass: float
    confidence: float

    def __post_init__(self) -> None:
        if self.anchor_id < 0:
            raise ValueError("anchor_id must be non-negative")
        if not np.isfinite(self.support_mass) or self.support_mass < 0.0:
            raise ValueError("support_mass must be finite and non-negative")
        _validate_confidence("support confidence", self.confidence)


@dataclass(frozen=True, slots=True)
class RegionAnnotation:
    characteristic_supports: tuple[CharacteristicSupport, ...] = ()
    semantic_tag: str | None = None
    semantic_confidence: float = 0.0
    structure_tag: str | None = None
    structure_confidence: float = 0.0

    def __post_init__(self) -> None:
        anchor_ids = tuple(item.anchor_id for item in self.characteristic_supports)
        if len(anchor_ids) != len(set(anchor_ids)):
            raise ValueError("region annotation anchor ids must be unique")
        _validate_confidence("semantic_confidence", self.semantic_confidence)
        if self.semantic_tag is None and self.semantic_confidence != 0.0:
            raise ValueError("semantic_confidence requires semantic_tag")
        _validate_confidence("structure_confidence", self.structure_confidence)
        if self.structure_tag is None and self.structure_confidence != 0.0:
            raise ValueError("structure_confidence requires structure_tag")
