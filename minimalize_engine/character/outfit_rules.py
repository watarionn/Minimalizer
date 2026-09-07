from __future__ import annotations

from dataclasses import dataclass, field
import colorsys

import cv2
import numpy as np

from ..models import Region, Shape
from .models import CharacterPartCandidate, CharacterStructure
from .part_types import CharacterPartType
from .heuristics import mask_bbox, mask_centroid


@dataclass
class OutfitStructure:
    torso_mask: np.ndarray | None
    left_sleeve_mask: np.ndarray | None
    right_sleeve_mask: np.ndarray | None
    lower_mask: np.ndarray | None
    left_shoe_mask: np.ndarray | None
    right_shoe_mask: np.ndarray | None
    lower_type: str = "none"
    accessory_region_ids: list[int] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict:
        def desc(mask):
            if mask is None or not np.any(mask > 0):
                return None
            return {
                "bbox": list(mask_bbox(mask)),
                "centroid": list(mask_centroid(mask)),
                "area": int(np.count_nonzero(mask)),
            }

        return {
            "torso": desc(self.torso_mask),
            "left_sleeve": desc(self.left_sleeve_mask),
            "right_sleeve": desc(self.right_sleeve_mask),
            "lower": desc(self.lower_mask),
            "left_shoe": desc(self.left_shoe_mask),
            "right_shoe": desc(self.right_shoe_mask),
            "lower_type": self.lower_type,
            "accessory_region_ids": list(self.accessory_region_ids),
            "confidence": self.confidence,
        }


