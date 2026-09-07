from __future__ import annotations

from dataclasses import dataclass, asdict, replace
from math import pi
from typing import Iterable

import cv2
import numpy as np

from ..models import Shape


@dataclass
class ShapeCleanupDecision:
    shape_id: int
    action: str
    reason: str
    shape_type: str
    semantic_type: str
    character_part: str
    area: float
    short_side: float
    long_side: float
    aspect_ratio: float
    area_ratio: float
    importance: float
    related_shape_id: int | None = None
    before_vertices: int | None = None
    after_vertices: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ShapeCleanupReport:
    enabled: bool
    before_count: int
    after_count: int
    removed_count: int
    removed_thin: int
    removed_micro: int
    removed_duplicate: int
    removed_isolated: int
    merged_count: int
    role_fragment_merged_count: int
    simplified_count: int
    vertices_before: int
    vertices_after: int
    protected_count: int
    decisions: list[ShapeCleanupDecision]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["removal_ratio"] = (
            self.removed_count / self.before_count if self.before_count else 0.0
        )
        data["vertex_reduction"] = max(0, self.vertices_before - self.vertices_after)
        data["vertex_reduction_ratio"] = (
            data["vertex_reduction"] / self.vertices_before if self.vertices_before else 0.0
        )
        return data


_PROTECTED_PREFIXES = (
    "character_hand_",
    "character_prop",
    "character_hair",
    "character_face",
    "character_eye",
    "character_mouth",
    "character_shoe",
)
_PROTECTED_EXACT = {
    "subject_mass",
    "subject_base",
    "boat",
    "building",
}
_PROTECTED_PART_TOKENS = (
    "arm",
    "leg",
    "hand",
    "prop",
    "hair",
    "weapon",
    "accessory",
)


def _is_protected(shape: Shape) -> bool:
    sem = (shape.semantic_type or "").lower()
    part = (shape.character_part or "").lower()
    role = (shape.source_role or "").lower()
    if sem in _PROTECTED_EXACT or sem.startswith(_PROTECTED_PREFIXES):
        return True
    if any(token in part for token in _PROTECTED_PART_TOKENS):
        return True
    if any(token in role for token in ("hand", "prop", "hair", "limb", "boat")):
        return True
    # Lines are intentionally thin. Their density is controlled by line_mode.
    if shape.shape_type == "line":
        return True
    return False


def _geometry_metrics(shape: Shape) -> tuple[float, float, float, float, tuple[float, float, float, float]]:
    """Return area, short side, long side, aspect ratio, bbox."""
    if shape.shape_type == "rectangle":
        w = max(float(shape.width or 0.0), 0.0)
        h = max(float(shape.height or 0.0), 0.0)
        x = float(shape.x or 0.0)
        y = float(shape.y or 0.0)
        short, long = sorted((w, h))
        area = w * h
        return area, short, long, long / max(short, 1e-6), (x, y, x + w, y + h)

    if shape.shape_type in {"circle", "ellipse"}:
        rx = float(shape.rx or 0.0)
        ry = float(shape.ry if shape.ry is not None else rx)
        cx = float(shape.cx or 0.0)
        cy = float(shape.cy or 0.0)
        short, long = sorted((2 * rx, 2 * ry))
        area = pi * rx * ry
        return area, short, long, long / max(short, 1e-6), (cx - rx, cy - ry, cx + rx, cy + ry)

    pts = np.asarray(shape.points, dtype=np.float32)
    if len(pts) >= 3:
        area = float(abs(cv2.contourArea(pts)))
        (_, _), (rw, rh), _ = cv2.minAreaRect(pts)
        short, long = sorted((float(rw), float(rh)))
        x0, y0 = np.min(pts, axis=0)
        x1, y1 = np.max(pts, axis=0)
        return area, short, long, long / max(short, 1e-6), (float(x0), float(y0), float(x1), float(y1))
    if len(pts) == 2:
        x0, y0 = np.min(pts, axis=0)
        x1, y1 = np.max(pts, axis=0)
        long = float(np.hypot(x1 - x0, y1 - y0))
        return 0.0, 0.0, long, 1e9, (float(x0), float(y0), float(x1), float(y1))
    return 0.0, 0.0, 0.0, 1.0, (0.0, 0.0, 0.0, 0.0)


