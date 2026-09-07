from __future__ import annotations

from dataclasses import dataclass
import cv2
import numpy as np

from ..models import Region, Shape
from .models import CharacterPartCandidate


@dataclass
class FaceFeatureLayout:
    face_bbox: tuple[int, int, int, int]
    left_eye: tuple[float, float, float] | None
    right_eye: tuple[float, float, float] | None
    mouth: tuple[float, float, float] | None
    wink_side: str = "unknown"
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "face_bbox": list(self.face_bbox),
            "left_eye": list(self.left_eye) if self.left_eye else None,
            "right_eye": list(self.right_eye) if self.right_eye else None,
            "mouth": list(self.mouth) if self.mouth else None,
            "wink_side": self.wink_side,
            "confidence": self.confidence,
        }


def _crop_bounds(
    bbox: tuple[int, int, int, int],
    image_shape,
) -> tuple[int, int, int, int]:
    h, w = image_shape[:2]
    x, y, bw, bh = bbox
    x0 = max(0, min(w - 1, x))
    y0 = max(0, min(h - 1, y))
    x1 = max(x0 + 1, min(w, x + bw))
    y1 = max(y0 + 1, min(h, y + bh))
    return x0, y0, x1, y1


def _dominant_color(
    image_rgb: np.ndarray,
    mask: np.ndarray,
    fallback=(236, 196, 170),
) -> tuple[int, int, int]:
    pixels = image_rgb[mask > 0]
    if len(pixels) < 6:
        return tuple(int(v) for v in fallback)
    # Median is much more stable than mean when eyes/hair leak into the face mask.
    med = np.median(pixels.astype(np.float32), axis=0)
    return tuple(int(np.clip(round(v), 0, 255)) for v in med)


def _dark_color_from_face(
    image_rgb: np.ndarray,
    face_mask: np.ndarray,
) -> tuple[int, int, int]:
    pixels = image_rgb[face_mask > 0]
    if len(pixels) < 8:
        return (48, 42, 46)
    lum = (
        pixels[:, 0].astype(np.float32) * 0.299
        + pixels[:, 1].astype(np.float32) * 0.587
        + pixels[:, 2].astype(np.float32) * 0.114
    )
    k = max(4, int(len(pixels) * 0.12))
    dark = pixels[np.argsort(lum)[:k]]
    rgb = np.median(dark.astype(np.float32), axis=0)
    # Keep eye/mouth details dark enough even in pastel images.
    if float(np.mean(rgb)) > 115:
        rgb = rgb * 0.55
    return tuple(int(np.clip(round(v), 18, 130)) for v in rgb)


def _component_candidates(
    binary: np.ndarray,
    *,
    x0: int,
    y0: int,
    min_area: int,
    max_area: int,
) -> list[tuple[float, float, float, int, int]]:
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(
        (binary > 0).astype(np.uint8),
        connectivity=8,
    )
    out = []
    for cid in range(1, n):
        area = int(stats[cid, cv2.CC_STAT_AREA])
        if area < min_area or area > max_area:
            continue
        bw = int(stats[cid, cv2.CC_STAT_WIDTH])
        bh = int(stats[cid, cv2.CC_STAT_HEIGHT])
        if bw <= 0 or bh <= 0:
            continue
        compact = min(bw, bh) / max(bw, bh)
        cx, cy = centroids[cid]
        score = float(area) * (0.55 + 0.45 * compact)
        out.append((x0 + float(cx), y0 + float(cy), score, bw, bh))
    return out


