from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

from .models import Shape
from .palette.feature_palette import extract_feature_palette, rgb_to_lab
from .structure_geometry import simplify_mask_polygon


@dataclass
class StructureBodyPlaneResult:
    enabled: bool
    reason: str
    shapes: tuple[Shape, ...] = ()
    body_area_ratio: float = 0.0
    zone_count: int = 0
    accent_count: int = 0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "shape_count": len(self.shapes),
            "body_area_ratio": round(float(self.body_area_ratio), 6),
            "zone_count": int(self.zone_count),
            "accent_count": int(self.accent_count),
        }


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _polygon(mask: np.ndarray, max_points: int = 10) -> list[tuple[float, float]] | None:
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    perimeter = float(cv2.arcLength(contour, True))
    chosen = None
    for ratio in (0.012, 0.018, 0.026, 0.038, 0.052):
        approx = cv2.approxPolyDP(contour, max(1.5, perimeter * ratio), True).reshape(-1, 2)
        chosen = approx
        if 3 <= len(approx) <= max_points:
            break
    if chosen is None or len(chosen) < 3:
        return None
    return [(float(x), float(y)) for x, y in chosen]


def _median_color(rgb: np.ndarray, mask: np.ndarray) -> tuple[int, int, int]:
    pixels = rgb[mask > 0]
    if len(pixels) == 0:
        return 160, 160, 160
    return tuple(int(v) for v in np.median(pixels, axis=0).astype(np.uint8))


