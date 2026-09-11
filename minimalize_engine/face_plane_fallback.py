from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .macro_subject_guard import MacroSubjectGuardResult
from .models import Shape
from .subject_segmentation import SubjectSegmentation


@dataclass(frozen=True)
class FacePlaneFallbackResult:
    enabled: bool
    reason: str
    shape: Shape | None = None
    bbox: tuple[int, int, int, int] | None = None
    skin_ratio: float = 0.0
    area_ratio: float = 0.0
    source: str = "none"

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "face_plane_created": self.shape is not None,
            "bbox": list(self.bbox) if self.bbox is not None else None,
            "skin_ratio": round(float(self.skin_ratio), 6),
            "area_ratio": round(float(self.area_ratio), 6),
            "source": self.source,
            "color": list(self.shape.fill_color) if self.shape is not None and self.shape.fill_color is not None else None,
        }


def _subject_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask > 0)
    if xs.size < 64:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _head_window(
    bbox: tuple[int, int, int, int], width: int, height: int
) -> tuple[int, int, int, int]:
    sx0, sy0, sx1, sy1 = bbox
    sw = max(sx1 - sx0, 1)
    sh = max(sy1 - sy0, 1)
    return (
        max(0, int(round(sx0 + sw * 0.22))),
        max(0, int(round(sy0 + sh * 0.04))),
        min(width, int(round(sx0 + sw * 0.78))),
        min(height, int(round(sy0 + sh * 0.49))),
    )


def _skin_mask(rgb: np.ndarray, subject: np.ndarray, window: tuple[int, int, int, int]) -> np.ndarray:
    ycrcb = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    yy, cr, cb = cv2.split(ycrcb)
    skin = (
        (yy >= 78)
        & (cr >= 132)
        & (cr <= 194)
        & (cb >= 68)
        & (cb <= 154)
        & (subject > 0)
    )
    x0, y0, x1, y1 = window
    clipped = np.zeros_like(subject, dtype=bool)
    clipped[y0:y1, x0:x1] = True
    skin &= clipped
    return cv2.morphologyEx(skin.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))


def _component_candidate(
    skin: np.ndarray,
    bbox: tuple[int, int, int, int],
    width: int,
    height: int,
) -> tuple[np.ndarray | None, str]:
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(skin, 8)
    if count <= 1:
        return None, "skin_component_missing"
    sx0, sy0, sx1, sy1 = bbox
    sw = max(sx1 - sx0, 1)
    sh = max(sy1 - sy0, 1)
    expected = np.asarray([sx0 + sw * 0.50, sy0 + sh * 0.29], dtype=float)
    canvas_area = max(float(width * height), 1.0)
    ranked: list[tuple[float, int]] = []
    oversized: list[tuple[float, int]] = []
    for index in range(1, count):
        area = int(stats[index, cv2.CC_STAT_AREA])
        ratio = area / canvas_area
        if ratio < 0.0012 or ratio > 0.18:
            continue
        x = int(stats[index, cv2.CC_STAT_LEFT])
        y = int(stats[index, cv2.CC_STAT_TOP])
        w = int(stats[index, cv2.CC_STAT_WIDTH])
        h = int(stats[index, cv2.CC_STAT_HEIGHT])
        aspect = float(w) / max(float(h), 1.0)
        if not 0.38 <= aspect <= 1.85:
            continue
        cx, cy = centroids[index]
        distance = float(np.linalg.norm(np.asarray([cx, cy]) - expected)) / max(float(min(width, height)), 1.0)
        if ratio > 0.075:
            if distance <= 0.12 and 0.70 <= aspect <= 1.60:
                oversized.append((distance, index))
            continue
        if distance > 0.27:
            continue
        center_bonus = max(0.0, 0.27 - distance)
        ranked.append((ratio * 4.0 + center_bonus * 0.9, index))
    if oversized:
        _distance, index = min(oversized)
        component = labels == index
        core = np.zeros_like(component, dtype=bool)
        fx0 = max(0, int(round(sx0 + sw * 0.36)))
        fx1 = min(width, int(round(sx0 + sw * 0.64)))
        fy0 = max(0, int(round(sy0 + sh * 0.18)))
        fy1 = min(height, int(round(sy0 + sh * 0.44)))
        core[fy0:fy1, fx0:fx1] = True
        sliced = (component & core).astype(np.uint8)
        if int(sliced.sum()) >= max(18, int(round(canvas_area * 0.0012))):
            return sliced, "central_skin_window"
    if not ranked:
        return None, "skin_component_gate"
    _score, index = max(ranked)
    component = labels == index
    ys, xs = np.where(component)
    if xs.size:
        bx0, by0, bx1, by1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
        bbox_ratio = float(max(bx1 - bx0, 1) * max(by1 - by0, 1)) / canvas_area
        if bbox_ratio > 0.085:
            core = np.zeros_like(component, dtype=bool)
            fx0 = max(0, int(round(sx0 + sw * 0.36)))
            fx1 = min(width, int(round(sx0 + sw * 0.64)))
            fy0 = max(0, int(round(sy0 + sh * 0.18)))
            fy1 = min(height, int(round(sy0 + sh * 0.44)))
            core[fy0:fy1, fx0:fx1] = True
            sliced = (component & core).astype(np.uint8)
            if int(sliced.sum()) >= max(18, int(round(canvas_area * 0.0012))):
                return sliced, "central_skin_window"
    return component.astype(np.uint8), "skin_component"