def _zone_mask(base: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = bbox
    out = np.zeros_like(base, dtype=np.uint8)
    out[y:y+h, x:x+w] = base[y:y+h, x:x+w]
    return out


def _largest_component(mask: np.ndarray, min_area: int = 8) -> np.ndarray | None:
    binary = (mask > 0).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    ids = [i for i in range(1, n) if int(stats[i, cv2.CC_STAT_AREA]) >= min_area]
    if not ids:
        return None
    cid = max(ids, key=lambda i: int(stats[i, cv2.CC_STAT_AREA]))
    return (labels == cid).astype(np.uint8) * 255


def _clean(mask: np.ndarray | None, scale: float = 0.008) -> np.ndarray | None:
    if mask is None or not np.any(mask > 0):
        return None
    h, w = mask.shape[:2]
    k = max(3, int(round(min(h, w) * scale)) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    out = cv2.morphologyEx((mask > 0).astype(np.uint8) * 255, cv2.MORPH_CLOSE, kernel)
    out = cv2.morphologyEx(out, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return _largest_component(out, min_area=max(6, int(mask.size * 0.0003)))


def _proximal_limb_mask(
    part: CharacterPartCandidate | None,
    torso_center: tuple[float, float],
    keep_ratio: float = 0.58,
) -> np.ndarray | None:
    if part is None or not np.any(part.mask > 0):
        return None
    ys, xs = np.nonzero(part.mask > 0)
    if len(xs) < 8:
        return None
    tx, ty = torso_center
    dist = np.sqrt((xs.astype(np.float32) - tx) ** 2 + (ys.astype(np.float32) - ty) ** 2)
    threshold = float(np.quantile(dist, np.clip(keep_ratio, 0.25, 0.85)))
    keep = dist <= threshold
    out = np.zeros_like(part.mask, dtype=np.uint8)
    out[ys[keep], xs[keep]] = 255
    return _clean(out, 0.006)


def _shoe_mask(
    subject_mask: np.ndarray,
    subject_bbox: tuple[int, int, int, int],
    axis_x: float,
    side: str,
) -> np.ndarray | None:
    sx, sy, sw, sh = subject_bbox
    h, w = subject_mask.shape[:2]
    y0 = max(sy, int(round(sy + sh * 0.855)))
    y1 = min(h, sy + sh)
    out = np.zeros_like(subject_mask, dtype=np.uint8)
    if side == "left":
        x0, x1 = sx, min(w, int(round(axis_x + sw * 0.04)))
    else:
        x0, x1 = max(0, int(round(axis_x - sw * 0.04))), min(w, sx + sw)
    if x1 <= x0 or y1 <= y0:
        return None
    out[y0:y1, x0:x1] = subject_mask[y0:y1, x0:x1]
    return _clean(out, 0.004)




def _is_skin_rgb(rgb: tuple[int, int, int]) -> bool:
    arr = np.asarray([[list(rgb)]], dtype=np.uint8)
    ycc = cv2.cvtColor(arr, cv2.COLOR_RGB2YCrCb)[0, 0]
    r, g, b = [int(v) for v in rgb]
    cr, cb = int(ycc[1]), int(ycc[2])
    return (
        132 <= cr <= 190
        and 70 <= cb <= 138
        and r >= 140
        and g >= 75
        and b >= 60
        and r >= b + 4
    )


def _region_driven_outfit_mask(
    regions: list[Region],
    zone_mask: np.ndarray,
) -> np.ndarray | None:
    zone = zone_mask > 0
    zone_area = max(1, int(np.count_nonzero(zone)))
    ranked = []
    for r in regions:
        if _is_skin_rgb(r.color_rgb):
            continue
        rm = r.mask > 0
        inter = int(np.count_nonzero(rm & zone))
        if inter <= 0:
            continue
        overlap = inter / max(1, r.area)
        zone_share = inter / zone_area
        if overlap < 0.16 and zone_share < 0.035:
            continue
        # Prefer structurally important regions, but do not require high
        # saturation because many outfits are black/white/gray.
        lum = (0.299 * r.color_rgb[0] + 0.587 * r.color_rgb[1] + 0.114 * r.color_rgb[2]) / 255.0
        contrast_bonus = abs(lum - 0.72)
        score = inter * (0.75 + r.importance_score * 0.20 + contrast_bonus * 0.15)
        ranked.append((score, r, inter))

    if not ranked:
        return None
    ranked.sort(key=lambda x: x[0], reverse=True)
    out = np.zeros_like(zone_mask, dtype=np.uint8)
    covered = 0
    for _, r, inter in ranked[:6]:
        piece = cv2.bitwise_and((r.mask > 0).astype(np.uint8) * 255, zone_mask)
        out = cv2.bitwise_or(out, piece)
        covered += inter
        if covered >= zone_area * 0.52:
            break

    if np.count_nonzero(out) < zone_area * 0.04:
        return None
    return _clean(out, 0.004)

def _saturation(rgb: tuple[int, int, int]) -> float:
    r, g, b = [v / 255.0 for v in rgb]
    return colorsys.rgb_to_hsv(r, g, b)[1]


def _accessory_region_ids(
    regions: list[Region],
    outfit_mask: np.ndarray,
    image_area: int,
    limit: int = 4,
) -> list[int]:
    target = outfit_mask > 0
    ranked = []
    h, w = outfit_mask.shape[:2]
    for r in regions:
        if r.area <= 0:
            continue
        if _is_skin_rgb(r.color_rgb):
            continue
        ar = r.area / max(1, image_area)
        if not (0.00012 <= ar <= 0.006):
            continue
        bx, by, bw, bh = r.bbox
        bbox_area = max(1, bw * bh)
        fill = r.area / bbox_area
        if bbox_area / max(1, image_area) > 0.018 or fill < 0.10:
            continue
        if bw > w * 0.24 or bh > h * 0.18:
            continue
        rm = r.mask > 0
        overlap = np.count_nonzero(rm & target) / max(1, r.area)
        if overlap < 0.45:
            continue
        sat = _saturation(r.color_rgb)
        score = r.importance_score * 0.50 + sat * 0.32 + min(1.0, overlap) * 0.18
        if r.is_accent:
            score += 0.12
        ranked.append((score, r.id))
    ranked.sort(reverse=True)
    return [rid for _, rid in ranked[:limit]]


def analyze_outfit_structure(
    structure: CharacterStructure,
    regions: list[Region],
) -> OutfitStructure:
    subject = structure.subject_mask
    sx, sy, sw, sh = structure.subject_bbox
    axis = float(structure.metadata.get("body_axis_x", sx + sw / 2.0))
    image_area = subject.size

    torso_part = structure.first_part(CharacterPartType.TORSO)
    outfit_part = structure.first_part(CharacterPartType.OUTFIT)
    left_arm = structure.first_part(CharacterPartType.LEFT_ARM)
    right_arm = structure.first_part(CharacterPartType.RIGHT_ARM)

    if torso_part is not None:
        torso_mask = torso_part.mask.copy()
        torso_bbox = torso_part.bbox
        torso_center = torso_part.centroid
    elif outfit_part is not None:
        torso_mask = outfit_part.mask.copy()
        torso_bbox = outfit_part.bbox
        torso_center = outfit_part.centroid
    else:
        torso_bbox = (
            int(round(axis - sw * 0.24)),
            int(round(sy + sh * 0.22)),
            int(round(sw * 0.48)),
            int(round(sh * 0.36)),
        )
        torso_mask = _zone_mask(subject, torso_bbox)
        torso_center = mask_centroid(torso_mask)

    torso_mask = _clean(torso_mask, 0.006)

    left_sleeve = _proximal_limb_mask(left_arm, torso_center)
    right_sleeve = _proximal_limb_mask(right_arm, torso_center)

    tx, ty, tw, th = torso_bbox
    lower_y0 = max(sy, int(round(ty + th * 0.28)))
    lower_y1 = min(sy + sh, int(round(sy + sh * 0.79)))
    if outfit_part is not None:
        ox, oy, ow, oh = outfit_part.bbox
        # The broad alpha-based outfit proposal gives a useful lower boundary.
        # Without this clamp, bare legs are easily swallowed into a giant
        # "lower outfit" polygon.
        lower_y1 = min(lower_y1, oy + oh)
    lower_x0 = max(sx, int(round(axis - sw * 0.34)))
    lower_x1 = min(sx + sw, int(round(axis + sw * 0.34)))
    lower = np.zeros_like(subject, dtype=np.uint8)
    if lower_y1 > lower_y0 and lower_x1 > lower_x0:
        lower[lower_y0:lower_y1, lower_x0:lower_x1] = subject[lower_y0:lower_y1, lower_x0:lower_x1]
    lower_region_mask = _region_driven_outfit_mask(regions, lower)
    lower = lower_region_mask

    lower_type = "none"
    if lower is not None:
        lx, ly, lw, lh = mask_bbox(lower)
        torso_width = max(1, tw)
        width_ratio = lw / torso_width
        height_ratio = lh / max(sh, 1)
        if width_ratio >= 1.18 and height_ratio <= 0.30:
            lower_type = "skirt_like"
        elif width_ratio >= 1.05 and height_ratio > 0.20:
            lower_type = "coat_like"
        elif width_ratio >= 0.62 and height_ratio <= 0.20:
            lower_type = "shorts_like"
        else:
            lower_type = "lower_outfit"

    left_shoe = _shoe_mask(subject, structure.subject_bbox, axis, "left")
    right_shoe = _shoe_mask(subject, structure.subject_bbox, axis, "right")

    outfit_union = np.zeros_like(subject, dtype=np.uint8)
    for m in [torso_mask, left_sleeve, right_sleeve, lower]:
        if m is not None:
            outfit_union = cv2.bitwise_or(outfit_union, m)
    accessory_ids = _accessory_region_ids(regions, outfit_union, image_area)

    components = [m is not None and np.any(m > 0) for m in [torso_mask, left_sleeve, right_sleeve, lower]]
    confidence = 0.38 + sum(components) * 0.11
    if lower_type != "none":
        confidence += 0.08
    if accessory_ids:
        confidence += 0.05

    return OutfitStructure(
        torso_mask=torso_mask,
        left_sleeve_mask=left_sleeve,
        right_sleeve_mask=right_sleeve,
        lower_mask=lower,
        left_shoe_mask=left_shoe,
        right_shoe_mask=right_shoe,
        lower_type=lower_type,
        accessory_region_ids=accessory_ids,
        confidence=float(np.clip(confidence, 0.0, 1.0)),
    )


def _dominant_color(
    image_rgb: np.ndarray,
    mask: np.ndarray | None,
    fallback=(96, 92, 108),
    *,
    avoid_skin: bool = False,
) -> tuple[int, int, int]:
    if mask is None:
        return tuple(fallback)
    pixels = image_rgb[mask > 0]
    if len(pixels) < 8:
        return tuple(fallback)

    if avoid_skin and len(pixels) >= 16:
        px = pixels.reshape(-1, 1, 3).astype(np.uint8)
        ycc = cv2.cvtColor(px, cv2.COLOR_RGB2YCrCb).reshape(-1, 3)
        cr = ycc[:, 1]
        cb = ycc[:, 2]
        r = pixels[:, 0].astype(np.int16)
        g = pixels[:, 1].astype(np.int16)
        b = pixels[:, 2].astype(np.int16)
        skin = (
            (cr >= 132) & (cr <= 190) & (cb >= 70) & (cb <= 138)
            & (r >= 145) & (g >= 80) & (b >= 65)
            & (r >= b + 5)
        )
        non_skin = pixels[~skin]
        if len(non_skin) >= max(8, int(len(pixels) * 0.16)):
            pixels = non_skin

    # Trim luminance extremes so highlights and black line art do not dominate.
    lum = pixels.astype(np.float32) @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    lo, hi = np.percentile(lum, [15, 85])
    core = pixels[(lum >= lo) & (lum <= hi)]
    if len(core) < 8:
        core = pixels
    med = np.median(core.astype(np.float32), axis=0)
    return tuple(int(np.clip(round(v), 0, 255)) for v in med)


def _simplified_polygon(mask: np.ndarray | None, max_vertices: int = 9) -> list[tuple[float, float]]:
    if mask is None or not np.any(mask > 0):
        return []
    contours, _ = cv2.findContours((mask > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(contours)
    if not contours:
        return []
    contour = max(contours, key=cv2.contourArea)
    peri = max(float(cv2.arcLength(contour, True)), 1.0)
    eps = peri * 0.018
    approx = cv2.approxPolyDP(contour, eps, True)
    while len(approx) > max_vertices and eps < peri * 0.08:
        eps *= 1.18
        approx = cv2.approxPolyDP(contour, eps, True)
    return [(float(p[0][0]), float(p[0][1])) for p in approx]


def _trapezoid_from_mask(mask: np.ndarray, *, widen_bottom: float = 0.10) -> list[tuple[float, float]]:
    x, y, w, h = mask_bbox(mask)
    inset_top = w * min(0.26, max(0.04, widen_bottom))
    inset_bottom = w * max(0.02, inset_top / max(w, 1) * 0.25)
    return [
        (x + inset_top, y),
        (x + w - inset_top, y),
        (x + w - inset_bottom, y + h),
        (x + inset_bottom, y + h),
    ]




def _waist_polygon_from_mask(mask: np.ndarray) -> list[tuple[float, float]]:
    """Build a small silhouette grammar for jackets/dresses without tracing detail."""
    x, y, w, h = mask_bbox(mask)
    if w <= 2 or h <= 3:
        return _simplified_polygon(mask)
    binary = mask > 0
    samples = []
    for frac in (0.06, 0.36, 0.62, 0.92):
        yy = min(binary.shape[0] - 1, max(0, int(round(y + h * frac))))
        xs = np.flatnonzero(binary[yy])
        if len(xs) < 2:
            samples.append((x, x + w))
        else:
            samples.append((float(xs.min()), float(xs.max())))
    # Smooth away tiny segmentation dents while preserving a narrow waist.
    left = [v[0] for v in samples]
    right = [v[1] for v in samples]
    center = x + w / 2.0
    min_half = w * 0.20
    pts_left = []
    pts_right = []
    for frac, lx, rx in zip((0.06, 0.36, 0.62, 0.92), left, right):
        half = max(min_half, min(w * 0.50, (rx - lx) / 2.0))
        local_center = float(np.clip((lx + rx) / 2.0, center - w * 0.10, center + w * 0.10))
        yy = y + h * frac
        pts_left.append((local_center - half, yy))
        pts_right.append((local_center + half, yy))
    return [(float(a), float(b)) for a, b in pts_left + list(reversed(pts_right))]

def _shape_from_mask(
    mask: np.ndarray | None,
    image_rgb: np.ndarray,
    sid: int,
    *,
    role: str,
    layer: str,
    part: str = "outfit",
    prefer_trapezoid: bool = False,
    prefer_waist: bool = False,
    confidence: float = 0.75,
) -> Shape | None:
    if mask is None or not np.any(mask > 0):
        return None
    color = _dominant_color(image_rgb, mask, avoid_skin=True)
    if prefer_waist:
        regular = _simplified_polygon(mask)
        waist = _waist_polygon_from_mask(mask)

        def poly_iou(points):
            if len(points) < 3:
                return 0.0
            pm = np.zeros_like(mask, dtype=np.uint8)
            arr = np.asarray(points, dtype=np.float32).round().astype(np.int32)
            cv2.fillPoly(pm, [arr], 255)
            a = mask > 0
            b = pm > 0
            inter = int(np.count_nonzero(a & b))
            union = int(np.count_nonzero(a | b))
            return inter / max(1, union)

        # Only use the stylized waist grammar when the source genuinely has
        # a visible pinch and fidelity stays essentially unchanged. Otherwise
        # keep the regular simplified contour.
        x0, y0, ww, hh = mask_bbox(mask)
        row_widths = []
        for frac in (0.18, 0.45, 0.68, 0.88):
            yy = min(mask.shape[0] - 1, max(0, int(round(y0 + hh * frac))))
            xs = np.flatnonzero(mask[yy] > 0)
            row_widths.append(float(xs.max() - xs.min() + 1) if len(xs) >= 2 else float(ww))
        outer = max(1.0, (row_widths[0] + row_widths[-1]) * 0.5)
        waist_ratio = min(row_widths[1], row_widths[2]) / outer
        regular_iou = poly_iou(regular)
        waist_iou = poly_iou(waist)
        pts = waist if (waist_ratio <= 0.88 and waist_iou >= regular_iou - 0.01) else regular
    else:
        pts = _trapezoid_from_mask(mask, widen_bottom=0.14) if prefer_trapezoid else _simplified_polygon(mask)
    if len(pts) < 3:
        return None
    return Shape(
        id=sid,
        shape_type="polygon",
        fill_color=color,
        points=pts,
        source_role=role,
        layer_name=layer,
        semantic_type=role,
        character_part=part,
        part_confidence=confidence,
        importance=0.98,
    )


def _shoe_shape(
    mask: np.ndarray | None,
    image_rgb: np.ndarray,
    sid: int,
    side: str,
) -> Shape | None:
    if mask is None or not np.any(mask > 0):
        return None
    x, y, w, h = mask_bbox(mask)
    color = _dominant_color(image_rgb, mask, fallback=(70, 68, 75), avoid_skin=True)
    toe = w * 0.18
    pts = [
        (x + toe, y),
        (x + w - toe * 0.25, y + h * 0.12),
        (x + w, y + h * 0.72),
        (x + w * 0.72, y + h),
        (x + w * 0.08, y + h * 0.92),
        (x, y + h * 0.35),
    ]
    return Shape(
        id=sid,
        shape_type="polygon",
        fill_color=color,
        points=[(float(px), float(py)) for px, py in pts],
        source_role="character_shoe",
        layer_name="character_outfit_detail",
        semantic_type="character_shoe",
        character_part="outfit",
        part_confidence=0.62,
        side_hint=side,
        importance=0.92,
    )


def _accessory_shape(
    region: Region,
    sid: int,
) -> Shape | None:
    x, y, w, h = region.bbox
    cx, cy = region.centroid
    aspect = max(w, h) / max(1.0, min(w, h))
    if aspect >= 2.5:
        if w >= h:
            pts = [(x, cy), (x + w, cy)]
        else:
            pts = [(cx, y), (cx, y + h)]
        return Shape(
            id=sid,
            shape_type="line",
            fill_color=None,
            stroke_color=region.color_rgb,
            stroke_width=max(0.8, min(w, h) * 0.32),
            points=[(float(a), float(b)) for a, b in pts],
            source_role="character_outfit_accessory",
            layer_name="character_outfit_accessory",
            semantic_type="character_accessory",
            character_part="outfit",
            part_confidence=0.58,
            importance=0.95,
        )

    if 0.72 <= w / max(h, 1) <= 1.38:
        radius = max(1.0, min(w, h) * 0.34)
        return Shape(
            id=sid,
            shape_type="circle",
            fill_color=region.color_rgb,
            cx=float(cx),
            cy=float(cy),
            rx=float(radius),
            ry=float(radius),
            source_role="character_outfit_accessory",
            layer_name="character_outfit_accessory",
            semantic_type="character_accessory",
            character_part="outfit",
            part_confidence=0.62,
            importance=0.96,
        )

    pts = [
        (cx, y),
        (x + w, cy),
        (cx, y + h),
        (x, cy),
    ]
    return Shape(
        id=sid,
        shape_type="polygon",
        fill_color=region.color_rgb,
        points=[(float(a), float(b)) for a, b in pts],
        source_role="character_outfit_accessory",
        layer_name="character_outfit_accessory",
        semantic_type="character_accessory",
        character_part="outfit",
        part_confidence=0.60,
        importance=0.96,
    )


def build_outfit_shapes(
    outfit: OutfitStructure,
    image_rgb: np.ndarray,
    regions: list[Region],
    budget: int,
    *,
    start_id: int,
) -> list[Shape]:
    if budget <= 0:
        return []

    out: list[Shape] = []
    sid = start_id

    def add(shape):
        nonlocal sid
        if shape is None or len(out) >= budget:
            return
        out.append(shape)
        sid += 1

    add(_shape_from_mask(
        outfit.torso_mask,
        image_rgb,
        sid,
        role="character_outfit_torso",
        layer="character_outfit_base",
        prefer_waist=True,
        confidence=outfit.confidence,
    ))

    if len(out) < budget and outfit.lower_mask is not None:
        add(_shape_from_mask(
            outfit.lower_mask,
            image_rgb,
            sid,
            role=f"character_{outfit.lower_type}",
            layer="character_outfit_base",
            prefer_trapezoid=outfit.lower_type in {"skirt_like", "coat_like", "shorts_like"},
            confidence=max(0.55, outfit.confidence - 0.06),
        ))

    for side, mask in [
        ("left", outfit.left_sleeve_mask),
        ("right", outfit.right_sleeve_mask),
    ]:
        if len(out) >= budget:
            break
        shape = _shape_from_mask(
            mask,
            image_rgb,
            sid,
            role="character_sleeve",
            layer="character_outfit_detail",
            confidence=0.64,
        )
        if shape is not None:
            shape.side_hint = side
        add(shape)

    # Shoes are lower priority than body/sleeves, but valuable in full-body art.
    for side, mask in [
        ("left", outfit.left_shoe_mask),
        ("right", outfit.right_shoe_mask),
    ]:
        if len(out) >= budget:
            break
        add(_shoe_shape(mask, image_rgb, sid, side))

    by_id = {r.id: r for r in regions}
    for rid in outfit.accessory_region_ids:
        if len(out) >= budget:
            break
        region = by_id.get(rid)
        if region is None:
            continue
        add(_accessory_shape(region, sid))

    return out[:budget]
