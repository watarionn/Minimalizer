from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .models import Shape
from .subject_segmentation import SubjectSegmentation
from .opaque_subject_rescue import OpaqueSubjectRescue
from .io.image_loader import load_image_data


@dataclass(frozen=True)
class MacroSubjectGuardResult:
    enabled: bool
    reason: str
    shapes: tuple[Shape, ...] = ()
    subject_bbox: tuple[int, int, int, int] | None = None
    subject_area_ratio: float = 0.0
    subject_coverage_ratio: float = 0.0
    outside_subject_ratio: float = 0.0
    head_anchor_count: int = 0
    torso_anchor_count: int = 0
    arm_anchor_count: int = 0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "shape_count": len(self.shapes),
            "subject_bbox": list(self.subject_bbox) if self.subject_bbox is not None else None,
            "subject_area_ratio": round(float(self.subject_area_ratio), 6),
            "subject_coverage_ratio": round(float(self.subject_coverage_ratio), 6),
            "outside_subject_ratio": round(float(self.outside_subject_ratio), 6),
            "head_anchor_count": self.head_anchor_count,
            "torso_anchor_count": self.torso_anchor_count,
            "arm_anchor_count": self.arm_anchor_count,
        }


def _dominant_source_color(
    pixels: np.ndarray,
    background: tuple[int, int, int] | None,
    *,
    avoid_skin: bool = False,
) -> tuple[int, int, int]:
    if pixels.size == 0:
        return (128, 128, 128)
    pixels = pixels.reshape(-1, 3).astype(np.uint8, copy=False)
    bins = (pixels // 24).astype(np.int16)
    keys, inverse, counts = np.unique(bins, axis=0, return_inverse=True, return_counts=True)
    background_array = np.asarray(background or (255, 255, 255), dtype=np.float32)
    ranked: list[tuple[float, tuple[int, int, int]]] = []
    total = max(int(len(pixels)), 1)
    for index, _key in enumerate(keys):
        selected = pixels[inverse == index]
        color_array = np.median(selected, axis=0).astype(np.float32)
        color = tuple(int(v) for v in np.round(color_array))
        distance = float(np.linalg.norm(color_array - background_array))
        fraction = float(counts[index]) / float(total)
        ycc = cv2.cvtColor(np.asarray(color, dtype=np.uint8).reshape(1, 1, 3), cv2.COLOR_RGB2YCrCb)[0, 0]
        yy, cr, cb = (int(v) for v in ycc)
        skin_like = 78 <= yy and 132 <= cr <= 194 and 68 <= cb <= 154
        score = fraction + min(distance / 255.0, 1.0) * 0.08
        if avoid_skin and skin_like:
            score -= 0.35
        ranked.append((score, color))
    return max(ranked, key=lambda item: item[0])[1]


def _coarse_color_candidates(pixels: np.ndarray, *, step: int = 64) -> list[tuple[float, tuple[int, int, int]]]:
    if pixels.size == 0:
        return []
    pixels = pixels.reshape(-1, 3).astype(np.uint8, copy=False)
    bins = (pixels.astype(np.int16) // max(int(step), 1)).astype(np.int16)
    _keys, inverse, counts = np.unique(bins, axis=0, return_inverse=True, return_counts=True)
    total = max(int(len(pixels)), 1)
    out = []
    for index, count in enumerate(counts):
        color = tuple(int(v) for v in np.median(pixels[inverse == index], axis=0))
        out.append((float(count) / float(total), color))
    return sorted(out, key=lambda item: item[0], reverse=True)


def _arm_identity_color(
    pixels: np.ndarray,
    background: tuple[int, int, int] | None,
    head_color: tuple[int, int, int] | None,
) -> tuple[int, int, int]:
    candidates = _coarse_color_candidates(pixels, step=64)
    if not candidates:
        return _dominant_source_color(pixels, background)
    default_fraction, default = candidates[0]
    if head_color is None or float(np.linalg.norm(np.asarray(default) - np.asarray(head_color))) >= 48.0:
        return default
    if default_fraction >= 0.45:
        return default
    alternatives = []
    for fraction, color in candidates[1:]:
        chroma = max(color) - min(color)
        head_distance = float(np.linalg.norm(np.asarray(color) - np.asarray(head_color)))
        if fraction < 0.10 or chroma < 40 or head_distance < 70.0:
            continue
        alternatives.append((fraction + min(chroma / 255.0, 1.0) * 0.04, color))
    return max(alternatives, key=lambda item: item[0])[1] if alternatives else default


def _torso_identity_color(
    pixels: np.ndarray,
    background: tuple[int, int, int] | None,
) -> tuple[int, int, int]:
    candidates = _coarse_color_candidates(pixels, step=48)
    if not candidates:
        return _dominant_source_color(pixels, background, avoid_skin=True)
    bg = np.asarray(background or (255, 255, 255), dtype=np.float32)
    ranked = []
    for fraction, color in candidates:
        arr = np.asarray(color, dtype=np.uint8)
        yy, cr, cb = (int(v) for v in cv2.cvtColor(arr.reshape(1, 1, 3), cv2.COLOR_RGB2YCrCb)[0, 0])
        skin_like = 78 <= yy and 132 <= cr <= 194 and 68 <= cb <= 154
        if skin_like or float(np.linalg.norm(arr.astype(np.float32) - bg)) < 14.0:
            continue
        chroma = max(color) - min(color)
        score = fraction + (yy / 255.0) * 0.04 + (chroma / 255.0) * 0.01
        ranked.append((score, color))
    return max(ranked, key=lambda item: item[0])[1] if ranked else _dominant_source_color(pixels, background, avoid_skin=True)


def _role_color_pixels(
    rgb: np.ndarray,
    component: np.ndarray,
    bbox: tuple[int, int, int, int],
    zone_name: str,
) -> np.ndarray:
    sx0, sy0, sx1, sy1 = bbox
    sw, sh = max(sx1 - sx0, 1), max(sy1 - sy0, 1)
    limits = {
        "left_arm": (0.00, 0.14, 0.34, 0.84),
        "right_arm": (0.66, 0.14, 1.00, 0.84),
        "torso": (0.28, 0.42, 0.72, 0.95),
    }
    if zone_name not in limits:
        return rgb[component > 0]
    x0r, y0r, x1r, y1r = limits[zone_name]
    sample = np.zeros_like(component, dtype=bool)
    x0 = max(0, int(round(sx0 + sw * x0r))); x1 = min(component.shape[1], int(round(sx0 + sw * x1r)))
    y0 = max(0, int(round(sy0 + sh * y0r))); y1 = min(component.shape[0], int(round(sy0 + sh * y1r)))
    sample[y0:y1, x0:x1] = True
    sample &= component > 0
    pixels = rgb[sample]
    return pixels if len(pixels) >= 64 else rgb[component > 0]


def _bounded_rect(
    bbox: tuple[int, int, int, int],
    width: int,
    height: int,
    x0_ratio: float,
    y0_ratio: float,
    x1_ratio: float,
    y1_ratio: float,
) -> tuple[int, int, int, int]:
    sx0, sy0, sx1, sy1 = bbox
    sw = max(sx1 - sx0, 1)
    sh = max(sy1 - sy0, 1)
    x0 = max(0, min(width, int(round(sx0 + sw * x0_ratio))))
    x1 = max(0, min(width, int(round(sx0 + sw * x1_ratio))))
    y0 = max(0, min(height, int(round(sy0 + sh * y0_ratio))))
    y1 = max(0, min(height, int(round(sy0 + sh * y1_ratio))))
    return x0, y0, x1, y1


def _simplified_component_polygon(
    subject_mask: np.ndarray,
    rect: tuple[int, int, int, int],
    *,
    min_pixels: int,
    max_vertices: int = 8,
    max_outside_ratio: float = 0.24,
) -> tuple[np.ndarray | None, np.ndarray | None, float]:
    height, width = subject_mask.shape
    x0, y0, x1, y1 = rect
    if x1 <= x0 or y1 <= y0:
        return None, None, 1.0
    zone = np.zeros_like(subject_mask, dtype=np.uint8)
    zone[y0:y1, x0:x1] = subject_mask[y0:y1, x0:x1]
    zone = cv2.morphologyEx(zone, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(zone, 8)
    if count <= 1:
        return None, None, 1.0
    candidates = [
        (int(stats[index, cv2.CC_STAT_AREA]), index)
        for index in range(1, count)
        if int(stats[index, cv2.CC_STAT_AREA]) >= min_pixels
    ]
    if not candidates:
        return None, None, 1.0
    _area, index = max(candidates)
    component = (labels == index).astype(np.uint8)
    contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None, 1.0
    contour = max(contours, key=cv2.contourArea)
    perimeter = float(cv2.arcLength(contour, True))
    if perimeter <= 1e-6:
        return None, None, 1.0

    component_pixels = max(int(component.sum()), 1)
    polygon_candidates: list[tuple[float, int, float, np.ndarray]] = []
    for epsilon_ratio in (0.012, 0.018, 0.025, 0.030, 0.040, 0.045, 0.055, 0.070):
        polygon = cv2.approxPolyDP(
            contour, max(1.0, perimeter * epsilon_ratio), True
        ).reshape(-1, 2)
        if not 3 <= len(polygon) <= max_vertices:
            continue
        polygon_mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(polygon_mask, [np.round(polygon).astype(np.int32)], 1)
        polygon_pixels = max(int(polygon_mask.sum()), 1)
        outside_ratio = int((polygon_mask & (1 - subject_mask)).sum()) / polygon_pixels
        component_coverage = int((polygon_mask & component).sum()) / component_pixels
        if component_coverage < 0.65:
            continue
        polygon_candidates.append((outside_ratio, len(polygon), -component_coverage, polygon))
    if not polygon_candidates:
        return None, None, 1.0
    outside_ratio, _vertices, _coverage, polygon = min(polygon_candidates, key=lambda item: item[:3])
    if outside_ratio > max_outside_ratio:
        return None, None, outside_ratio
    return polygon.astype(np.float32), component, outside_ratio


def build_macro_subject_guard(
    segmentation: SubjectSegmentation,
    width: int,
    height: int,
) -> MacroSubjectGuardResult:
    """Build a few coarse subject anchors without inventing fine anatomy.

    This guard is intentionally conservative and only consumes the deterministic
    AI-free subject candidate that already exists in Minimalizer. It preserves a
    head/hair mass, a torso mass, and optional side/arm masses before later
    aggressive poster cleanup can collapse the person into background slabs.
    """
    if segmentation.rgba is None or segmentation.mask is None:
        return MacroSubjectGuardResult(False, "subject_candidate_missing")
    if segmentation.reason not in {"accepted", "confidence_gate", "phase15_opaque_rescue", "phase15_relaxed_border"}:
        return MacroSubjectGuardResult(False, "subject_candidate_reason_gate")
    border_floor = 0.18 if segmentation.reason == "phase15_relaxed_border" else 0.30
    if float(segmentation.border_dominant_fraction) < border_floor:
        return MacroSubjectGuardResult(False, "background_evidence_gate")
    if float(segmentation.center_fill_ratio) < 0.35:
        return MacroSubjectGuardResult(False, "center_fill_gate")
    if float(segmentation.border_leak_ratio) > 0.56:
        return MacroSubjectGuardResult(False, "border_leak_gate")
    if not segmentation.enabled and float(segmentation.confidence) < 0.42:
        return MacroSubjectGuardResult(False, "confidence_gate")

    width = max(int(width), 1)
    height = max(int(height), 1)
    rgb = cv2.resize(segmentation.rgba[:, :, :3], (width, height), interpolation=cv2.INTER_AREA)
    mask = cv2.resize(
        segmentation.mask.astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST
    )
    mask = (mask > 0).astype(np.uint8)
    ys, xs = np.where(mask > 0)
    if xs.size < 64:
        return MacroSubjectGuardResult(False, "subject_too_small")
    subject_area_ratio = float(mask.mean())
    if not 0.18 <= subject_area_ratio <= 0.82:
        return MacroSubjectGuardResult(False, "subject_area_gate", subject_area_ratio=subject_area_ratio)

    bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    canvas_area = max(float(width * height), 1.0)
    min_pixels = max(8, int(round(canvas_area * 0.0045)))
    zone_specs = (
        ("head", "head", 947000, 0.18, 0.00, 0.82, 0.46, 0.46),
        ("torso", "torso", 947001, 0.27, 0.34, 0.73, 0.98, 0.32),
        ("left_arm", "left_arm", 947002, 0.00, 0.08, 0.40, 0.88, 0.40),
        ("right_arm", "right_arm", 947003, 0.60, 0.08, 1.00, 0.88, 0.40),
    )
    anchors: list[Shape] = []
    anchor_masks: list[np.ndarray] = []
    outside_weighted = 0.0
    outside_pixels = 0
    head_color: tuple[int, int, int] | None = None
    for zone_name, character_part, shape_id, x0r, y0r, x1r, y1r, outside_limit in zone_specs:
        rect = _bounded_rect(bbox, width, height, x0r, y0r, x1r, y1r)
        polygon, component, outside_ratio = _simplified_component_polygon(
            mask,
            rect,
            min_pixels=min_pixels,
            max_vertices=10 if zone_name == "head" else 8,
            max_outside_ratio=outside_limit,
        )
        if polygon is None or component is None:
            continue
        color_pixels = _role_color_pixels(rgb, component, bbox, zone_name)
        if zone_name == "torso":
            color = _torso_identity_color(color_pixels, segmentation.background_rgb)
        elif zone_name in {"left_arm", "right_arm"}:
            color = _arm_identity_color(color_pixels, segmentation.background_rgb, head_color)
        else:
            color = _dominant_source_color(color_pixels, segmentation.background_rgb)
        if zone_name == "head":
            head_color = color
        anchor = Shape(
            id=shape_id,
            shape_type="polygon",
            fill_color=color,
            points=[(float(x), float(y)) for x, y in polygon],
            z_index=19950 + len(anchors),
            importance=1.0,
            source_role=f"phase15_macro_{zone_name}_anchor",
            layer_name="foreground",
            semantic_type=f"character_{zone_name}_macro_anchor",
            character_part=character_part,
            part_confidence=max(0.70, min(0.98, float(segmentation.confidence) + 0.20)),
            side_hint="left" if zone_name == "left_arm" else "right" if zone_name == "right_arm" else "unknown",
        )
        anchors.append(anchor)
        polygon_mask = np.zeros_like(mask, dtype=np.uint8)
        cv2.fillPoly(polygon_mask, [np.round(polygon).astype(np.int32)], 1)
        anchor_masks.append(polygon_mask)
        pixels = int(polygon_mask.sum())
        outside_weighted += outside_ratio * pixels
        outside_pixels += pixels

    head_count = sum(shape.character_part == "head" for shape in anchors)
    torso_count = sum(shape.character_part == "torso" for shape in anchors)
    arm_count = sum(shape.character_part in {"left_arm", "right_arm"} for shape in anchors)
    if head_count < 1 or torso_count < 1:
        return MacroSubjectGuardResult(
            False,
            "required_macro_anchor_missing",
            subject_bbox=bbox,
            subject_area_ratio=subject_area_ratio,
            head_anchor_count=head_count,
            torso_anchor_count=torso_count,
            arm_anchor_count=arm_count,
        )

    combined = np.zeros_like(mask, dtype=np.uint8)
    for anchor_mask in anchor_masks:
        combined |= anchor_mask
    subject_pixels = max(int(mask.sum()), 1)
    coverage_ratio = int((combined & mask).sum()) / subject_pixels
    outside_ratio = outside_weighted / max(outside_pixels, 1)
    if coverage_ratio < 0.28:
        return MacroSubjectGuardResult(
            False,
            "macro_coverage_gate",
            subject_bbox=bbox,
            subject_area_ratio=subject_area_ratio,
            subject_coverage_ratio=coverage_ratio,
            outside_subject_ratio=outside_ratio,
            head_anchor_count=head_count,
            torso_anchor_count=torso_count,
            arm_anchor_count=arm_count,
        )

    return MacroSubjectGuardResult(
        True,
        "macro_subject_anchors",
        shapes=tuple(anchors),
        subject_bbox=bbox,
        subject_area_ratio=subject_area_ratio,
        subject_coverage_ratio=coverage_ratio,
        outside_subject_ratio=outside_ratio,
        head_anchor_count=head_count,
        torso_anchor_count=torso_count,
        arm_anchor_count=arm_count,
    )



def _mask_border_leak(mask: np.ndarray) -> float:
    edge = np.concatenate([mask[0, :], mask[-1, :], mask[:, 0], mask[:, -1]])
    return float(edge.mean()) if edge.size else 1.0


def _candidate_from_opaque_rescue(rescue: OpaqueSubjectRescue) -> SubjectSegmentation | None:
    if not rescue.enabled or rescue.rgba is None:
        return None
    mask = (rescue.rgba[:, :, 3] >= 128).astype(np.uint8)
    if int(mask.sum()) < 64:
        return None
    leak = _mask_border_leak(mask)
    confidence = float(np.clip(
        0.40 * float(rescue.border_dominant_fraction)
        + 0.38 * min(float(rescue.center_fill_ratio) / 0.85, 1.0)
        + 0.22 * (1.0 - min(leak / 0.45, 1.0)),
        0.0,
        1.0,
    ))
    return SubjectSegmentation(
        False,
        "phase15_opaque_rescue",
        rgba=rescue.rgba,
        mask=mask,
        background_rgb=rescue.background_rgb,
        border_dominant_fraction=float(rescue.border_dominant_fraction),
        foreground_area_ratio=float(mask.mean()),
        center_fill_ratio=float(rescue.center_fill_ratio),
        border_leak_ratio=leak,
        confidence=confidence,
    )


def _relaxed_border_candidate(image_or_path, existing: SubjectSegmentation) -> SubjectSegmentation | None:
    if existing.reason != "border_gate" or float(existing.border_dominant_fraction) < 0.18:
        return None
    if isinstance(image_or_path, (str, Path)):
        data = load_image_data(image_or_path)
        rgb, alpha = data.rgb, data.alpha
    else:
        arr = np.asarray(image_or_path)
        if arr.ndim != 3 or arr.shape[2] not in {3, 4}:
            return None
        rgb = arr[:, :, :3].astype(np.uint8, copy=False)
        alpha = arr[:, :, 3] if arr.shape[2] == 4 else None
    height, width = rgb.shape[:2]
    aspect = min(height, width) / max(float(max(height, width)), 1.0)
    if aspect < 0.90:
        return None
    if alpha is not None and bool(np.any(alpha < 250)):
        transparent_fraction = float((alpha < 250).mean())
        # Small anti-aliased/transparent border specks are common in otherwise
        # opaque portrait thumbnails. They should not disable the relaxed
        # border recovery path, but genuinely alpha-cut subjects stay out.
        if transparent_fraction > 0.02:
            return None

    border_width = max(2, int(round(min(height, width) * 0.04)))
    border = np.concatenate([
        rgb[:border_width].reshape(-1, 3),
        rgb[height-border_width:].reshape(-1, 3),
        rgb[border_width:height-border_width, :border_width].reshape(-1, 3),
        rgb[border_width:height-border_width, width-border_width:].reshape(-1, 3),
    ])
    bins = (border // 24).astype(np.int16)
    keys = bins[:, 0] * 121 + bins[:, 1] * 11 + bins[:, 2]
    values, counts = np.unique(keys, return_counts=True)
    order = np.argsort(counts)[::-1]
    labs: list[np.ndarray] = []
    colors: list[tuple[int, int, int]] = []
    total = max(len(border), 1)
    for idx in order[:10]:
        fraction = float(counts[idx]) / float(total)
        if fraction < 0.025:
            continue
        selected = border[keys == values[idx]]
        color = np.median(selected, axis=0).astype(np.uint8)
        labs.append(cv2.cvtColor(color.reshape(1, 1, 3), cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0])
        colors.append(tuple(int(v) for v in color))
    if len(labs) < 2:
        return None

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    centers = np.stack(labs)
    distance = np.linalg.norm(lab[:, :, None, :] - centers[None, None, :, :], axis=3).min(axis=2)
    background_candidate = (distance <= 26.0).astype(np.uint8)
    if alpha is not None:
        background_candidate[alpha < 128] = 1
    count, labels, _, _ = cv2.connectedComponentsWithStats(background_candidate, 8)
    if count <= 1:
        return None
    edge_labels = np.unique(np.concatenate([labels[0, :], labels[-1, :], labels[:, 0], labels[:, -1]]))
    edge_labels = edge_labels[edge_labels != 0]
    background = np.isin(labels, edge_labels).astype(np.uint8)
    subject = (1 - background).astype(np.uint8)
    if alpha is not None:
        subject[alpha < 16] = 0
    close_k = max(3, int(round(min(height, width) * 0.010)))
    if close_k % 2 == 0:
        close_k += 1
    subject = cv2.morphologyEx(subject, cv2.MORPH_CLOSE, np.ones((close_k, close_k), np.uint8))
    subject = cv2.morphologyEx(subject, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    area = float(subject.mean())
    center = subject[int(height*0.20):int(height*0.80), int(width*0.20):int(width*0.80)]
    center_fill = float(center.mean()) if center.size else 0.0
    leak = _mask_border_leak(subject)
    if not 0.20 <= area <= 0.72 or center_fill < 0.32 or leak > 0.38:
        return None
    confidence = float(np.clip(
        0.30 * min(float(existing.border_dominant_fraction) / 0.30, 1.0)
        + 0.42 * min(center_fill / 0.80, 1.0)
        + 0.28 * (1.0 - min(leak / 0.45, 1.0)),
        0.0,
        1.0,
    ))
    rgba = np.dstack([rgb, subject * 255]).astype(np.uint8)
    return SubjectSegmentation(
        False,
        "phase15_relaxed_border",
        rgba=rgba,
        mask=subject,
        background_rgb=colors[0],
        border_dominant_fraction=float(existing.border_dominant_fraction),
        foreground_area_ratio=area,
        center_fill_ratio=center_fill,
        border_leak_ratio=leak,
        confidence=confidence,
    )


def phase15_subject_candidate(
    image_or_path,
    segmentation: SubjectSegmentation,
    rescue: OpaqueSubjectRescue,
) -> SubjectSegmentation:
    """Return the strongest accepted or safely recovered deterministic portrait mask.

    A rejected Phase 10 candidate may still carry RGBA/mask data for later rescue.
    Presence of those arrays must not outrank an actually accepted opaque rescue,
    otherwise a confidence-gated mask can become the final portrait mask.
    """
    if segmentation.enabled and segmentation.rgba is not None and segmentation.mask is not None:
        return segmentation
    rescue_candidate = _candidate_from_opaque_rescue(rescue)
    if rescue_candidate is not None:
        rescue_usable = (
            0.18 <= float(rescue_candidate.foreground_area_ratio) <= 0.82
            and float(rescue_candidate.center_fill_ratio) >= 0.35
            and float(rescue_candidate.border_leak_ratio) <= 0.56
            and float(rescue_candidate.confidence) >= 0.42
        )
        if rescue_usable:
            return rescue_candidate
    relaxed = _relaxed_border_candidate(image_or_path, segmentation)
    if relaxed is not None:
        return relaxed
    if segmentation.rgba is not None and segmentation.mask is not None:
        return segmentation
    return segmentation