def _cluster_fallback(
    rgb: np.ndarray,
    subject: np.ndarray,
    window: tuple[int, int, int, int],
    background: tuple[int, int, int] | None,
) -> np.ndarray | None:
    x0, y0, x1, y1 = window
    candidate = np.zeros_like(subject, dtype=np.uint8)
    region_mask = subject[y0:y1, x0:x1] > 0
    pixels = rgb[y0:y1, x0:x1][region_mask]
    if len(pixels) < 32:
        return None
    bins = (pixels.astype(np.int16) // 20).astype(np.int16)
    keys, inverse, counts = np.unique(bins, axis=0, return_inverse=True, return_counts=True)
    bg = np.asarray(background or (255, 255, 255), dtype=np.float32)
    ranked: list[tuple[float, np.ndarray]] = []
    total = max(len(pixels), 1)
    for index, _key in enumerate(keys):
        selected = pixels[inverse == index]
        if len(selected) < max(8, int(round(total * 0.025))):
            continue
        color = np.median(selected, axis=0).astype(np.uint8)
        ycc = cv2.cvtColor(color.reshape(1, 1, 3), cv2.COLOR_RGB2YCrCb)[0, 0]
        yy, cr, cb = (int(v) for v in ycc)
        if yy < 82 or not 130 <= cr <= 198 or not 66 <= cb <= 158:
            continue
        bg_distance = float(np.linalg.norm(color.astype(np.float32) - bg))
        if bg_distance < 18.0:
            continue
        fraction = len(selected) / total
        warmth = max(0.0, float(cr) - float(cb)) / 128.0
        ranked.append((fraction * 3.0 + warmth * 0.35 + min(bg_distance / 255.0, 1.0) * 0.15, color))
    if not ranked:
        return None
    _score, color = max(ranked, key=lambda item: item[0])
    crop = rgb[y0:y1, x0:x1].astype(np.int16)
    distance = np.linalg.norm(crop - color.astype(np.int16)[None, None, :], axis=2)
    local = (distance <= 34.0) & region_mask
    candidate[y0:y1, x0:x1] = local.astype(np.uint8)
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(candidate, 8)
    if count <= 1:
        return None
    index = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    if int(stats[index, cv2.CC_STAT_AREA]) < 12:
        return None
    return (labels == index).astype(np.uint8)



def _preferred_skin_color(
    rgb: np.ndarray,
    subject: np.ndarray,
    window: tuple[int, int, int, int],
    background: tuple[int, int, int] | None,
) -> tuple[int, int, int] | None:
    x0, y0, x1, y1 = window
    region_mask = subject[y0:y1, x0:x1] > 0
    pixels = rgb[y0:y1, x0:x1][region_mask]
    if len(pixels) < 32:
        return None
    bins = (pixels.astype(np.int16) // 16).astype(np.int16)
    _keys, inverse, counts = np.unique(bins, axis=0, return_inverse=True, return_counts=True)
    bg = np.asarray(background or (255, 255, 255), dtype=np.float32)
    total = max(len(pixels), 1)
    ranked: list[tuple[float, tuple[int, int, int]]] = []
    for index, count in enumerate(counts):
        if int(count) < max(10, int(round(total * 0.008))):
            continue
        color = np.median(pixels[inverse == index], axis=0).astype(np.uint8)
        yy, cr, cb = (int(v) for v in cv2.cvtColor(color.reshape(1, 1, 3), cv2.COLOR_RGB2YCrCb)[0, 0])
        if yy < 135 or not 134 <= cr <= 190 or not 78 <= cb <= 132:
            continue
        if int(color[0]) - int(color[2]) > 58:
            continue
        distance = float(np.linalg.norm(color.astype(np.float32) - bg))
        if distance < 14.0:
            continue
        fraction = int(count) / total
        warmth = max(0.0, float(cr - cb)) / 80.0
        brightness = yy / 255.0
        score = fraction * 2.2 + warmth * 0.55 + brightness * 0.35 + min(distance / 255.0, 1.0) * 0.12
        ranked.append((score, tuple(int(v) for v in color)))
    return max(ranked, key=lambda item: item[0])[1] if ranked else None

def _plane_from_component(
    rgb: np.ndarray,
    component: np.ndarray,
    width: int,
    height: int,
    *,
    source: str,
    preferred_fill: tuple[int, int, int] | None = None,
) -> FacePlaneFallbackResult:
    ys, xs = np.where(component > 0)
    if xs.size < 12:
        return FacePlaneFallbackResult(False, "face_pixels_too_small")
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    bw, bh = max(x1 - x0, 1), max(y1 - y0, 1)
    canvas_area = max(float(width * height), 1.0)
    area_ratio = float(bw * bh) / canvas_area
    if not 0.0015 <= area_ratio <= 0.085:
        return FacePlaneFallbackResult(False, "face_geometry_gate", bbox=(x0, y0, x1, y1), area_ratio=area_ratio)
    pixels = rgb[component > 0]
    ycc = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_RGB2YCrCb).reshape(-1, 3)
    yy, cr, cb = ycc[:, 0], ycc[:, 1], ycc[:, 2]
    skin_like = (yy >= 78) & (cr >= 132) & (cr <= 194) & (cb >= 68) & (cb <= 154)
    skin_pixels = pixels[skin_like]
    color_pixels = skin_pixels if len(skin_pixels) >= max(12, int(round(len(pixels) * 0.12))) else pixels
    fill = preferred_fill or tuple(int(v) for v in np.median(color_pixels, axis=0))
    points = [
        (x0 + 0.18 * bw, y0),
        (x1 - 0.18 * bw, y0),
        (x1, y0 + 0.32 * bh),
        (x1 - 0.08 * bw, y1),
        (x0 + 0.08 * bw, y1),
        (x0, y0 + 0.32 * bh),
    ]
    shape = Shape(
        id=948000,
        shape_type="polygon",
        fill_color=fill,
        points=[(float(x), float(y)) for x, y in points],
        z_index=39950,
        importance=1.0,
        source_role="phase15_face_fallback_anchor",
        layer_name="foreground",
        semantic_type="character_face_anchor",
        character_part="face",
        part_confidence=0.86,
    )
    skin_ratio = float(component.sum()) / max(float(bw * bh), 1.0)
    return FacePlaneFallbackResult(
        True,
        "fallback_face_plane",
        shape=shape,
        bbox=(x0, y0, x1, y1),
        skin_ratio=skin_ratio,
        area_ratio=area_ratio,
        source=source,
    )


def build_face_plane_fallback(
    segmentation: SubjectSegmentation,
    macro_guard: MacroSubjectGuardResult,
    width: int,
    height: int,
) -> FacePlaneFallbackResult:
    """Create one faceless source-colored skin plane when explicit face metadata is absent."""
    if segmentation.rgba is None or segmentation.mask is None:
        return FacePlaneFallbackResult(False, "subject_candidate_missing")
    if not macro_guard.enabled:
        return FacePlaneFallbackResult(False, "macro_subject_guard_required")

    width = max(int(width), 1)
    height = max(int(height), 1)
    rgb = cv2.resize(segmentation.rgba[:, :, :3], (width, height), interpolation=cv2.INTER_AREA)
    subject = cv2.resize(segmentation.mask.astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST)
    subject = (subject > 0).astype(np.uint8)
    bbox = macro_guard.subject_bbox or _subject_bbox(subject)
    if bbox is None:
        return FacePlaneFallbackResult(False, "subject_bbox_missing")
    window = _head_window(bbox, width, height)
    skin = _skin_mask(rgb, subject, window)
    preferred_fill = _preferred_skin_color(rgb, subject, window, segmentation.background_rgb)
    component, source = _component_candidate(skin, bbox, width, height)
    if component is None:
        component = _cluster_fallback(rgb, subject, window, segmentation.background_rgb)
        source = "skin_color_cluster"
    if component is None:
        return FacePlaneFallbackResult(False, "skin_evidence_missing")
    result = _plane_from_component(
        rgb, component, width, height, source=source, preferred_fill=preferred_fill
    )
    if result.enabled or result.reason != "face_geometry_gate":
        return result

    # Broad warm hair/skin clusters can span most of the upper body. Keep the
    # evidence source-derived, but crop it to a conservative central upper
    # subject window before giving up. This recovers one blank face plane
    # without inventing eyes, mouth, or hair detail.
    sx0, sy0, sx1, sy1 = bbox
    sw = max(sx1 - sx0, 1)
    sh = max(sy1 - sy0, 1)
    core = np.zeros_like(component, dtype=np.uint8)
    fx0 = max(0, int(round(sx0 + sw * 0.36)))
    fx1 = min(width, int(round(sx0 + sw * 0.64)))
    fy0 = max(0, int(round(sy0 + sh * 0.18)))
    fy1 = min(height, int(round(sy0 + sh * 0.44)))
    core[fy0:fy1, fx0:fx1] = 1
    sliced = (component.astype(np.uint8) & core).astype(np.uint8)
    if int(sliced.sum()) < max(18, int(round(width * height * 0.0012))):
        return result
    return _plane_from_component(
        rgb, sliced, width, height, source="central_skin_window", preferred_fill=preferred_fill
    )
