from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin
from pathlib import Path

import cv2
import numpy as np

from .io.image_loader import load_image_data
from .models import Scene, Shape


@dataclass
class OpaqueSubjectHierarchy:
    enabled: bool
    confidence: float = 0.0
    subject_area_ratio: float = 0.0
    bbox: tuple[int, int, int, int] | None = None
    reason: str = "disabled"
    mask: np.ndarray | None = None

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "confidence": round(float(self.confidence), 6),
            "subject_area_ratio": round(float(self.subject_area_ratio), 6),
            "bbox": list(self.bbox) if self.bbox is not None else None,
            "reason": self.reason,
        }


def _source_rgb(image_or_path) -> np.ndarray:
    if isinstance(image_or_path, (str, Path)):
        return load_image_data(image_or_path).rgb
    arr = np.asarray(image_or_path)
    if arr.ndim != 3 or arr.shape[2] not in {3, 4}:
        raise ValueError("image array must be HxWx3 or HxWx4")
    return arr[:, :, :3]


def _border_prototypes(lab: np.ndarray, border: int) -> np.ndarray:
    h, w = lab.shape[:2]
    strips = [
        lab[:border, :, :],
        lab[h - border :, :, :],
        lab[:, :border, :],
        lab[:, w - border :, :],
    ]
    centers = [np.median(strip.reshape(-1, 3), axis=0) for strip in strips]
    all_border = np.concatenate([strip.reshape(-1, 3) for strip in strips], axis=0)
    centers.append(np.median(all_border, axis=0))
    unique: list[np.ndarray] = []
    for center in centers:
        if not unique or min(float(np.linalg.norm(center - x)) for x in unique) >= 5.0:
            unique.append(center)
    return np.asarray(unique, dtype=np.float32)


def _foreground_distance(lab: np.ndarray, prototypes: np.ndarray) -> np.ndarray:
    pixels = lab.astype(np.float32)[:, :, None, :]
    centers = prototypes[None, None, :, :]
    return np.linalg.norm(pixels - centers, axis=3).min(axis=2)


def _component_score(mask: np.ndarray, distance: np.ndarray, label: int, stats, centroids) -> float:
    h, w = mask.shape
    x, y, cw, ch, area = [int(v) for v in stats[label]]
    area_ratio = area / max(float(h * w), 1.0)
    if area_ratio < 0.04 or area_ratio > 0.72:
        return -1.0
    cx, cy = [float(v) for v in centroids[label]]
    dx = (cx - w * 0.5) / max(w * 0.5, 1.0)
    dy = (cy - h * 0.5) / max(h * 0.5, 1.0)
    center_score = max(0.0, 1.0 - float(np.hypot(dx, dy)) / 1.15)
    area_score = min(1.0, area_ratio / 0.18)
    if area_ratio > 0.55:
        area_score *= max(0.0, 1.0 - (area_ratio - 0.55) / 0.17)
    comp = mask == label
    contrast = float(distance[comp].mean()) if np.any(comp) else 0.0
    contrast_score = min(1.0, contrast / 42.0)
    center_box = comp[int(h * 0.15) : int(h * 0.85), int(w * 0.15) : int(w * 0.85)]
    center_fraction = float(center_box.sum()) / max(float(area), 1.0)
    touches = int(x <= 1) + int(y <= 1) + int(x + cw >= w - 1) + int(y + ch >= h - 1)
    edge_penalty = 0.10 * max(0, touches - 1)
    return 0.34 * area_score + 0.34 * center_score + 0.22 * contrast_score + 0.10 * min(1.0, center_fraction / 0.7) - edge_penalty


