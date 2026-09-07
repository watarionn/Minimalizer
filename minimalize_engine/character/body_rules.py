from __future__ import annotations

from dataclasses import dataclass
import math

import cv2
import numpy as np

from ..models import Shape
from .models import CharacterPartCandidate, CharacterStructure
from .part_types import CharacterPartType


@dataclass
class LimbPrimitiveDescriptor:
    part_type: CharacterPartType
    side: str
    proximal: tuple[float, float]
    bend: tuple[float, float]
    distal: tuple[float, float]
    proximal_width: float
    distal_width: float
    bend_angle_deg: float
    confidence: float

    def to_dict(self) -> dict:
        return {
            "part_type": str(self.part_type),
            "side": self.side,
            "proximal": list(self.proximal),
            "bend": list(self.bend),
            "distal": list(self.distal),
            "proximal_width": self.proximal_width,
            "distal_width": self.distal_width,
            "bend_angle_deg": self.bend_angle_deg,
            "confidence": self.confidence,
        }


@dataclass
class CharacterBodyAnalysis:
    torso_points: list[tuple[float, float]]
    limbs: list[LimbPrimitiveDescriptor]
    confidence: float

    def to_dict(self) -> dict:
        return {
            "torso_points": [list(p) for p in self.torso_points],
            "limbs": [l.to_dict() for l in self.limbs],
            "confidence": self.confidence,
        }


def _dominant_color(
    image_rgb: np.ndarray,
    mask: np.ndarray,
    fallback=(105, 100, 112),
) -> tuple[int, int, int]:
    pixels = image_rgb[mask > 0]
    if len(pixels) < 8:
        return tuple(fallback)
    lum = pixels.astype(np.float32) @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    lo, hi = np.percentile(lum, [12, 88])
    core = pixels[(lum >= lo) & (lum <= hi)]
    if len(core) < 8:
        core = pixels
    med = np.median(core.astype(np.float32), axis=0)
    return tuple(int(np.clip(round(v), 0, 255)) for v in med)


def _torso_polygon(part: CharacterPartCandidate) -> list[tuple[float, float]]:
    mask = part.mask > 0
    ys, xs = np.nonzero(mask)
    if len(xs) < 8:
        x, y, w, h = part.bbox
        return [
            (x + w * 0.20, y),
            (x + w * 0.80, y),
            (x + w * 0.92, y + h * 0.45),
            (x + w * 0.72, y + h),
            (x + w * 0.28, y + h),
            (x + w * 0.08, y + h * 0.45),
        ]

    y_min, y_max = float(ys.min()), float(ys.max())
    bands = [
        (0.05, 0.25),
        (0.38, 0.62),
        (0.76, 0.96),
    ]
    extents = []
    for a, b in bands:
        ya = y_min + (y_max - y_min) * a
        yb = y_min + (y_max - y_min) * b
        select = (ys >= ya) & (ys <= yb)
        bx = xs[select]
        by = ys[select]
        if len(bx) < 4:
            extents.append(None)
            continue
        extents.append((
            float(np.percentile(bx, 8)),
            float(np.percentile(bx, 92)),
            float(np.median(by)),
        ))

    x, y, w, h = part.bbox
    fallback = [
        (x + w * 0.18, x + w * 0.82, y + h * 0.14),
        (x + w * 0.10, x + w * 0.90, y + h * 0.50),
        (x + w * 0.26, x + w * 0.74, y + h * 0.90),
    ]
    extents = [e if e is not None else fallback[i] for i, e in enumerate(extents)]
    top, mid, bottom = extents
    return [
        (top[0], top[2]),
        (top[1], top[2]),
        (mid[1], mid[2]),
        (bottom[1], bottom[2]),
        (bottom[0], bottom[2]),
        (mid[0], mid[2]),
    ]