def _bbox_overlap_fraction(a, b) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    iy = max(0.0, min(ay1, by1) - max(ay0, by0))
    inter = ix * iy
    aa = max(0.0, ax1 - ax0) * max(0.0, ay1 - ay0)
    ab = max(0.0, bx1 - bx0) * max(0.0, by1 - by0)
    return inter / max(min(aa, ab), 1e-6)


def _bbox_distance(a, b) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0.0, max(ax0, bx0) - min(ax1, bx1))
    dy = max(0.0, max(ay0, by0) - min(ay1, by1))
    return float(np.hypot(dx, dy))


def _color_distance(a: tuple[int, int, int] | None, b: tuple[int, int, int] | None) -> float:
    if a is None or b is None:
        return 999.0
    return float(np.linalg.norm(np.asarray(a, dtype=float) - np.asarray(b, dtype=float)))


def _vertex_count(shape: Shape) -> int:
    if shape.shape_type == "polygon":
        return len(shape.points)
    if shape.shape_type == "rectangle":
        return 4
    if shape.shape_type in {"circle", "ellipse"}:
        return 4
    if shape.shape_type == "line":
        return len(shape.points) if shape.points else 2
    return len(shape.points)


def _shape_polygon(shape: Shape) -> np.ndarray | None:
    if shape.shape_type == "polygon" and len(shape.points) >= 3:
        return np.asarray(shape.points, dtype=np.float32)
    if shape.shape_type == "rectangle":
        x, y = float(shape.x or 0), float(shape.y or 0)
        w, h = float(shape.width or 0), float(shape.height or 0)
        return np.asarray([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], dtype=np.float32)
    return None


def _polygon_local_iou(a: np.ndarray, b: np.ndarray, scale: int = 3) -> float:
    """Raster IoU in a tight local box, used only as a cleanup safety gate."""
    both = np.vstack([a.reshape(-1, 2), b.reshape(-1, 2)]).astype(np.float32)
    x0, y0 = np.floor(np.min(both, axis=0) - 2).astype(int)
    x1, y1 = np.ceil(np.max(both, axis=0) + 2).astype(int)
    w, h = max(1, x1 - x0 + 1), max(1, y1 - y0 + 1)
    ma = np.zeros((h * scale, w * scale), dtype=np.uint8)
    mb = np.zeros_like(ma)
    aa = np.rint((a.reshape(-1, 2) - (x0, y0)) * scale).astype(np.int32)
    bb = np.rint((b.reshape(-1, 2) - (x0, y0)) * scale).astype(np.int32)
    cv2.fillPoly(ma, [aa], 1)
    cv2.fillPoly(mb, [bb], 1)
    union = np.count_nonzero(ma | mb)
    return 1.0 if union == 0 else float(np.count_nonzero(ma & mb) / union)


def _try_simplify_polygon(
    shape: Shape,
    epsilon_ratio: float,
    max_area_error: float,
    min_iou: float = 0.985,
) -> Shape | None:
    """Adaptively reduce generic polygon vertices without changing its silhouette.

    Search from aggressive to conservative epsilon values and accept the first
    candidate that passes both area and local raster-IoU gates. Protected
    semantic/character geometry remains untouched.
    """
    if shape.shape_type != "polygon" or len(shape.points) < 7 or _is_protected(shape):
        return None
    pts = np.asarray(shape.points, dtype=np.float32)
    peri = float(cv2.arcLength(pts, True))
    area0 = abs(float(cv2.contourArea(pts)))
    if peri <= 0 or area0 <= 1e-6:
        return None

    for factor in (1.75, 1.40, 1.15, 1.00, 0.80, 0.60, 0.45):
        approx = cv2.approxPolyDP(
            pts, max(0.35, peri * epsilon_ratio * factor), True
        ).reshape(-1, 2)
        if len(approx) < 3 or len(approx) > len(pts) - 2:
            continue
        area1 = abs(float(cv2.contourArea(approx)))
        if abs(area1 - area0) / area0 > max_area_error:
            continue
        if _polygon_local_iou(pts, approx) < min_iou:
            continue
        return replace(shape, points=[(float(x), float(y)) for x, y in approx])
    return None