def estimate_eye_candidates(
    image_rgb: np.ndarray,
    face_bbox: tuple[int, int, int, int],
    face_mask: np.ndarray | None = None,
) -> list[tuple[float, float, float]]:
    x0, y0, x1, y1 = _crop_bounds(face_bbox, image_rgb.shape)
    crop = image_rgb[y0:y1, x0:x1]
    if crop.size == 0:
        return []

    h, w = crop.shape[:2]
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)

    # Eyes should lie in the upper-middle face band.
    band = np.zeros((h, w), dtype=np.uint8)
    ya = int(round(h * 0.22))
    yb = max(ya + 1, int(round(h * 0.62)))
    xa = int(round(w * 0.07))
    xb = max(xa + 1, int(round(w * 0.93)))
    band[ya:yb, xa:xb] = 255

    if face_mask is not None:
        fm = face_mask[y0:y1, x0:x1]
        if fm.shape == band.shape:
            band = cv2.bitwise_and(band, (fm > 0).astype(np.uint8) * 255)

    valid_gray = gray[band > 0]
    if len(valid_gray) < 8:
        return []

    # Relative threshold handles both dark and brightly colored anime eyes.
    threshold = int(np.clip(np.percentile(valid_gray, 28), 25, 165))
    dark = ((gray <= threshold).astype(np.uint8) * 255)
    dark = cv2.bitwise_and(dark, band)
    dark = cv2.morphologyEx(
        dark,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
    )

    face_area = max(1, (x1 - x0) * (y1 - y0))
    comps = _component_candidates(
        dark,
        x0=x0,
        y0=y0,
        min_area=max(1, int(face_area * 0.0015)),
        max_area=max(3, int(face_area * 0.12)),
    )

    expected_y = y0 + (y1 - y0) * 0.42
    center_x = x0 + (x1 - x0) * 0.50
    ranked = []
    for cx, cy, raw, bw, bh in comps:
        side_dist = abs(cx - center_x) / max((x1 - x0) * 0.5, 1.0)
        if side_dist < 0.08 or side_dist > 0.92:
            continue
        y_dist = abs(cy - expected_y) / max((y1 - y0), 1.0)
        shape_bonus = min(1.0, bw / max(bh, 1))
        score = raw * (1.0 - min(0.75, y_dist * 2.0)) * (0.7 + 0.3 * shape_bonus)
        ranked.append((cx, cy, score))

    ranked.sort(key=lambda t: t[2], reverse=True)
    return ranked[:8]


def _choose_eye_pair(
    candidates: list[tuple[float, float, float]],
    face_bbox: tuple[int, int, int, int],
) -> tuple[
    tuple[float, float, float] | None,
    tuple[float, float, float] | None,
]:
    if not candidates:
        return None, None

    x, y, w, h = face_bbox
    center = x + w / 2.0
    lefts = [c for c in candidates if c[0] < center]
    rights = [c for c in candidates if c[0] >= center]

    best_pair = None
    best_score = -1.0
    for left in lefts[:5]:
        for right in rights[:5]:
            sep = right[0] - left[0]
            if sep < w * 0.20 or sep > w * 0.82:
                continue
            ydiff = abs(left[1] - right[1])
            if ydiff > h * 0.20:
                continue

            symmetry = 1.0 - min(
                1.0,
                abs(((left[0] + right[0]) / 2.0) - center) / max(w * 0.30, 1.0),
            )
            alignment = 1.0 - min(1.0, ydiff / max(h * 0.20, 1.0))
            raw = np.sqrt(max(left[2], 1e-6) * max(right[2], 1e-6))
            score = float(raw * (0.55 + 0.25 * symmetry + 0.20 * alignment))
            if score > best_score:
                best_score = score
                best_pair = (left, right)

    if best_pair is not None:
        a, b = best_pair
        max_raw = max([c[2] for c in candidates] + [1.0])
        ac = float(np.clip(a[2] / max_raw, 0.0, 1.0))
        bc = float(np.clip(b[2] / max_raw, 0.0, 1.0))

        # A very weak "partner" is commonly a hair/eyelash fragment. Mirror the
        # confident eye instead of keeping a random speck. This is geometry-only
        # and still leaves true wink cases available when no partner exists.
        if ac >= 0.55 and bc < 0.18:
            mirrored_x = center + (center - a[0])
            b = (mirrored_x, a[1], a[2] * 0.48)
            bc = 0.48
        elif bc >= 0.55 and ac < 0.18:
            mirrored_x = center - (b[0] - center)
            a = (mirrored_x, b[1], b[2] * 0.48)
            ac = 0.48

        return (
            (a[0], a[1], ac),
            (b[0], b[1], bc),
        )

    # Single-eye fallback supports wink / occluded-eye compositions.
    best = candidates[0]
    confidence = 0.52
    if best[0] < center:
        return (best[0], best[1], confidence), None
    return None, (best[0], best[1], confidence)