def _pca_limb_descriptor(
    part: CharacterPartCandidate,
    torso_center: tuple[float, float],
) -> LimbPrimitiveDescriptor | None:
    ys, xs = np.nonzero(part.mask > 0)
    if len(xs) < 10:
        return None

    pts = np.column_stack([xs.astype(np.float32), ys.astype(np.float32)])
    mean = pts.mean(axis=0)
    centered = pts - mean
    cov = np.cov(centered, rowvar=False)
    try:
        vals, vecs = np.linalg.eigh(cov)
    except np.linalg.LinAlgError:
        return None
    axis = vecs[:, int(np.argmax(vals))]
    axis = axis / max(np.linalg.norm(axis), 1e-6)
    perp = np.array([-axis[1], axis[0]], dtype=np.float32)

    proj = centered @ axis
    p10, p50, p90 = np.percentile(proj, [8, 50, 92])

    def center_at(q: float, width_ratio: float = 0.14):
        spread = max(1.0, (p90 - p10) * width_ratio)
        select = np.abs(proj - q) <= spread
        if np.count_nonzero(select) >= 4:
            return pts[select].mean(axis=0)
        return mean + axis * q

    a = center_at(float(p10))
    b = center_at(float(p90))
    mid = center_at(float(p50), 0.18)

    # The endpoint nearer the torso is proximal.
    da = float(np.linalg.norm(a - np.asarray(torso_center)))
    db = float(np.linalg.norm(b - np.asarray(torso_center)))
    if db < da:
        a, b = b, a

    # Pull the bend toward actual mid-slice pixels. This helps bent arms.
    length = max(1.0, float(np.linalg.norm(b - a)))
    widths = centered @ perp
    base_width = max(1.5, float(np.percentile(np.abs(widths), 82)) * 2.0)

    # Estimate proximal/distal widths from local perpendicular spread.
    global_proj = (pts - mean) @ axis
    q_a = float((a - mean) @ axis)
    q_b = float((b - mean) @ axis)

    def local_width(q):
        select = np.abs(global_proj - q) <= max(2.0, length * 0.14)
        local = pts[select]
        if len(local) < 5:
            return base_width
        local_perp = (local - local.mean(axis=0)) @ perp
        return max(1.5, float(np.percentile(np.abs(local_perp), 84)) * 2.0)

    wa = local_width(q_a)
    wb = local_width(q_b)
    # Human-like big Shapes taper mildly toward hands/feet.
    proximal_width = max(wa, wb * 0.88)
    distal_width = min(wb, proximal_width * 0.86)
    if part.part_type in {CharacterPartType.LEFT_LEG, CharacterPartType.RIGHT_LEG}:
        distal_width = max(distal_width, proximal_width * 0.55)

    v1 = mid - a
    v2 = b - mid
    n1 = max(float(np.linalg.norm(v1)), 1e-6)
    n2 = max(float(np.linalg.norm(v2)), 1e-6)
    cosang = float(np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0))
    bend_angle = float(math.degrees(math.acos(cosang)))

    return LimbPrimitiveDescriptor(
        part_type=part.part_type,
        side=part.side,
        proximal=(float(a[0]), float(a[1])),
        bend=(float(mid[0]), float(mid[1])),
        distal=(float(b[0]), float(b[1])),
        proximal_width=float(np.clip(proximal_width, 2.0, max(part.bbox[2], part.bbox[3]) * 0.55)),
        distal_width=float(np.clip(distal_width, 1.6, max(part.bbox[2], part.bbox[3]) * 0.45)),
        bend_angle_deg=bend_angle,
        confidence=part.confidence,
    )


def analyze_body_primitives(
    structure: CharacterStructure,
) -> CharacterBodyAnalysis:
    torso = structure.first_part(CharacterPartType.TORSO)
    torso_points = _torso_polygon(torso) if torso is not None else []
    torso_center = torso.centroid if torso is not None else (
        structure.subject_bbox[0] + structure.subject_bbox[2] / 2.0,
        structure.subject_bbox[1] + structure.subject_bbox[3] * 0.42,
    )

    limbs = []
    for part_type in [
        CharacterPartType.LEFT_ARM,
        CharacterPartType.RIGHT_ARM,
        CharacterPartType.LEFT_LEG,
        CharacterPartType.RIGHT_LEG,
    ]:
        part = structure.first_part(part_type)
        if part is None:
            continue
        desc = _pca_limb_descriptor(part, torso_center)
        if desc is not None:
            limbs.append(desc)

    scores = []
    if torso is not None:
        scores.append(torso.confidence)
    scores.extend(l.confidence for l in limbs)
    confidence = float(np.mean(scores)) if scores else 0.0
    return CharacterBodyAnalysis(
        torso_points=torso_points,
        limbs=limbs,
        confidence=confidence,
    )


def _segment_polygon(
    a: np.ndarray,
    b: np.ndarray,
    width_a: float,
    width_b: float,
) -> list[tuple[float, float]]:
    v = b - a
    norm = max(float(np.linalg.norm(v)), 1e-6)
    perp = np.array([-v[1], v[0]], dtype=np.float32) / norm
    p1 = a + perp * width_a * 0.5
    p2 = b + perp * width_b * 0.5
    p3 = b - perp * width_b * 0.5
    p4 = a - perp * width_a * 0.5
    return [
        (float(p1[0]), float(p1[1])),
        (float(p2[0]), float(p2[1])),
        (float(p3[0]), float(p3[1])),
        (float(p4[0]), float(p4[1])),
    ]


def _polyline_body_polygon(
    desc: LimbPrimitiveDescriptor,
    width_scale: float = 1.0,
) -> list[tuple[float, float]]:
    a = np.asarray(desc.proximal, dtype=np.float32)
    m = np.asarray(desc.bend, dtype=np.float32)
    b = np.asarray(desc.distal, dtype=np.float32)

    v1 = m - a
    v2 = b - m
    n1 = max(float(np.linalg.norm(v1)), 1e-6)
    n2 = max(float(np.linalg.norm(v2)), 1e-6)
    p1 = np.array([-v1[1], v1[0]], dtype=np.float32) / n1
    p2 = np.array([-v2[1], v2[0]], dtype=np.float32) / n2
    pm = p1 + p2
    if np.linalg.norm(pm) < 1e-5:
        pm = p1
    pm = pm / max(float(np.linalg.norm(pm)), 1e-6)

    width_scale = float(np.clip(width_scale, 0.55, 1.25))
    wp = desc.proximal_width * 0.5 * width_scale
    wm = (
        desc.proximal_width * 0.56
        + desc.distal_width * 0.44
    ) * 0.5 * width_scale
    wd = desc.distal_width * 0.5 * width_scale

    left = [a + p1 * wp, m + pm * wm, b + p2 * wd]
    right = [b - p2 * wd, m - pm * wm, a - p1 * wp]
    return [(float(p[0]), float(p[1])) for p in left + right]