def _primitive_fit_iou(points: np.ndarray, kind: str, scale: int = 4) -> tuple[float, tuple[float, ...] | None]:
    """Compare a polygon with an axis-aligned primitive using a local mask.

    Exporters only support axis-aligned rectangles/ellipses, so this deliberately
    scores the exact geometry Minimalizer would emit instead of a rotated fit.
    """
    if points is None or len(points) < 3:
        return 0.0, None
    pts = np.asarray(points, dtype=np.float32).reshape(-1, 2)
    x0, y0 = np.min(pts, axis=0)
    x1, y1 = np.max(pts, axis=0)
    w, h = float(x1 - x0), float(y1 - y0)
    if w <= 0.5 or h <= 0.5:
        return 0.0, None

    pad = 2.0
    ox, oy = float(x0 - pad), float(y0 - pad)
    mw = max(4, int(np.ceil((w + 2 * pad) * scale)) + 2)
    mh = max(4, int(np.ceil((h + 2 * pad) * scale)) + 2)
    original = np.zeros((mh, mw), dtype=np.uint8)
    candidate = np.zeros_like(original)
    local = np.round((pts - np.asarray([ox, oy], dtype=np.float32)) * scale).astype(np.int32)
    cv2.fillPoly(original, [local], 255)

    if kind == "rectangle":
        a = (int(round((x0 - ox) * scale)), int(round((y0 - oy) * scale)))
        b = (int(round((x1 - ox) * scale)), int(round((y1 - oy) * scale)))
        cv2.rectangle(candidate, a, b, 255, -1)
        params = (float(x0), float(y0), w, h)
    elif kind == "ellipse":
        cx, cy = float((x0 + x1) / 2), float((y0 + y1) / 2)
        rx, ry = w / 2.0, h / 2.0
        center = (int(round((cx - ox) * scale)), int(round((cy - oy) * scale)))
        axes = (max(1, int(round(rx * scale))), max(1, int(round(ry * scale))))
        cv2.ellipse(candidate, center, axes, 0, 0, 360, 255, -1)
        params = (cx, cy, rx, ry)
    else:
        return 0.0, None

    aa, bb = original > 0, candidate > 0
    union = int(np.count_nonzero(aa | bb))
    if union == 0:
        return 0.0, None
    return float(np.count_nonzero(aa & bb) / union), params


def _try_promote_polygon_primitive(
    shape: Shape,
    rectangle_iou: float,
    ellipse_iou: float,
    max_area: float,
) -> tuple[Shape | None, str | None, float]:
    if shape.shape_type != "polygon" or len(shape.points) < 4 or _is_protected(shape):
        return None, None, 0.0
    if shape.stroke_width > 0 or shape.fill_color is None:
        return None, None, 0.0
    area = _geometry_metrics(shape)[0]
    if area <= 1e-6 or area > max_area:
        return None, None, 0.0

    pts = np.asarray(shape.points, dtype=np.float32)
    rect_score, rect = _primitive_fit_iou(pts, "rectangle")
    ell_score, ell = _primitive_fit_iou(pts, "ellipse") if len(pts) >= 5 else (0.0, None)

    # Prefer the simpler rectangle if it clears its stricter threshold and is
    # not materially worse than the ellipse. Otherwise use an axis-aligned
    # ellipse only when its exported geometry is an excellent match.
    if rect is not None and rect_score >= rectangle_iou and rect_score + 0.01 >= ell_score:
        x, y, w, h = rect
        return replace(shape, shape_type="rectangle", points=[], x=x, y=y, width=w, height=h,
                       cx=None, cy=None, rx=None, ry=None), "polygon_to_rectangle", rect_score
    if ell is not None and ell_score >= ellipse_iou:
        cx, cy, rx, ry = ell
        return replace(shape, shape_type="ellipse", points=[], x=None, y=None, width=None, height=None,
                       cx=cx, cy=cy, rx=rx, ry=ry), "polygon_to_ellipse", ell_score
    return None, None, max(rect_score, ell_score)

