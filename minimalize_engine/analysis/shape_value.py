from __future__ import annotations

from dataclasses import asdict, dataclass
from math import pi
from typing import Iterable

import cv2
import numpy as np

from ..models import Shape


@dataclass
class ShapeValueDecision:
    shape_id: int
    action: str
    reason: str
    value: float
    area_ratio: float
    importance: float
    contrast: float
    silhouette: float
    uniqueness: float
    connectedness: float
    simplicity: float
    aspect_ratio: float
    semantic_type: str
    character_part: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ShapeValueReport:
    enabled: bool
    before_count: int
    after_count: int
    removed_count: int
    protected_count: int
    mean_value: float
    min_kept_value: float | None
    max_removed_value: float | None
    decisions: list[ShapeValueDecision]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["removal_ratio"] = self.removed_count / self.before_count if self.before_count else 0.0
        return data


_PROTECTED_PREFIXES = (
    "character_hand_", "character_prop", "character_hair", "character_face",
    "character_eye", "character_mouth", "character_shoe",
)
_PROTECTED_EXACT = {"subject_mass", "subject_base", "boat", "building"}
_PROTECTED_TOKENS = ("arm", "leg", "hand", "prop", "hair", "weapon", "accessory", "face", "head", "torso", "body")


def _is_protected(shape: Shape) -> bool:
    sem = (shape.semantic_type or "").lower()
    part = (shape.character_part or "").lower()
    role = (shape.source_role or "").lower()
    if shape.shape_type == "line":
        return True
    if sem in _PROTECTED_EXACT or sem.startswith(_PROTECTED_PREFIXES):
        return True
    if sem.startswith("subject_") or sem == "accent":
        return True
    if any(t in part for t in _PROTECTED_TOKENS):
        return True
    if any(t in role for t in ("hand", "prop", "hair", "limb", "boat", "accent")):
        return True
    return False


def _metrics(shape: Shape) -> tuple[float, float, tuple[float, float, float, float], int]:
    if shape.shape_type == "rectangle":
        w, h = max(float(shape.width or 0), 0), max(float(shape.height or 0), 0)
        x, y = float(shape.x or 0), float(shape.y or 0)
        short, long = sorted((w, h))
        return w * h, long / max(short, 1e-6), (x, y, x + w, y + h), 4
    if shape.shape_type in {"circle", "ellipse"}:
        rx = max(float(shape.rx or 0), 0)
        ry = max(float(shape.ry if shape.ry is not None else rx), 0)
        cx, cy = float(shape.cx or 0), float(shape.cy or 0)
        short, long = sorted((2 * rx, 2 * ry))
        return pi * rx * ry, long / max(short, 1e-6), (cx-rx, cy-ry, cx+rx, cy+ry), 4
    pts = np.asarray(shape.points, dtype=np.float32)
    if len(pts) >= 3:
        area = abs(float(cv2.contourArea(pts)))
        (_, _), (rw, rh), _ = cv2.minAreaRect(pts)
        short, long = sorted((float(rw), float(rh)))
        x0, y0 = np.min(pts, axis=0); x1, y1 = np.max(pts, axis=0)
        return area, long / max(short, 1e-6), (float(x0), float(y0), float(x1), float(y1)), len(pts)
    return 0.0, 999.0, (0.0, 0.0, 0.0, 0.0), len(pts)


def _bbox_overlap(a, b) -> float:
    ax0, ay0, ax1, ay1 = a; bx0, by0, bx1, by1 = b
    ix = max(0.0, min(ax1, bx1) - max(ax0, bx0)); iy = max(0.0, min(ay1, by1) - max(ay0, by0))
    inter = ix * iy
    aa = max(0.0, ax1-ax0) * max(0.0, ay1-ay0)
    ab = max(0.0, bx1-bx0) * max(0.0, by1-by0)
    return inter / max(min(aa, ab), 1e-6)


def _bbox_distance(a, b) -> float:
    ax0, ay0, ax1, ay1 = a; bx0, by0, bx1, by1 = b
    dx = max(0.0, max(ax0, bx0) - min(ax1, bx1)); dy = max(0.0, max(ay0, by0) - min(ay1, by1))
    return float(np.hypot(dx, dy))


def _color_distance(a, b) -> float:
    if a is None or b is None:
        return 255.0
    return float(np.linalg.norm(np.asarray(a, dtype=float)-np.asarray(b, dtype=float)))


