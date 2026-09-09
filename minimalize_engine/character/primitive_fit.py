from __future__ import annotations

from dataclasses import dataclass
import math

import cv2
import numpy as np


@dataclass
class PrimitiveFit:
    kind: str
    shape_type: str
    score: float
    iou: float
    recall: float
    precision: float
    complexity: int
    points: list[tuple[float, float]] | None = None
    cx: float | None = None
    cy: float | None = None
    rx: float | None = None
    ry: float | None = None

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "shape_type": self.shape_type,
            "score": round(float(self.score), 6),
            "iou": round(float(self.iou), 6),
            "recall": round(float(self.recall), 6),
            "precision": round(float(self.precision), 6),
            "complexity": self.complexity,
        }


def _largest_contour(mask: np.ndarray) -> np.ndarray | None:
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    return max(contours, key=cv2.contourArea)


def _polygon_mask(shape: tuple[int, int], points: np.ndarray) -> np.ndarray:
    canvas = np.zeros(shape, dtype=np.uint8)
    if len(points) >= 3:
        cv2.fillPoly(canvas, [np.round(points).astype(np.int32)], 1)
    return canvas


def _ellipse_mask(shape: tuple[int, int], cx: float, cy: float, rx: float, ry: float, angle: float = 0.0) -> np.ndarray:
    canvas = np.zeros(shape, dtype=np.uint8)
    cv2.ellipse(
        canvas,
        (int(round(cx)), int(round(cy))),
        (max(1, int(round(rx))), max(1, int(round(ry)))),
        float(angle),
        0,
        360,
        1,
        -1,
    )
    return canvas


def _metrics(target: np.ndarray, candidate: np.ndarray, complexity: int) -> tuple[float, float, float, float]:
    a = target > 0
    b = candidate > 0
    intersection = float(np.logical_and(a, b).sum())
    union = float(np.logical_or(a, b).sum())
    target_area = max(float(a.sum()), 1.0)
    candidate_area = max(float(b.sum()), 1.0)
    iou = intersection / max(union, 1.0)
    recall = intersection / target_area
    precision = intersection / candidate_area

    ay, ax = np.where(a)
    by, bx = np.where(b)
    if len(ax) and len(bx):
        diagonal = max(math.hypot(*target.shape), 1.0)
        distance = math.hypot(float(ax.mean() - bx.mean()), float(ay.mean() - by.mean())) / diagonal
        centroid_score = max(0.0, 1.0 - distance * 5.0)
    else:
        centroid_score = 0.0
    simplicity = max(0.0, 1.0 - max(complexity - 4, 0) / 8.0)
    score = 0.58 * iou + 0.16 * recall + 0.10 * precision + 0.09 * centroid_score + 0.07 * simplicity
    return score, iou, recall, precision


def _polygon_candidates(contour: np.ndarray, max_vertices: tuple[int, ...]) -> list[tuple[str, np.ndarray]]:
    perimeter = max(float(cv2.arcLength(contour, True)), 1.0)
    candidates: list[tuple[str, np.ndarray]] = []
    seen: set[tuple[tuple[int, int], ...]] = set()
    for vertex_limit in max_vertices:
        epsilon = perimeter * 0.008
        best = contour.reshape(-1, 2)
        while epsilon <= perimeter * 0.18:
            approx = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
            if 3 <= len(approx) <= vertex_limit:
                best = approx
                break
            epsilon *= 1.28
        if not 3 <= len(best) <= vertex_limit:
            continue
        key = tuple((int(x), int(y)) for x, y in best)
        if key in seen:
            continue
        seen.add(key)
        candidates.append((f"polygon_{len(best)}", best.astype(np.float32)))
    return candidates