def _try_merge_pair(a: Shape, b: Shape, max_gap: float, color_distance: float, max_hull_inflation: float) -> Shape | None:
    if _is_protected(a) or _is_protected(b):
        return None
    if a.fill_color is None or b.fill_color is None or a.layer_name != b.layer_name:
        return None
    if _color_distance(a.fill_color, b.fill_color) > color_distance:
        return None
    pa, pb = _shape_polygon(a), _shape_polygon(b)
    if pa is None or pb is None:
        return None
    ma, mb = _geometry_metrics(a), _geometry_metrics(b)
    if _bbox_distance(ma[4], mb[4]) > max_gap:
        return None
    area_sum = ma[0] + mb[0]
    if area_sum <= 1e-6:
        return None
    hull = cv2.convexHull(np.vstack([pa, pb])).reshape(-1, 2)
    hull_area = abs(float(cv2.contourArea(hull)))
    if hull_area / area_sum > max_hull_inflation:
        return None
    # Keep the stronger semantic carrier; only geometry/color become the union.
    keep = a if (a.importance, ma[0]) >= (b.importance, mb[0]) else b
    rgb = tuple(int(round((x + y) / 2)) for x, y in zip(a.fill_color, b.fill_color))
    return replace(
        keep,
        shape_type="polygon",
        fill_color=rgb,
        points=[(float(x), float(y)) for x, y in hull],
        x=None, y=None, width=None, height=None,
        cx=None, cy=None, rx=None, ry=None,
        importance=max(float(a.importance), float(b.importance)),
    )



def _union_polygon_outline(a: Shape, b: Shape, scale: int = 4) -> np.ndarray | None:
    """Raster-union two fill polygons locally and return one outer contour.

    The local high-resolution mask avoids convex-hull whitespace bridging. If
    the shapes remain disconnected, no merge is produced.
    """
    pa, pb = _shape_polygon(a), _shape_polygon(b)
    if pa is None or pb is None:
        return None
    pts = np.vstack([pa, pb])
    x0, y0 = np.floor(np.min(pts, axis=0) - 2.0).astype(int)
    x1, y1 = np.ceil(np.max(pts, axis=0) + 2.0).astype(int)
    w = max(1, (x1 - x0 + 1) * scale)
    h = max(1, (y1 - y0 + 1) * scale)
    mask = np.zeros((h, w), dtype=np.uint8)
    for poly in (pa, pb):
        local = np.round((poly - np.asarray([x0, y0], dtype=np.float32)) * scale).astype(np.int32)
        cv2.fillPoly(mask, [local], 255)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if abs(float(cv2.contourArea(c))) > 0.5]
    if len(contours) != 1:
        return None
    contour = contours[0].reshape(-1, 2).astype(np.float32) / float(scale)
    contour += np.asarray([x0, y0], dtype=np.float32)
    if len(contour) < 3:
        return None
    return contour


def _try_role_fragment_merge(
    a: Shape,
    b: Shape,
    max_gap: float,
    color_distance: float,
    max_fragment_area: float,
    max_combined_area: float,
    max_hull_inflation: float,
) -> Shape | None:
    """Absorb a tiny touching fragment into a same-role nearby fill.

    Unlike the generic adjacent merge, this pass can merge into a larger
    carrier. It requires matching role/layer/part metadata and uses a local
    raster union so concavities are preserved instead of replaced by a hull.
    """
    if _is_protected(a) or _is_protected(b):
        return None
    if a.fill_color is None or b.fill_color is None:
        return None
    if a.stroke_width > 0 or b.stroke_width > 0:
        return None
    if a.layer_name != b.layer_name:
        return None
    if (a.source_role or "misc") != (b.source_role or "misc"):
        return None
    if (a.character_part or "unknown") != (b.character_part or "unknown"):
        return None
    if a.pattern_group != b.pattern_group:
        return None
    if _color_distance(a.fill_color, b.fill_color) > color_distance:
        return None

    ma, mb = _geometry_metrics(a), _geometry_metrics(b)
    if min(ma[0], mb[0]) > max_fragment_area:
        return None
    area_sum = ma[0] + mb[0]
    if area_sum <= 1e-6 or area_sum > max_combined_area:
        return None
    if _bbox_distance(ma[4], mb[4]) > max_gap:
        return None

    union = _union_polygon_outline(a, b)
    if union is None:
        return None
    union_area = abs(float(cv2.contourArea(union)))
    # Parameter name retained for config compatibility; here it limits actual
    # union-area change rather than convex-hull inflation.
    if union_area / area_sum > max_hull_inflation:
        return None
    if union_area / area_sum < 0.94:
        return None

    keep = a if (a.importance, ma[0]) >= (b.importance, mb[0]) else b
    rgb = tuple(int(round((x + y) / 2)) for x, y in zip(a.fill_color, b.fill_color))
    return replace(
        keep,
        shape_type="polygon",
        fill_color=rgb,
        points=[(float(x), float(y)) for x, y in union],
        x=None, y=None, width=None, height=None,
        cx=None, cy=None, rx=None, ry=None,
        importance=max(float(a.importance), float(b.importance)),
    )