def evaluate_global_shape_value(
    shapes: Iterable[Shape],
    canvas_width: int,
    canvas_height: int,
    background: tuple[int, int, int] | None,
    *,
    enable: bool = True,
    min_value: float = 0.400,
    max_remove_area_ratio: float = 0.006,
    max_remove_importance: float = 0.64,
    neighbor_distance_ratio: float = 0.035,
    redundancy_overlap: float = 0.82,
    redundancy_color_distance: float = 16.0,
    near_background_max_color_distance: float = 12.0,
    near_background_max_area_ratio: float = 0.007,
    near_background_max_importance: float = 0.40,
) -> tuple[list[Shape], ShapeValueReport]:
    source = list(shapes)
    if not enable:
        return source, ShapeValueReport(False, len(source), len(source), 0, 0, 0.0, None, None, [])

    canvas_area = max(float(canvas_width * canvas_height), 1.0)
    min_side = max(float(min(canvas_width, canvas_height)), 1.0)
    neighbor_dist = min_side * neighbor_distance_ratio
    met = {s.id: _metrics(s) for s in source}
    protected_count = sum(1 for s in source if _is_protected(s))
    decisions: list[ShapeValueDecision] = []
    removed: set[int] = set()
    values: list[float] = []

    for s in source:
        area, aspect, box, vertices = met[s.id]
        ar = area / canvas_area
        protected = _is_protected(s)

        area_score = float(np.clip(np.sqrt(ar / 0.018), 0.0, 1.0))
        importance = float(np.clip(s.importance, 0.0, 1.0))
        contrast = float(np.clip(_color_distance(s.fill_color, background) / 150.0, 0.0, 1.0)) if background is not None else 0.55

        # A shape touching the canvas/large composition has more silhouette/composition value.
        x0, y0, x1, y1 = box
        edge_touch = x0 <= 1.5 or y0 <= 1.5 or x1 >= canvas_width-1.5 or y1 >= canvas_height-1.5
        silhouette = float(np.clip(0.35 + 0.45 * area_score + (0.20 if edge_touch else 0.0), 0.0, 1.0))

        same_layer = [o for o in source if o.id != s.id and o.layer_name == s.layer_name]
        nearest = min((_bbox_distance(box, met[o.id][2]) for o in same_layer), default=neighbor_dist * 2)
        connectedness = float(np.clip(1.0 - nearest / max(neighbor_dist, 1e-6), 0.0, 1.0))

        redundancy = 0.0
        for o in same_layer:
            if _color_distance(s.fill_color, o.fill_color) > redundancy_color_distance:
                continue
            ov = _bbox_overlap(box, met[o.id][2])
            if ov >= redundancy_overlap:
                redundancy = max(redundancy, ov)
        uniqueness = float(np.clip(1.0 - redundancy, 0.0, 1.0))

        aspect_penalty = float(np.clip((aspect - 5.0) / 8.0, 0.0, 1.0))
        vertex_penalty = float(np.clip((vertices - 7) / 12.0, 0.0, 1.0))
        simplicity = float(np.clip(1.0 - 0.55 * aspect_penalty - 0.45 * vertex_penalty, 0.0, 1.0))

        value = (
            0.23 * area_score + 0.25 * importance + 0.18 * contrast +
            0.12 * silhouette + 0.10 * uniqueness + 0.07 * connectedness + 0.05 * simplicity
        )
        values.append(value)

        removable = (
            not protected and ar <= max_remove_area_ratio and importance <= max_remove_importance
            and value < min_value
        )

        # Small fill-only fragments that are almost the same color as the
        # background are a common quantization/segmentation residue.  They can
        # still receive a middling global score from area or connectedness, so
        # prune them with a dedicated conservative rule.  Edge-touching shapes
        # are excluded because background-colored cutouts at the composition
        # boundary can carry real silhouette/negative-space structure.
        color_distance = _color_distance(s.fill_color, background) if background is not None else 255.0
        has_visible_stroke = s.stroke_color is not None and s.stroke_width > 0
        near_background_fragment = (
            background is not None
            and not protected
            and not edge_touch
            and not has_visible_stroke
            and ar <= near_background_max_area_ratio
            and importance <= near_background_max_importance
            and color_distance <= near_background_max_color_distance
        )
        if near_background_fragment and not removable:
            removable = True
        elif removable:
            # Preserve the original low-value diagnostic when the generic
            # scorer had already decided to prune this shape.
            near_background_fragment = False

        # Keep tiny but high-contrast accents even when the generic importance model underrated them.
        if contrast >= 0.76 and ar >= 0.00012:
            removable = False
            near_background_fragment = False

        action = "remove" if removable else "keep"
        reason = (
            "near_background_fragment" if near_background_fragment
            else "low_global_value" if removable
            else "protected_semantic" if protected
            else "sufficient_value"
        )
        if removable:
            removed.add(s.id)
        decisions.append(ShapeValueDecision(
            s.id, action, reason, float(value), float(ar), importance, contrast,
            silhouette, uniqueness, connectedness, simplicity, float(aspect),
            s.semantic_type, s.character_part,
        ))

    result = [s for s in source if s.id not in removed]
    kept_vals = [d.value for d in decisions if d.action == "keep"]
    removed_vals = [d.value for d in decisions if d.action == "remove"]
    report = ShapeValueReport(
        True, len(source), len(result), len(removed), protected_count,
        float(np.mean(values)) if values else 0.0,
        min(kept_vals) if kept_vals else None,
        max(removed_vals) if removed_vals else None,
        decisions,
    )
    return result, report
