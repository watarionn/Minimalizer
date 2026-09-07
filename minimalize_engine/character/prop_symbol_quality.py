from __future__ import annotations

from dataclasses import dataclass, asdict
import math
import numpy as np

from ..models import Scene, Shape
from .models import CharacterStructure
from .part_types import CharacterPartType


@dataclass
class PropSymbolQualityReport:
    score: float | None
    applicable: bool
    retention: float | None
    compactness: float | None
    placement: float | None
    expected_props: int
    symbol_shapes: int
    retry_reasons: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _shape_center(s: Shape) -> tuple[float, float] | None:
    if s.shape_type in {"circle", "ellipse"} and s.cx is not None and s.cy is not None:
        return float(s.cx), float(s.cy)
    if s.shape_type == "rectangle" and None not in {s.x, s.y, s.width, s.height}:
        return float(s.x + s.width / 2), float(s.y + s.height / 2)
    if s.points:
        xs = [p[0] for p in s.points]
        ys = [p[1] for p in s.points]
        return float(sum(xs) / len(xs)), float(sum(ys) / len(ys))
    return None


def evaluate_prop_symbol_quality(scene: Scene, structure: CharacterStructure, *, min_score: float = 0.68) -> PropSymbolQualityReport:
    expected_parts = structure.get_parts(CharacterPartType.PROP)
    expected = len(expected_parts)
    if expected <= 0:
        return PropSymbolQualityReport(None, False, None, None, None, 0, 0, [])

    shapes = [s for s in scene.shapes if s.character_part == "prop"]
    retention = min(1.0, len(shapes) / expected)
    # Minimalizer should use a small number of symbolic shapes per object.
    per_prop = len(shapes) / max(1, expected)
    compactness = float(np.clip(1.0 - max(0.0, per_prop - 2.0) * 0.24, 0.0, 1.0))

    sx, sy, sw, sh = structure.subject_bbox
    scale = max(1.0, math.hypot(sw, sh))
    shape_centers = [c for c in (_shape_center(s) for s in shapes) if c is not None]
    placement_scores = []
    for p in expected_parts:
        if not shape_centers:
            placement_scores.append(0.0)
            continue
        d = min(math.hypot(c[0] - p.centroid[0], c[1] - p.centroid[1]) for c in shape_centers)
        placement_scores.append(float(np.clip(1.0 - d / (scale * 0.28), 0.0, 1.0)))
    placement = float(sum(placement_scores) / max(1, len(placement_scores)))
    score = float(np.clip(0.48 * retention + 0.20 * compactness + 0.32 * placement, 0.0, 1.0))
    reasons = ["prop_symbolization_low"] if score < min_score else []
    return PropSymbolQualityReport(score, True, float(retention), compactness, placement, expected, len(shapes), reasons)