def _trapezoid_candidates(mask: np.ndarray) -> list[tuple[str, np.ndarray]]:
    ys, xs = np.where(mask > 0)
    if len(xs) < 4:
        return []
    x0, x1 = float(xs.min()), float(xs.max())
    y0, y1 = float(ys.min()), float(ys.max())
    height = max(y1 - y0, 1.0)
    width = max(x1 - x0, 1.0)

    top = (ys <= y0 + height * 0.30)
    bottom = (ys >= y0 + height * 0.70)
    top_cx = float(xs[top].mean()) if np.any(top) else float(xs.mean())
    bottom_cx = float(xs[bottom].mean()) if np.any(bottom) else float(xs.mean())
    candidates = []
    for top_scale, bottom_scale in ((0.55, 0.95), (0.70, 1.00), (0.82, 1.00), (0.95, 0.75), (1.00, 0.88)):
        tw = width * top_scale
        bw = width * bottom_scale
        pts = np.asarray([
            [top_cx - tw * 0.5, y0],
            [top_cx + tw * 0.5, y0],
            [bottom_cx + bw * 0.5, y1],
            [bottom_cx - bw * 0.5, y1],
        ], dtype=np.float32)
        candidates.append((f"trapezoid_{top_scale:.2f}_{bottom_scale:.2f}", pts))
    return candidates


def _rotated_rect_candidate(contour: np.ndarray) -> tuple[str, np.ndarray] | None:
    if len(contour) < 3:
        return None
    rect = cv2.minAreaRect(contour)
    return "rotated_rect", cv2.boxPoints(rect).astype(np.float32)


def _triangle_candidate(contour: np.ndarray) -> tuple[str, np.ndarray] | None:
    if len(contour) < 3:
        return None
    _, triangle = cv2.minEnclosingTriangle(contour)
    if triangle is None:
        return None
    return "triangle", triangle.reshape(-1, 2).astype(np.float32)


def fit_best_primitive(
    mask: np.ndarray,
    *,
    allowed: tuple[str, ...] = ("polygon",),
    polygon_vertices: tuple[int, ...] = (4, 5, 6, 8),
) -> PrimitiveFit | None:
    target = (mask > 0).astype(np.uint8)
    contour = _largest_contour(target)
    if contour is None or cv2.contourArea(contour) < 3.0:
        return None

    candidates: list[tuple[str, str, np.ndarray | tuple[float, float, float, float, float], int]] = []
    if "polygon" in allowed:
        for kind, points in _polygon_candidates(contour, polygon_vertices):
            candidates.append((kind, "polygon", points, len(points)))
    if "trapezoid" in allowed:
        for kind, points in _trapezoid_candidates(target):
            candidates.append((kind, "polygon", points, 4))
    if "rotated_rect" in allowed:
        item = _rotated_rect_candidate(contour)
        if item is not None:
            candidates.append((item[0], "polygon", item[1], 4))
    if "triangle" in allowed:
        item = _triangle_candidate(contour)
        if item is not None:
            candidates.append((item[0], "polygon", item[1], 3))
    if "ellipse" in allowed and len(contour) >= 5:
        (cx, cy), (diameter_a, diameter_b), angle = cv2.fitEllipse(contour)
        candidates.append(("ellipse", "ellipse", (cx, cy, diameter_a * 0.5, diameter_b * 0.5, angle), 4))

    best: PrimitiveFit | None = None
    for kind, shape_type, geometry, complexity in candidates:
        if shape_type == "ellipse":
            cx, cy, rx, ry, angle = geometry
            candidate_mask = _ellipse_mask(target.shape, cx, cy, rx, ry, angle)
            score, iou, recall, precision = _metrics(target, candidate_mask, complexity)
            fit = PrimitiveFit(kind, "ellipse", score, iou, recall, precision, complexity, cx=cx, cy=cy, rx=rx, ry=ry)
        else:
            points = np.asarray(geometry, dtype=np.float32)
            candidate_mask = _polygon_mask(target.shape, points)
            score, iou, recall, precision = _metrics(target, candidate_mask, complexity)
            fit = PrimitiveFit(
                kind,
                "polygon",
                score,
                iou,
                recall,
                precision,
                complexity,
                points=[(float(x), float(y)) for x, y in points],
            )
        if best is None or fit.score > best.score:
            best = fit
    return best