def cleanup_minimal_shapes(
    shapes: Iterable[Shape],
    canvas_width: int,
    canvas_height: int,
    *,
    enable: bool = True,
    thin_aspect_ratio: float = 8.0,
    thin_short_side_ratio: float = 0.022,
    thin_max_area_ratio: float = 0.0045,
    thin_rectangle_short_side_ratio: float = 0.012,
    thin_rectangle_aspect_ratio: float = 4.5,
    thin_rectangle_max_area_ratio: float = 0.0060,
    thin_rectangle_max_importance: float = 0.97,
    micro_area_ratio: float = 0.00016,
    micro_max_importance: float = 0.52,
    remove_duplicates: bool = False,
    duplicate_overlap: float = 0.97,
    duplicate_color_distance: float = 4.0,
    merge_adjacent: bool = True,
    merge_gap_ratio: float = 0.008,
    merge_color_distance: float = 7.0,
    merge_max_area_ratio: float = 0.018,
    merge_max_hull_inflation: float = 1.08,
    role_fragment_merge: bool = False,
    role_fragment_gap_ratio: float = 0.002,
    role_fragment_color_distance: float = 3.0,
    role_fragment_max_area_ratio: float = 0.010,
    role_fragment_max_combined_area_ratio: float = 0.080,
    role_fragment_max_hull_inflation: float = 1.070,
    simplify_polygons: bool = True,
    simplify_epsilon_ratio: float = 0.012,
    simplify_max_area_error: float = 0.045,
    simplify_min_iou: float = 0.985,
    promote_primitives: bool = True,
    promote_rectangle_iou: float = 0.955,
    promote_ellipse_iou: float = 0.945,
    promote_max_area_ratio: float = 0.080,
    remove_isolated: bool = True,
    isolated_max_area_ratio: float = 0.0008,
    isolated_min_distance_ratio: float = 0.075,
    isolated_max_importance: float = 0.38,
) -> tuple[list[Shape], ShapeCleanupReport]:
    source = list(shapes)
    vertices_before = sum(_vertex_count(s) for s in source)
    if not enable:
        return source, ShapeCleanupReport(
            False, len(source), len(source), 0, 0, 0, 0, 0, 0, 0, 0,
            vertices_before, vertices_before, 0, [],
        )

    canvas_area = max(float(canvas_width * canvas_height), 1.0)
    min_side = max(float(min(canvas_width, canvas_height)), 1.0)
    thin_short_side = max(1.6, min_side * thin_short_side_ratio)
    thin_rectangle_short_side = max(1.35, min_side * thin_rectangle_short_side_ratio)
    merge_gap = max(0.75, min_side * merge_gap_ratio)
    role_fragment_gap = max(0.50, min_side * role_fragment_gap_ratio)
    isolated_min_distance = min_side * isolated_min_distance_ratio

    metrics = {s.id: _geometry_metrics(s) for s in source}
    removed: set[int] = set()
    decisions: list[ShapeCleanupDecision] = []
    protected_count = 0
    removed_thin = 0
    removed_micro = 0
    removed_duplicate = 0
    removed_isolated = 0
    merged_count = 0
    role_fragment_merged_count = 0
    simplified_count = 0

    # Pass 1: reject low-value slivers and tiny fragments conservatively.
    for s in source:
        area, short, long, aspect, _ = metrics[s.id]
        area_ratio = area / canvas_area
        protected = _is_protected(s)
        if protected:
            protected_count += 1
            continue

        is_thin = (
            short <= thin_short_side
            and aspect >= thin_aspect_ratio
            and area_ratio <= thin_max_area_ratio
            and s.importance < 0.90
        )
        # Rectangles produced from quantized fragments can survive the generic
        # sliver rule when they are only moderately elongated. In a minimal
        # rendering these needle-like bars usually read as segmentation noise,
        # so give rectangles a stricter short-side rule while preserving all
        # semantic/character-protected geometry above.
        is_thin_rectangle = (
            s.shape_type == "rectangle"
            and short <= thin_rectangle_short_side
            and aspect >= thin_rectangle_aspect_ratio
            and area_ratio <= thin_rectangle_max_area_ratio
            and s.importance < thin_rectangle_max_importance
        )
        is_micro = (
            area_ratio <= micro_area_ratio
            and s.importance <= micro_max_importance
            and s.shape_type != "line"
        )
        if is_thin or is_thin_rectangle or is_micro:
            reason = "thin_rectangle" if is_thin_rectangle and not is_thin else "thin_sliver" if is_thin else "micro_fragment"
            removed.add(s.id)
            if is_thin or is_thin_rectangle:
                removed_thin += 1
            else:
                removed_micro += 1
            decisions.append(ShapeCleanupDecision(
                s.id, "remove", reason, s.shape_type, s.semantic_type,
                s.character_part, area, short, long, aspect, area_ratio,
                float(s.importance),
            ))

    # Pass 2: remove near-duplicate same-color fills. Off by default because
    # meaningful layered overlaps can look duplicate in bbox space.
    survivors = [s for s in source if s.id not in removed]
    if remove_duplicates:
        for i, a in enumerate(survivors):
            if a.id in removed or _is_protected(a) or a.fill_color is None:
                continue
            aa, _, _, _, abox = metrics[a.id]
            for b in survivors[i + 1:]:
                if b.id in removed or _is_protected(b) or b.fill_color is None:
                    continue
                if a.layer_name != b.layer_name:
                    continue
                if _color_distance(a.fill_color, b.fill_color) > duplicate_color_distance:
                    continue
                ba, _, _, _, bbox = metrics[b.id]
                if _bbox_overlap_fraction(abox, bbox) < duplicate_overlap:
                    continue
                score_a = aa * (0.75 + 0.25 * max(0.0, a.importance))
                score_b = ba * (0.75 + 0.25 * max(0.0, b.importance))
                loser = b if score_a >= score_b else a
                la, lsh, llo, lasp, _ = metrics[loser.id]
                removed.add(loser.id)
                removed_duplicate += 1
                decisions.append(ShapeCleanupDecision(
                    loser.id, "remove", "near_duplicate", loser.shape_type,
                    loser.semantic_type, loser.character_part, la, lsh, llo,
                    lasp, la / canvas_area, float(loser.importance),
                ))
                if loser is a:
                    break

    # Pass 3: remove tiny low-value fragments that are spatially isolated.
    if remove_isolated:
        live = [s for s in source if s.id not in removed]
        live_metrics = {s.id: metrics[s.id] for s in live}
        for s in live:
            if _is_protected(s) or s.importance > isolated_max_importance:
                continue
            area, short, long, aspect, box = live_metrics[s.id]
            if area / canvas_area > isolated_max_area_ratio:
                continue
            distances = [
                _bbox_distance(box, live_metrics[o.id][4])
                for o in live if o.id != s.id and o.layer_name == s.layer_name
            ]
            if distances and min(distances) >= isolated_min_distance:
                removed.add(s.id)
                removed_isolated += 1
                decisions.append(ShapeCleanupDecision(
                    s.id, "remove", "isolated_fragment", s.shape_type,
                    s.semantic_type, s.character_part, area, short, long,
                    aspect, area / canvas_area, float(s.importance),
                ))

    # Pass 4: merge directly adjacent, nearly same-color small generic fills.
    # Convex-hull inflation is capped tightly to avoid bridging real whitespace.
    working = [s for s in source if s.id not in removed]
    if merge_adjacent:
        changed = True
        while changed:
            changed = False
            for i, a in enumerate(working):
                ma = _geometry_metrics(a)
                if ma[0] / canvas_area > merge_max_area_ratio:
                    continue
                for j in range(i + 1, len(working)):
                    b = working[j]
                    mb = _geometry_metrics(b)
                    if mb[0] / canvas_area > merge_max_area_ratio:
                        continue
                    merged = _try_merge_pair(
                        a, b, merge_gap, merge_color_distance, merge_max_hull_inflation
                    )
                    if merged is None:
                        continue
                    loser = b if merged.id == a.id else a
                    winner = a if merged.id == a.id else b
                    wmetrics = _geometry_metrics(winner)
                    decisions.append(ShapeCleanupDecision(
                        loser.id, "merge", "adjacent_same_color", loser.shape_type,
                        loser.semantic_type, loser.character_part, mb[0] if loser is b else ma[0],
                        mb[1] if loser is b else ma[1], mb[2] if loser is b else ma[2],
                        mb[3] if loser is b else ma[3],
                        (mb[0] if loser is b else ma[0]) / canvas_area,
                        float(loser.importance), related_shape_id=winner.id,
                    ))
                    merged_count += 1
                    # Preserve original z-order position of the earlier pair member.
                    new_working = working[:i] + [merged] + working[i + 1:j] + working[j + 1:]
                    working = new_working
                    changed = True
                    break
                if changed:
                    break


    # Pass 5: absorb a tiny touching fragment into a same-role fill.
    # This may absorb a fragment into a larger carrier, unlike Pass 4, but only
    # under strict role/color/contact and hull-inflation agreement.
    if role_fragment_merge:
        changed = True
        while changed:
            changed = False
            for i, a in enumerate(working):
                ma = _geometry_metrics(a)
                for j in range(i + 1, len(working)):
                    b = working[j]
                    mb = _geometry_metrics(b)
                    merged = _try_role_fragment_merge(
                        a, b, role_fragment_gap, role_fragment_color_distance,
                        canvas_area * role_fragment_max_area_ratio,
                        canvas_area * role_fragment_max_combined_area_ratio,
                        role_fragment_max_hull_inflation,
                    )
                    if merged is None:
                        continue
                    loser = b if merged.id == a.id else a
                    winner = a if merged.id == a.id else b
                    lm = mb if loser is b else ma
                    decisions.append(ShapeCleanupDecision(
                        loser.id, "merge", "role_touching_fragment", loser.shape_type,
                        loser.semantic_type, loser.character_part, lm[0], lm[1], lm[2],
                        lm[3], lm[0] / canvas_area, float(loser.importance),
                        related_shape_id=winner.id,
                    ))
                    merged_count += 1
                    role_fragment_merged_count += 1
                    working = working[:i] + [merged] + working[i + 1:j] + working[j + 1:]
                    changed = True
                    break
                if changed:
                    break

    # Pass 6: reduce jagged generic polygons only when area is essentially kept.
    if simplify_polygons:
        simplified: list[Shape] = []
        for s in working:
            replacement = _try_simplify_polygon(s, simplify_epsilon_ratio, simplify_max_area_error, simplify_min_iou)
            if replacement is not None:
                m = _geometry_metrics(s)
                decisions.append(ShapeCleanupDecision(
                    s.id, "simplify", "polygon_vertex_reduction", s.shape_type,
                    s.semantic_type, s.character_part, m[0], m[1], m[2], m[3],
                    m[0] / canvas_area, float(s.importance),
                    before_vertices=len(s.points), after_vertices=len(replacement.points),
                ))
                simplified_count += 1
                simplified.append(replacement)
            else:
                simplified.append(s)
        working = simplified

    # Pass 7: after merging/simplification, re-check generic polygons for a
    # simpler exported primitive. This second chance catches geometry that only
    # became rectangle/ellipse-like after the cleanup passes above.
    if promote_primitives:
        promoted: list[Shape] = []
        for s in working:
            replacement, reason, score = _try_promote_polygon_primitive(
                s, promote_rectangle_iou, promote_ellipse_iou,
                canvas_area * promote_max_area_ratio,
            )
            if replacement is not None and reason is not None:
                m = _geometry_metrics(s)
                decisions.append(ShapeCleanupDecision(
                    s.id, "promote", reason, s.shape_type, s.semantic_type,
                    s.character_part, m[0], m[1], m[2], m[3], m[0] / canvas_area,
                    float(s.importance), before_vertices=len(s.points),
                    after_vertices=_vertex_count(replacement),
                ))
                promoted.append(replacement)
            else:
                promoted.append(s)
        working = promoted

    result = working
    vertices_after = sum(_vertex_count(s) for s in result)
    removed_count = len(source) - len(result)
    report = ShapeCleanupReport(
        True,
        len(source),
        len(result),
        removed_count,
        removed_thin,
        removed_micro,
        removed_duplicate,
        removed_isolated,
        merged_count,
        role_fragment_merged_count,
        simplified_count,
        vertices_before,
        vertices_after,
        protected_count,
        decisions,
    )
    return result, report