def estimate_mouth_candidate(
    image_rgb: np.ndarray,
    face_bbox: tuple[int, int, int, int],
    face_mask: np.ndarray | None = None,
) -> tuple[float, float, float] | None:
    x0, y0, x1, y1 = _crop_bounds(face_bbox, image_rgb.shape)
    crop = image_rgb[y0:y1, x0:x1]
    h, w = crop.shape[:2]
    if h < 4 or w < 4:
        return None

    # Mouth band is narrow and lower-center. Use red saturation first, dark
    # contrast second. This avoids promoting bangs/eyelashes into a mouth.
    ya = int(round(h * 0.54))
    yb = max(ya + 1, int(round(h * 0.86)))
    xa = int(round(w * 0.22))
    xb = max(xa + 1, int(round(w * 0.78)))

    band_rgb = crop[ya:yb, xa:xb]
    hsv = cv2.cvtColor(band_rgb, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(band_rgb, cv2.COLOR_RGB2GRAY)

    red_like = (
        ((hsv[:, :, 0] <= 14) | (hsv[:, :, 0] >= 165))
        & (hsv[:, :, 1] >= 45)
        & (hsv[:, :, 2] >= 45)
    )
    dark_threshold = np.percentile(gray, 22)
    dark_like = gray <= max(35, dark_threshold)

    binary = ((red_like | dark_like).astype(np.uint8) * 255)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    if face_mask is not None:
        fm = face_mask[y0 + ya:y0 + yb, x0 + xa:x0 + xb]
        if fm.shape == binary.shape:
            binary = cv2.bitwise_and(binary, (fm > 0).astype(np.uint8) * 255)

    comps = _component_candidates(
        binary,
        x0=x0 + xa,
        y0=y0 + ya,
        min_area=1,
        max_area=max(3, int((x1 - x0) * (y1 - y0) * 0.08)),
    )
    if not comps:
        return None

    expected_x = (x0 + x1) / 2.0
    expected_y = y0 + (y1 - y0) * 0.70
    ranked = []
    for cx, cy, raw, bw, bh in comps:
        xdist = abs(cx - expected_x) / max((x1 - x0) * 0.5, 1.0)
        ydist = abs(cy - expected_y) / max((y1 - y0), 1.0)
        horizontal = min(1.0, bw / max(bh, 1))
        score = raw * (1.0 - min(0.8, xdist)) * (1.0 - min(0.7, ydist * 2)) * (0.65 + 0.35 * horizontal)
        ranked.append((cx, cy, score))

    ranked.sort(key=lambda t: t[2], reverse=True)
    best = ranked[0]
    max_score = max(r[2] for r in ranked)
    return (
        float(best[0]),
        float(best[1]),
        float(np.clip(best[2] / max(max_score, 1e-6), 0.0, 1.0)),
    )


def analyze_face_layout(
    image_rgb: np.ndarray,
    face: CharacterPartCandidate,
    regions: list[Region] | None = None,
) -> FaceFeatureLayout:
    contour_fit = face.metadata.get("contour_fit") or {}
    raw_search_bbox = contour_fit.get("face_ellipse_bbox")
    search_bbox = (
        tuple(int(round(v)) for v in raw_search_bbox)
        if raw_search_bbox and len(raw_search_bbox) == 4
        else face.bbox
    )
    candidates = estimate_eye_candidates(
        image_rgb,
        search_bbox,
        face.mask,
    )
    left_eye, right_eye = _choose_eye_pair(candidates, search_bbox)
    mouth = estimate_mouth_candidate(image_rgb, search_bbox, face.mask)

    eye_count = int(left_eye is not None) + int(right_eye is not None)
    wink_side = "unknown"
    if eye_count == 1:
        wink_side = "right" if left_eye is not None else "left"

    eye_conf = (
        sum(e[2] for e in [left_eye, right_eye] if e is not None) / max(1, eye_count)
    )
    mouth_conf = mouth[2] if mouth is not None else 0.0
    confidence = float(np.clip(
        face.confidence * 0.35
        + min(1.0, eye_count / 2) * 0.35
        + eye_conf * 0.20
        + mouth_conf * 0.10,
        0.0,
        1.0,
    ))

    return FaceFeatureLayout(
        face_bbox=search_bbox,
        left_eye=left_eye,
        right_eye=right_eye,
        mouth=mouth,
        wink_side=wink_side,
        confidence=confidence,
    )


def _face_base_shape(
    face: CharacterPartCandidate,
    image_rgb: np.ndarray,
    start_id: int,
) -> Shape:
    contour_fit = face.metadata.get("contour_fit") or {}
    raw_bbox = contour_fit.get("face_ellipse_bbox")
    if raw_bbox and len(raw_bbox) == 4:
        x, y, w, h = [float(v) for v in raw_bbox]
        cx = x + w / 2.0
        cy = y + h / 2.0
        rx = max(2.0, w / 2.0)
        ry = max(2.0, h / 2.0)
    else:
        x, y, w, h = face.bbox
        cx = x + w / 2.0
        cy = y + h * 0.47
        rx = max(2.0, w * 0.47)
        # Face candidate masks can include neck/cheek spill, producing a tall bbox.
        # Clamp vertical radius by face width so the final abstraction stays head-like.
        ry = max(2.0, min(h * 0.43, w * 0.58))
    skin = _dominant_color(image_rgb, face.mask)
    return Shape(
        id=start_id,
        shape_type="ellipse",
        fill_color=skin,
        cx=cx,
        cy=cy,
        rx=rx,
        ry=ry,
        source_role="character_face_base",
        layer_name="character_face_base",
        semantic_type="character_face",
        character_part="face",
        part_confidence=face.confidence,
        importance=1.0,
    )


def _build_eye_shape_for_side(
    layout: FaceFeatureLayout,
    face: CharacterPartCandidate,
    image_rgb: np.ndarray,
    side: str,
    *,
    start_id: int,
) -> Shape | None:
    eye = layout.left_eye if side == "left" else layout.right_eye
    if eye is None:
        return None

    dark = _dark_color_from_face(image_rgb, face.mask)
    _, _, fw, fh = layout.face_bbox
    rx = max(1.0, fw * 0.032)
    ry = max(1.0, fh * 0.026)
    x, y, conf = eye
    return Shape(
        id=start_id,
        shape_type="ellipse",
        fill_color=dark,
        cx=float(x),
        cy=float(y),
        rx=rx,
        ry=ry,
        source_role="character_eye",
        layer_name="character_face_detail",
        semantic_type="character_eye",
        character_part="face",
        part_confidence=float(conf),
        importance=1.0,
        side_hint=side,
    )


def build_eye_shapes(
    layout: FaceFeatureLayout,
    face: CharacterPartCandidate,
    image_rgb: np.ndarray,
    *,
    start_id: int,
) -> list[Shape]:
    out = []
    sid = start_id
    for side in ["left", "right"]:
        shape = _build_eye_shape_for_side(
            layout,
            face,
            image_rgb,
            side,
            start_id=sid,
        )
        if shape is None:
            continue
        out.append(shape)
        sid += 1
    return out


def build_mouth_shape(
    layout: FaceFeatureLayout,
    face: CharacterPartCandidate,
    image_rgb: np.ndarray,
    *,
    start_id: int,
) -> Shape | None:
    if layout.mouth is None:
        return None

    x, y, conf = layout.mouth
    _, _, fw, fh = layout.face_bbox
    dark = _dark_color_from_face(image_rgb, face.mask)
    half = max(1.5, fw * 0.040)
    return Shape(
        id=start_id,
        shape_type="line",
        fill_color=None,
        stroke_color=dark,
        stroke_width=max(0.8, min(fw, fh) * 0.012),
        points=[(x - half, y), (x + half, y)],
        source_role="character_mouth",
        layer_name="character_face_detail",
        semantic_type="character_mouth",
        character_part="face",
        part_confidence=float(conf),
        importance=1.0,
    )


def _identity_eye_order(
    layout: FaceFeatureLayout,
    primary_eye_side: str,
) -> list[str]:
    available = {
        "left": layout.left_eye,
        "right": layout.right_eye,
    }
    primary = primary_eye_side if primary_eye_side in available else "none"
    if primary == "none" or available.get(primary) is None:
        detected = [
            (side, eye)
            for side, eye in available.items()
            if eye is not None
        ]
        detected.sort(key=lambda item: float(item[1][2]), reverse=True)
        primary = detected[0][0] if detected else "none"

    order = []
    if primary in {"left", "right"} and available.get(primary) is not None:
        order.append(primary)
    for side in ["left", "right"]:
        if side not in order and available.get(side) is not None:
            order.append(side)
    return order


def build_face_helper_shape(
    layout: FaceFeatureLayout,
    face: CharacterPartCandidate,
    image_rgb: np.ndarray,
    *,
    start_id: int,
) -> Shape:
    """Render one tiny fringe/forehead cue only when Identity Budget asks for it.

    The helper is intentionally a single short polyline rather than another
    filled feature. It should remain a last-resort identity mark, not turn the
    minimal face into a miniature illustration.
    """
    fx, fy, fw, fh = layout.face_bbox
    cx = fx + fw * 0.50
    y = fy + fh * 0.16
    span = max(2.0, fw * 0.13)
    drop = max(1.0, fh * 0.035)
    dark = _dark_color_from_face(image_rgb, face.mask)
    return Shape(
        id=start_id,
        shape_type="line",
        fill_color=None,
        stroke_color=dark,
        stroke_width=max(0.7, min(fw, fh) * 0.010),
        points=[
            (cx - span, y),
            (cx, y + drop),
            (cx + span, y),
        ],
        source_role="character_face_helper",
        layer_name="character_face_detail",
        semantic_type="character_face_helper",
        character_part="face",
        part_confidence=float(face.confidence),
        importance=0.82,
    )


def build_face_shapes(
    image_rgb: np.ndarray,
    face: CharacterPartCandidate,
    layout: FaceFeatureLayout,
    budget: int,
    *,
    start_id: int,
    identity_reservation: dict[str, int] | None = None,
    primary_eye_side: str = "none",
) -> list[Shape]:
    """Build either the legacy face or a Phase 10.5-c identity-minimal face.

    When `identity_reservation` is None this preserves the historical behavior.
    When present, only cues explicitly reserved by Face Identity Budget may
    consume Shapes. This makes optional detail truly optional instead of merely
    planned.
    """
    if budget <= 0:
        return []

    if identity_reservation is None:
        out = [_face_base_shape(face, image_rgb, start_id)]
        sid = start_id + 1

        if budget >= 2:
            eyes = build_eye_shapes(layout, face, image_rgb, start_id=sid)
            slots = max(0, budget - len(out))
            out.extend(eyes[:slots])
            sid = start_id + len(out)

        if len(out) < budget and layout.mouth is not None:
            mouth = build_mouth_shape(
                layout,
                face,
                image_rgb,
                start_id=sid,
            )
            if mouth is not None:
                out.append(mouth)
        return out[:budget]

    reservation = {
        "face_base": int(bool(identity_reservation.get("face_base", 0))),
        "primary_eye": int(bool(identity_reservation.get("primary_eye", 0))),
        "secondary_eye": int(bool(identity_reservation.get("secondary_eye", 0))),
        "mouth": int(bool(identity_reservation.get("mouth", 0))),
        "helper": int(bool(identity_reservation.get("helper", 0))),
    }
    out: list[Shape] = []
    sid = start_id

    if reservation["face_base"] and len(out) < budget:
        out.append(_face_base_shape(face, image_rgb, sid))
        sid += 1

    eye_order = _identity_eye_order(layout, primary_eye_side)
    rendered_eye_sides: set[str] = set()

    if reservation["primary_eye"] and len(out) < budget and eye_order:
        side = eye_order[0]
        eye_shape = _build_eye_shape_for_side(
            layout, face, image_rgb, side, start_id=sid
        )
        if eye_shape is not None:
            out.append(eye_shape)
            rendered_eye_sides.add(side)
            sid += 1

    if reservation["secondary_eye"] and len(out) < budget:
        secondary = next(
            (side for side in eye_order if side not in rendered_eye_sides),
            None,
        )
        if secondary is not None:
            eye_shape = _build_eye_shape_for_side(
                layout, face, image_rgb, secondary, start_id=sid
            )
            if eye_shape is not None:
                out.append(eye_shape)
                rendered_eye_sides.add(secondary)
                sid += 1

    if reservation["mouth"] and len(out) < budget:
        mouth = build_mouth_shape(
            layout, face, image_rgb, start_id=sid
        )
        if mouth is not None:
            out.append(mouth)
            sid += 1

    if reservation["helper"] and len(out) < budget:
        out.append(
            build_face_helper_shape(
                layout, face, image_rgb, start_id=sid
            )
        )

    return out[:budget]

