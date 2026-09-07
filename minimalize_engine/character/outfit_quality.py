from __future__ import annotations

from dataclasses import dataclass, asdict
import cv2
import numpy as np

from ..models import Scene, Shape
from .models import CharacterStructure
from .part_types import CharacterPartType


@dataclass
class OutfitQualityReport:
    score: float | None
    applicable: bool
    source_coverage: float | None
    silhouette_iou: float | None
    structure_score: float | None
    generated_shapes: int
    expected_components: int
    retained_components: int
    retry_reasons: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _draw_shape(mask: np.ndarray, shape: Shape) -> None:
    if shape.shape_type == "polygon" and len(shape.points) >= 3:
        pts = np.asarray(shape.points, dtype=np.float32).round().astype(np.int32)
        cv2.fillPoly(mask, [pts], 255)
    elif shape.shape_type == "rectangle" and None not in {shape.x, shape.y, shape.width, shape.height}:
        cv2.rectangle(mask, (int(round(shape.x)), int(round(shape.y))), (int(round(shape.x + shape.width)), int(round(shape.y + shape.height))), 255, -1)
    elif shape.shape_type in {"circle", "ellipse"} and None not in {shape.cx, shape.cy, shape.rx, shape.ry}:
        cv2.ellipse(mask, (int(round(shape.cx)), int(round(shape.cy))), (max(1, int(round(shape.rx))), max(1, int(round(shape.ry)))), 0, 0, 360, 255, -1)
    elif shape.shape_type == "line" and len(shape.points) >= 2:
        a, b = shape.points[0], shape.points[-1]
        cv2.line(mask, tuple(np.round(a).astype(int)), tuple(np.round(b).astype(int)), 255, max(1, int(round(shape.stroke_width))))


def evaluate_outfit_quality(scene: Scene, structure: CharacterStructure, *, min_score: float = 0.62) -> OutfitQualityReport:
    source_parts = [
        structure.first_part(CharacterPartType.OUTFIT),
        structure.first_part(CharacterPartType.TORSO),
    ]
    source_parts = [p for p in source_parts if p is not None]
    if not source_parts:
        return OutfitQualityReport(None, False, None, None, None, 0, 0, 0, [])

    source = np.zeros_like(structure.subject_mask, dtype=np.uint8)
    for p in source_parts:
        source = cv2.bitwise_or(source, p.mask)

    generated = np.zeros_like(source)
    outfit_shapes = [s for s in scene.shapes if s.character_part == "outfit"]
    for s in outfit_shapes:
        _draw_shape(generated, s)

    src = source > 0
    gen = generated > 0
    inter = int(np.count_nonzero(src & gen))
    union = int(np.count_nonzero(src | gen))
    coverage = inter / max(1, int(np.count_nonzero(src)))
    iou = inter / max(1, union)

    details = scene.metadata.get("character", {}).get("details", {}).get("outfit", {})
    struct = details.get("structure") or {}
    expected = sum(1 for key in ("torso", "left_sleeve", "right_sleeve", "lower", "left_shoe", "right_shoe") if struct.get(key) is not None)
    roles = [s.source_role for s in outfit_shapes]
    retained = 0
    if any(r == "character_outfit_torso" for r in roles): retained += 1
    if any(r == "character_sleeve" and s.side_hint == "left" for r, s in zip(roles, outfit_shapes)): retained += 1
    if any(r == "character_sleeve" and s.side_hint == "right" for r, s in zip(roles, outfit_shapes)): retained += 1
    if any(r.startswith("character_") and r in {"character_skirt_like", "character_coat_like", "character_shorts_like", "character_pants_like"} for r in roles): retained += 1
    retained += sum(1 for side in ("left", "right") if any(s.source_role == "character_shoe" and s.side_hint == side for s in outfit_shapes))
    structure_score = 1.0 if expected <= 0 else min(1.0, retained / expected)

    score = float(np.clip(0.42 * coverage + 0.33 * iou + 0.25 * structure_score, 0.0, 1.0))
    reasons = ["outfit_structure_low"] if score < min_score else []
    return OutfitQualityReport(score, True, float(coverage), float(iou), float(structure_score), len(outfit_shapes), expected, retained, reasons)
