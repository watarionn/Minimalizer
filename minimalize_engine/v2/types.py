from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

RegionId: TypeAlias = int
EdgeKey: TypeAlias = tuple[RegionId, RegionId]
BBox: TypeAlias = tuple[int, int, int, int]
LabelMap: TypeAlias = NDArray[np.int32]


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


@dataclass(frozen=True, slots=True)
class CharacteristicAnchor:
    id: int
    lab: NDArray[np.float64]
    confidence: float


@dataclass(frozen=True, slots=True)
class CharacteristicContext:
    anchors: tuple[CharacteristicAnchor, ...]
    anchor_map: NDArray[np.int32] | None = None
    confidence_map: NDArray[np.float32] | None = None


@dataclass(frozen=True, slots=True)
class CharacteristicSupport:
    anchor_id: int
    support_mass: float
    confidence: float


@dataclass(frozen=True, slots=True)
class RegionAnnotation:
    characteristic_supports: tuple[CharacteristicSupport, ...] = ()
    semantic_tag: str | None = None
    semantic_confidence: float = 0.0