def _dominant_color(rgb: np.ndarray, mask: np.ndarray) -> tuple[int, int, int]:
    ys, xs = np.where(mask > 0)
    if len(xs) < 24:
        return _median_color(rgb, mask)
    pixels = rgb[ys, xs]
    if len(pixels) > 9000:
        indexes = np.linspace(0, len(pixels) - 1, 9000).astype(np.int32)
        pixels = pixels[indexes]
    lab = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
    clusters = min(3, max(1, len(lab) // 180))
    if clusters < 2:
        return _median_color(rgb, mask)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 25, 0.8)
    cv2.setRNGSeed(1701)
    _score, labels, _centers = cv2.kmeans(lab, clusters, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.ravel(), minlength=clusters)
    selected = pixels[labels.ravel() == int(np.argmax(counts))]
    return tuple(int(v) for v in np.median(selected, axis=0).astype(np.uint8))


def _central_span(mask: np.ndarray, y: int, cx: float, band: int = 3) -> tuple[int, int] | None:
    h, w = mask.shape
    y0 = max(0, y - band)
    y1 = min(h, y + band + 1)
    row = (mask[y0:y1].max(axis=0) > 0).astype(np.uint8)
    center = int(round(cx))
    if center < 0 or center >= w or row[center] == 0:
        xs = np.where(row > 0)[0]
        if len(xs) == 0:
            return None
        center = int(xs[np.argmin(np.abs(xs - center))])
    left = center
    right = center
    while left > 0 and row[left - 1] > 0:
        left -= 1
    while right + 1 < w and row[right + 1] > 0:
        right += 1
    return left, right + 1


def _zone_masks(body: np.ndarray, face: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    h, w = body.shape
    face_box = _bbox(face)
    body_box = _bbox(body)
    if body_box is None:
        zeros = np.zeros_like(body, dtype=np.uint8)
        return zeros, zeros, zeros
    bx0, by0, bx1, by1 = body_box
    if face_box is None:
        cx = (bx0 + bx1) * 0.5
        face_h = max((by1 - by0) * 0.18, 20.0)
        shoulder_y = by0 + int((by1 - by0) * 0.24)
    else:
        fx0, fy0, fx1, fy1 = face_box
        cx = (fx0 + fx1) * 0.5
        face_h = max(float(fy1 - fy0), 20.0)
        shoulder_y = min(by1 - 1, int(round(fy1 + face_h * 0.16)))

    body_h = max(by1 - shoulder_y, 1)
    sample_ys = [
        shoulder_y,
        min(by1 - 1, shoulder_y + int(body_h * 0.34)),
        min(by1 - 1, shoulder_y + int(body_h * 0.72)),
        by1 - 1,
    ]
    spans = []
    fallback_half = max((bx1 - bx0) * 0.18, 10.0)
    for y in sample_ys:
        span = _central_span(body, y, cx, band=max(2, int(round(h * 0.008))))
        if span is None:
            spans.append((cx - fallback_half, cx + fallback_half))
            continue
        left, right = span
        raw_half = max((right - left) * 0.5, 6.0)
        raw_center = (left + right) * 0.5
        center = cx * 0.72 + raw_center * 0.28
        half = min(raw_half, (bx1 - bx0) * 0.34)
        half = max(half, fallback_half * 0.75)
        spans.append((center - half, center + half))

    pts_left = [(int(round(l)), int(y)) for y, (l, _r) in zip(sample_ys, spans)]
    pts_right = [(int(round(r)), int(y)) for y, (_l, r) in reversed(list(zip(sample_ys, spans)))]
    torso_poly = np.asarray(pts_left + pts_right, dtype=np.int32)
    torso_prior = np.zeros_like(body, dtype=np.uint8)
    cv2.fillPoly(torso_prior, [torso_poly], 1)
    torso = torso_prior & body

    remaining = body & (1 - torso)
    left = np.zeros_like(body, dtype=np.uint8)
    right = np.zeros_like(body, dtype=np.uint8)
    split = int(round(cx))
    left[:, :split] = remaining[:, :split]
    right[:, split:] = remaining[:, split:]
    return left, torso, right

def _absorb_body_residual(
    zones: tuple[np.ndarray, np.ndarray, np.ndarray],
    body: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    result = [(zone > 0).astype(np.uint8) & body for zone in zones]
    covered = np.zeros_like(body, dtype=np.uint8)
    for zone in result:
        covered |= zone
    residual = body & (1 - covered)
    if not np.any(residual):
        return tuple(result)

    active = [index for index, zone in enumerate(result) if np.any(zone)]
    if not active:
        return tuple(result)
    distances = []
    for index in active:
        inverse = (1 - result[index]).astype(np.uint8)
        distances.append(cv2.distanceTransform(inverse, cv2.DIST_L2, 5))
    nearest = np.argmin(np.stack(distances, axis=-1), axis=-1)
    for rank, index in enumerate(active):
        result[index] |= (residual & (nearest == rank)).astype(np.uint8)
    return tuple(result)


def _accent_mask(rgb: np.ndarray, zone: np.ndarray) -> np.ndarray | None:
    ys, xs = np.where(zone > 0)
    if len(xs) < 120:
        return None
    pixels = rgb[ys, xs]
    lab = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
    spread = float(np.mean(np.std(lab, axis=0)))
    if spread < 8.0:
        return None
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 25, 0.8)
    cv2.setRNGSeed(1701)
    _score, labels, _centers = cv2.kmeans(lab, 2, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    labels = labels.ravel()
    counts = np.bincount(labels, minlength=2)
    accent_label = int(np.argmin(counts))
    ratio = float(counts[accent_label]) / max(float(len(labels)), 1.0)
    if not 0.16 <= ratio <= 0.48:
        return None
    accent = np.zeros_like(zone, dtype=np.uint8)
    selected = labels == accent_label
    accent[ys[selected], xs[selected]] = 1
    accent = cv2.morphologyEx(
        accent,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
    ) & zone
    count, components, stats, _ = cv2.connectedComponentsWithStats(accent, 8)
    if count <= 1:
        return None
    index = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
    component = (components == index).astype(np.uint8)
    if int(component.sum()) < int(zone.sum() * 0.12):
        return None
    return component


def _characteristic_torso_planes(rgb: np.ndarray, zone: np.ndarray, max_colors: int = 4):
    ys, xs = np.where(zone > 0)
    if len(xs) < 120:
        return None
    rgba = np.zeros((*zone.shape, 4), dtype=np.uint8)
    rgba[..., :3] = rgb
    rgba[..., 3] = (zone > 0).astype(np.uint8) * 255
    try:
        palette = extract_feature_palette(Image.fromarray(rgba, "RGBA"), n_colors=max_colors, remove_background=False)
    except ValueError:
        return None
    if len(palette) < 2:
        return None
    pixels = rgb[ys, xs]
    labs = rgb_to_lab(pixels)
    centers = rgb_to_lab(np.asarray([color.rgb for color in palette], dtype=np.uint8))
    labels = np.argmin(np.linalg.norm(labs[:, None, :] - centers[None, :, :], axis=2), axis=1)
    counts = np.bincount(labels, minlength=len(palette))
    base_index = int(np.argmax(counts))
    base_color = tuple(int(v) for v in palette[base_index].rgb)
    accents = []
    base_lab = centers[base_index]
    order = sorted((i for i in range(len(palette)) if i != base_index), key=lambda i: palette[i].score, reverse=True)
    for index in order:
        share = float(counts[index]) / max(float(len(labels)), 1.0)
        if share < 0.07 or share > 0.48 or float(np.linalg.norm(centers[index] - base_lab)) < 14.0:
            continue
        candidate = np.zeros_like(zone, dtype=np.uint8)
        chosen = labels == index
        candidate[ys[chosen], xs[chosen]] = 1
        candidate = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))) & zone
        count, components, stats, _ = cv2.connectedComponentsWithStats(candidate, 8)
        if count <= 1:
            continue
        component_index = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
        component = (components == component_index).astype(np.uint8)
        if int(component.sum()) < max(40, int(zone.sum() * 0.05)):
            continue
        accents.append((component, tuple(int(v) for v in palette[index].rgb), palette[index].family))
    return base_color, accents