def estimate_opaque_subject_hierarchy(image_or_path, scene: Scene) -> OpaqueSubjectHierarchy:
    if bool(scene.metadata.get("subject_mode")):
        return OpaqueSubjectHierarchy(False, reason="alpha_subject")
    rgb = _source_rgb(image_or_path)
    resized = cv2.resize(rgb, (scene.width, scene.height), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(resized, cv2.COLOR_RGB2LAB).astype(np.float32)
    h, w = lab.shape[:2]
    min_side = max(1, min(h, w))
    border = max(2, int(round(min_side * 0.06)))
    prototypes = _border_prototypes(lab, border)
    distance = _foreground_distance(lab, prototypes)

    border_values = np.concatenate([
        distance[:border, :].ravel(), distance[h - border :, :].ravel(),
        distance[:, :border].ravel(), distance[:, w - border :].ravel(),
    ])
    threshold = max(16.0, float(np.percentile(border_values, 88)) + 7.0)
    candidate = (distance >= threshold).astype(np.uint8)

    close_k = max(3, int(round(min_side * 0.018)))
    if close_k % 2 == 0:
        close_k += 1
    open_k = max(3, int(round(min_side * 0.008)))
    if open_k % 2 == 0:
        open_k += 1
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, np.ones((close_k, close_k), np.uint8))
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_OPEN, np.ones((open_k, open_k), np.uint8))

    count, labels, stats, centroids = cv2.connectedComponentsWithStats(candidate, connectivity=8)
    if count <= 1:
        return OpaqueSubjectHierarchy(False, reason="no_component")
    scores = [(label, _component_score(labels, distance, label, stats, centroids)) for label in range(1, count)]
    best_label, best_score = max(scores, key=lambda item: item[1])
    if best_score < 0.56:
        return OpaqueSubjectHierarchy(False, confidence=max(0.0, best_score), reason="low_confidence")

    best = (labels == best_label).astype(np.uint8)
    x, y, bw, bh, area = [int(v) for v in stats[best_label]]
    expand = max(2, int(round(min_side * 0.025)))
    x0, y0 = max(0, x - expand), max(0, y - expand)
    x1, y1 = min(w, x + bw + expand), min(h, y + bh + expand)
    for label, score in scores:
        if label == best_label or score < 0.34:
            continue
        cx, cy = [float(v) for v in centroids[label]]
        comp_area = int(stats[label, cv2.CC_STAT_AREA])
        if x0 <= cx <= x1 and y0 <= cy <= y1 and comp_area / max(float(h * w), 1.0) >= 0.004:
            best[labels == label] = 1

    ys, xs = np.where(best > 0)
    if len(xs) == 0:
        return OpaqueSubjectHierarchy(False, confidence=best_score, reason="empty_mask")
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    area_ratio = float(best.mean())
    if not 0.05 <= area_ratio <= 0.70:
        return OpaqueSubjectHierarchy(False, confidence=best_score, subject_area_ratio=area_ratio, bbox=bbox, reason="area_gate")
    return OpaqueSubjectHierarchy(True, confidence=min(1.0, best_score), subject_area_ratio=area_ratio, bbox=bbox, reason="accepted", mask=best)


def _shape_polygon(shape: Shape, curve_sides: int = 12) -> np.ndarray | None:
    if shape.shape_type == "polygon" and len(shape.points) >= 3:
        return np.asarray(shape.points, dtype=np.float32)
    if shape.shape_type == "rectangle":
        x, y = float(shape.x or 0.0), float(shape.y or 0.0)
        w, h = max(float(shape.width or 0.0), 0.0), max(float(shape.height or 0.0), 0.0)
        return np.asarray([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], dtype=np.float32)
    if shape.shape_type in {"circle", "ellipse"}:
        cx, cy = float(shape.cx or 0.0), float(shape.cy or 0.0)
        rx = max(float(shape.rx or 0.0), 0.0)
        ry = max(float(shape.ry if shape.ry is not None else rx), 0.0)
        if rx <= 0.0 or ry <= 0.0:
            return None
        return np.asarray([(cx + rx * cos(2 * pi * i / curve_sides), cy + ry * sin(2 * pi * i / curve_sides)) for i in range(curve_sides)], dtype=np.float32)
    return None


def shape_subject_overlap(shape: Shape, hierarchy: OpaqueSubjectHierarchy) -> float:
    if not hierarchy.enabled or hierarchy.mask is None or shape.fill_color is None or shape.shape_type == "line":
        return 0.0
    poly = _shape_polygon(shape)
    if poly is None or len(poly) < 3:
        return 0.0
    h, w = hierarchy.mask.shape
    x0 = max(0, int(np.floor(poly[:, 0].min())))
    y0 = max(0, int(np.floor(poly[:, 1].min())))
    x1 = min(w, int(np.ceil(poly[:, 0].max())) + 1)
    y1 = min(h, int(np.ceil(poly[:, 1].max())) + 1)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    local = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    pts = np.round(poly - np.asarray([x0, y0], dtype=np.float32)).astype(np.int32)
    cv2.fillPoly(local, [pts], 1)
    denom = int(local.sum())
    if denom <= 0:
        return 0.0
    subject = hierarchy.mask[y0:y1, x0:x1]
    return float((local * subject).sum()) / float(denom)