def _part_color(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
    part_type: CharacterPartType,
) -> tuple[int, int, int]:
    part = structure.first_part(part_type)
    if part is None:
        return (105, 100, 112)
    return _dominant_color(image_rgb, part.mask)



def _clip_primitive_to_part(
    points: list[tuple[float, float]],
    part: CharacterPartCandidate,
    *,
    max_vertices: int = 8,
) -> list[tuple[float, float]]:
    """
    Keep the idealized limb primitive close to its observed part mask.

    A tiny dilation allows deliberate simplification while preventing a wide
    capsule from spilling far outside the source silhouette.
    """
    if len(points) < 3:
        return points

    mask = np.zeros_like(part.mask, dtype=np.uint8)
    pts = np.asarray(points, dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)

    scale = max(1, int(round(min(part.mask.shape[:2]) * 0.003)))
    k = scale * 2 + 1
    allowed = cv2.dilate(
        (part.mask > 0).astype(np.uint8) * 255,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)),
    )
    clipped = cv2.bitwise_and(mask, allowed)
    if np.count_nonzero(clipped) < 6:
        return points

    contours, _ = cv2.findContours(
        clipped,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    contours = list(contours)
    if not contours:
        return points

    contour = max(contours, key=cv2.contourArea)
    peri = max(1.0, float(cv2.arcLength(contour, True)))
    eps = peri * 0.018
    approx = cv2.approxPolyDP(contour, eps, True)
    while len(approx) > max_vertices and eps < peri * 0.075:
        eps *= 1.18
        approx = cv2.approxPolyDP(contour, eps, True)

    if len(approx) < 3:
        return points
    return [
        (float(p[0][0]), float(p[0][1]))
        for p in approx
    ]

def build_body_shapes(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
    analysis: CharacterBodyAnalysis,
    budget: int,
    *,
    start_id: int,
    limb_width_scale: float = 1.0,
) -> list[Shape]:
    if budget <= 0:
        return []

    out: list[Shape] = []
    sid = start_id
    torso = structure.first_part(CharacterPartType.TORSO)

    if torso is not None and len(analysis.torso_points) >= 4 and len(out) < budget:
        out.append(
            Shape(
                id=sid,
                shape_type="polygon",
                fill_color=_part_color(image_rgb, structure, CharacterPartType.TORSO),
                points=analysis.torso_points,
                source_role="character_torso_base",
                layer_name="character_body_base",
                semantic_type="character_torso",
                character_part="torso",
                part_confidence=torso.confidence,
                side_hint="center",
                importance=1.0,
            )
        )
        sid += 1

    # Prefer having one readable primitive for every detected limb.
    priority = {
        CharacterPartType.LEFT_ARM: 0,
        CharacterPartType.RIGHT_ARM: 1,
        CharacterPartType.LEFT_LEG: 2,
        CharacterPartType.RIGHT_LEG: 3,
    }
    limbs = sorted(
        analysis.limbs,
        key=lambda d: (priority.get(d.part_type, 9), -d.confidence),
    )

    for desc in limbs:
        if len(out) >= budget:
            break
        color = _part_color(image_rgb, structure, desc.part_type)
        points = _polyline_body_polygon(
            desc,
            width_scale=limb_width_scale,
        )
        part = structure.first_part(desc.part_type)
        if part is not None:
            points = _clip_primitive_to_part(points, part)
        out.append(
            Shape(
                id=sid,
                shape_type="polygon",
                fill_color=color,
                points=points,
                source_role="character_limb_base",
                layer_name="character_body_base",
                semantic_type=f"character_{str(desc.part_type)}",
                character_part=str(desc.part_type),
                part_confidence=desc.confidence,
                side_hint=desc.side,
                importance=0.99,
            )
        )
        sid += 1

    return out[:budget]


def expected_body_shape_count(
    structure: CharacterStructure,
    budget_per_part: dict,
) -> int:
    count = 0
    if structure.first_part(CharacterPartType.TORSO) is not None:
        count += min(1, int(budget_per_part.get(CharacterPartType.TORSO, 0)))
    for t in [
        CharacterPartType.LEFT_ARM,
        CharacterPartType.RIGHT_ARM,
        CharacterPartType.LEFT_LEG,
        CharacterPartType.RIGHT_LEG,
    ]:
        if structure.first_part(t) is not None:
            count += min(1, int(budget_per_part.get(t, 0)))
    return count