def build_structure_body_planes(
    rgb: np.ndarray,
    subject_mask: np.ndarray,
    *,
    face_mask: np.ndarray | None = None,
    head_mask: np.ndarray | None = None,
    hair_mask: np.ndarray | None = None,
    torso_mask: np.ndarray | None = None,
    left_arm_mask: np.ndarray | None = None,
    right_arm_mask: np.ndarray | None = None,
    max_accents: int = 2,
    start_id: int = 963000,
) -> StructureBodyPlaneResult:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        return StructureBodyPlaneResult(False, "rgb_required")
    if subject_mask.ndim != 2 or subject_mask.shape != rgb.shape[:2]:
        return StructureBodyPlaneResult(False, "mask_shape_mismatch")

    body = (subject_mask > 0).astype(np.uint8)
    locked = np.zeros_like(body)
    # Keep body/arms underneath head and long hair; those layers are painted above.
    # Only the blank face itself is excluded from body-zone construction.
    for part in (face_mask,):
        if part is not None and part.shape == body.shape:
            locked |= (part > 0).astype(np.uint8)
    if np.any(locked):
        locked = cv2.dilate(locked, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
        body &= (locked == 0).astype(np.uint8)

    area_ratio = float(body.mean())
    if int(body.sum()) < 120:
        return StructureBodyPlaneResult(False, "body_area_gate", body_area_ratio=area_ratio)

    face = (face_mask > 0).astype(np.uint8) if face_mask is not None and face_mask.shape == body.shape else np.zeros_like(body)
    explicit = []
    for part in (left_arm_mask, torso_mask, right_arm_mask):
        if part is None or part.shape != body.shape:
            explicit.append(np.zeros_like(body, dtype=np.uint8))
        else:
            explicit.append((part > 0).astype(np.uint8) & body)
    explicit_total = sum(int(zone.sum()) for zone in explicit)
    use_explicit = explicit_total >= max(80, int(body.sum() * 0.32)) and sum(int(zone.sum()) >= 24 for zone in explicit) >= 2
    zones = tuple(explicit) if use_explicit else _zone_masks(body, face)
    zones = _absorb_body_residual(zones, body)
    names = ("left_sleeve", "torso", "right_sleeve")
    shapes: list[Shape] = []
    shape_id = start_id
    zone_count = 0
    accent_count = 0

    for zone_index, (name, zone) in enumerate(zip(names, zones)):
        if int(zone.sum()) < max(40, int(body.sum() * 0.035)):
            continue
        points = simplify_mask_polygon(zone, max_points=14, min_iou=0.88)
        if points is None:
            continue
        characteristic = _characteristic_torso_planes(rgb, zone, max_colors=4) if name == "torso" else None
        # Keep the established dominant major plane as the torso base.
        # Characteristic selection is only allowed to rescue secondary identity colors.
        base_color = _dominant_color(rgb, zone)
        shapes.append(
            Shape(
                id=shape_id,
                shape_type="polygon",
                fill_color=base_color,
                points=points,
                z_index=30320 + zone_index * 10,
                importance=0.985,
                source_role=f"phase17_body_zone_{name}",
                layer_name="foreground",
                semantic_type="character_body_zone",
                character_part="torso" if name == "torso" else "arm",
                part_confidence=0.88,
                side_hint="left" if name == "left_sleeve" else "right" if name == "right_sleeve" else "unknown",
            )
        )
        shape_id += 1
        zone_count += 1

        # Sleeves stay as one coarse plane. Torso can use up to two
        # characteristic major-color planes selected inside the torso mask.
        if name != "torso" or accent_count >= max_accents:
            continue
        candidates = []
        if characteristic is not None:
            candidates = characteristic[1][: max(0, max_accents - accent_count)]
        if not candidates:
            accent = _accent_mask(rgb, zone)
            if accent is not None:
                candidates = [(accent, _median_color(rgb, accent), "fallback")]
        base_lab_actual = rgb_to_lab(np.asarray(base_color, dtype=np.uint8))
        for accent_index, (accent, accent_color, family) in enumerate(candidates):
            if accent_count >= max_accents:
                break
            accent_lab_actual = rgb_to_lab(np.asarray(accent_color, dtype=np.uint8))
            if float(np.linalg.norm(accent_lab_actual - base_lab_actual)) < 14.0:
                continue
            accent_points = _polygon(accent, max_points=7)
            if accent_points is None:
                continue
            shapes.append(
                Shape(
                    id=shape_id,
                    shape_type="polygon",
                    fill_color=accent_color,
                    points=accent_points,
                    z_index=30325 + zone_index * 10 + accent_count,
                    importance=0.95,
                    source_role=f"phase18_body_accent_torso_{family}_{accent_index + 1}",
                    layer_name="foreground",
                    semantic_type="character_body_accent",
                    character_part="torso",
                    part_confidence=0.84,
                    side_hint="unknown",
                )
            )
            shape_id += 1
            accent_count += 1

    if not shapes:
        return StructureBodyPlaneResult(False, "zone_polygon_failed", body_area_ratio=area_ratio)
    return StructureBodyPlaneResult(
        True,
        "ok",
        tuple(shapes),
        body_area_ratio=area_ratio,
        zone_count=zone_count,
        accent_count=accent_count,
    )
