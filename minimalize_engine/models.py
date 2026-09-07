from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
import numpy as np


@dataclass
class PaletteColor:
    id: int
    rgb: tuple[int, int, int]
    lab: tuple[float, float, float]
    pixel_count: int
    ratio: float


@dataclass
class Region:
    id: int
    palette_id: int
    mask: np.ndarray
    area: int
    area_ratio: float
    color_rgb: tuple[int, int, int]
    color_lab: tuple[float, float, float]
    bbox: tuple[int, int, int, int]
    centroid: tuple[float, float]
    contour: np.ndarray | None = None
    area_score: float = 0.0
    contrast_score: float = 0.0
    rarity_score: float = 0.0
    structure_score: float = 0.0
    importance_score: float = 0.0
    is_accent: bool = False
    touches_edge: bool = False
    role: str = "misc"
    composition_layer: str = "midground"
    multiscale_score: float = 0.0
    semantic_type: str = "generic"
    semantic_confidence: float = 0.0
    pattern_group: int | None = None
    character_part_hint: str = "unknown"
    part_confidence: float = 0.0
    side_hint: str = "unknown"


ShapeType = Literal["polygon", "rectangle", "circle", "ellipse", "line"]


@dataclass
class Shape:
    id: int
    shape_type: ShapeType
    fill_color: tuple[int, int, int] | None
    points: list[tuple[float, float]] = field(default_factory=list)
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    cx: float | None = None
    cy: float | None = None
    rx: float | None = None
    ry: float | None = None
    stroke_color: tuple[int, int, int] | None = None
    stroke_width: float = 0.0
    z_index: int = 0
    source_region_id: int | None = None
    importance: float = 0.0
    source_role: str = "misc"
    layer_name: str = "midground"
    semantic_type: str = "generic"
    pattern_group: int | None = None
    character_part: str = "unknown"
    part_confidence: float = 0.0
    side_hint: str = "unknown"


@dataclass
class Scene:
    width: int
    height: int
    background: tuple[int, int, int] | None
    shapes: list[Shape]
    metadata: dict = field(default_factory=dict)
