from __future__ import annotations

from dataclasses import dataclass
import cv2
import numpy as np

from ..models import Shape
from .models import CharacterPartCandidate


@dataclass
class HairFlow:
    id: int
    flow_type: str
    points: list[tuple[float, float]]
    side: str
    confidence: float
    color: tuple[int, int, int] | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "flow_type": self.flow_type,
            "points": [list(p) for p in self.points],
            "side": self.side,
            "confidence": self.confidence,
            "color": list(self.color) if self.color is not None else None,
        }


def _dominant_hair_colors(
    image_rgb: np.ndarray,
    hair_mask: np.ndarray,
) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    pixels = image_rgb[hair_mask > 0]
    if len(pixels) < 10:
        return (90, 72, 82), (55, 45, 52)

    # Deterministic 2-cluster quantization for base/accent hair colors.
    sample = pixels.astype(np.float32)
    if len(sample) > 5000:
        idx = np.linspace(0, len(sample) - 1, 5000).astype(np.int32)
        sample = sample[idx]

    mean = sample.mean(axis=0)
    lum = sample @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    pivot = np.median(lum)
    low = sample[lum <= pivot]
    high = sample[lum > pivot]

    def med(arr, fallback):
        if len(arr) < 4:
            arr = sample
        value = np.median(arr, axis=0) if len(arr) else np.asarray(fallback)
        return tuple(int(np.clip(round(v), 0, 255)) for v in value)

    dark = med(low, mean)
    light = med(high, mean)

    # Main color follows the larger luminance half closest to overall median.
    overall = med(sample, mean)
    d_dark = sum((overall[i] - dark[i]) ** 2 for i in range(3))
    d_light = sum((overall[i] - light[i]) ** 2 for i in range(3))
    main = dark if d_dark <= d_light else light
    accent = light if main == dark else dark
    return main, accent


def _largest_contours(mask: np.ndarray, count: int = 3):
    binary = (mask > 0).astype(np.uint8) * 255
    k = max(3, int(round(min(mask.shape[:2]) * 0.008)) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    contours = list(contours)
    contours.sort(key=cv2.contourArea, reverse=True)
    return contours[:count]


def _simplified_contour_points(
    contour: np.ndarray,
    *,
    epsilon_ratio: float = 0.018,
    min_vertices: int = 5,
    max_vertices: int = 14,
) -> list[tuple[float, float]]:
    if contour is None or len(contour) < 3:
        return []
    peri = max(float(cv2.arcLength(contour, True)), 1.0)
    eps = peri * epsilon_ratio
    approx = cv2.approxPolyDP(contour, eps, True)

    while len(approx) > max_vertices and eps < peri * 0.08:
        eps *= 1.18
        approx = cv2.approxPolyDP(contour, eps, True)

    if len(approx) < min_vertices:
        approx = cv2.approxPolyDP(contour, max(peri * 0.009, 0.8), True)

    pts = [(float(p[0][0]), float(p[0][1])) for p in approx]
    return pts


def _side_of_x(x: float, center_x: float, tolerance: float) -> str:
    if x < center_x - tolerance:
        return "left"
    if x > center_x + tolerance:
        return "right"
    return "center"


def detect_bangs_flow(
    hair_mask: np.ndarray,
    face_bbox: tuple[int, int, int, int] | None,
) -> list[HairFlow]:
    if face_bbox is None:
        return []

    x, y, w, h = face_bbox
    mh, mw = hair_mask.shape[:2]
    xa = max(0, x - int(round(w * 0.15)))
    xb = min(mw, x + w + int(round(w * 0.15)))
    ya = max(0, y - int(round(h * 0.50)))
    yb = min(mh, y + int(round(h * 0.50)))

    crop = hair_mask[ya:yb, xa:xb] > 0
    if crop.size == 0 or not np.any(crop):
        return []

    center_x = x + w / 2.0
    # Find several lower boundary points of hair above the eyes.
    sample_xs = np.linspace(max(xa, x), min(xb - 1, x + w), 5)
    endpoints = []
    for sx in sample_xs:
        ix = int(round(sx))
        col = np.where(hair_mask[ya:yb, ix] > 0)[0]
        if len(col) == 0:
            continue
        py = ya + int(col.max())
        if py > y + h * 0.62:
            continue
        endpoints.append((float(ix), float(py)))

    if not endpoints:
        return []

    top_pixels = np.argwhere(hair_mask[max(0, ya):max(ya + 1, y + int(h * 0.15)), xa:xb] > 0)
    if len(top_pixels):
        root_y = max(ya, y - h * 0.22)
    else:
        root_y = y - h * 0.08
    root_y = float(max(0, root_y))

    flows = []
    for i, end in enumerate(endpoints):
        sx = end[0]
        root_x = center_x + (sx - center_x) * 0.42
        flows.append(
            HairFlow(
                id=i,
                flow_type="bangs",
                points=[(float(root_x), root_y), end],
                side=_side_of_x(sx, center_x, w * 0.08),
                confidence=0.68,
            )
        )
    return flows


def detect_side_hair_flows(
    hair_mask: np.ndarray,
    face_bbox: tuple[int, int, int, int] | None,
) -> list[HairFlow]:
    if face_bbox is None:
        return []

    x, y, w, h = face_bbox
    mh, mw = hair_mask.shape[:2]
    center_x = x + w / 2.0
    flows = []
    fid = 100

    for side, xa, xb in [
        ("left", max(0, x - int(w * 0.55)), max(1, x + int(w * 0.18))),
        ("right", min(mw - 1, x + int(w * 0.82)), min(mw, x + int(w * 1.55))),
    ]:
        if xb <= xa:
            continue
        ya = max(0, y - int(h * 0.25))
        yb = min(mh, y + int(h * 1.55))
        crop = hair_mask[ya:yb, xa:xb] > 0
        ys, xs = np.nonzero(crop)
        if len(xs) < 10:
            continue

        if side == "left":
            qx = float(np.percentile(xs + xa, 30))
        else:
            qx = float(np.percentile(xs + xa, 70))
        top_y = float(np.percentile(ys + ya, 15))
        bottom_y = float(np.percentile(ys + ya, 88))
        root_x = float(x + w * (0.25 if side == "left" else 0.75))
        end_x = qx
        mid_x = (root_x + end_x) / 2.0 + (-w * 0.08 if side == "left" else w * 0.08)

        flows.append(
            HairFlow(
                id=fid,
                flow_type="side_hair",
                points=[
                    (root_x, top_y),
                    (float(mid_x), (top_y + bottom_y) / 2.0),
                    (float(end_x), bottom_y),
                ],
                side=side,
                confidence=0.72,
            )
        )
        fid += 1

    return flows


def detect_back_hair_flow(
    hair_mask: np.ndarray,
    subject_bbox: tuple[int, int, int, int],
    face_bbox: tuple[int, int, int, int] | None,
) -> list[HairFlow]:
    ys, xs = np.nonzero(hair_mask > 0)
    if len(xs) < 20:
        return []

    x0, y0, bw, bh = subject_bbox
    center_x = float(np.median(xs))
    top_y = float(np.percentile(ys, 8))
    bottom_y = float(np.percentile(ys, 92))
    if face_bbox is not None:
        _, fy, _, fh = face_bbox
        # A very short hair mask is better represented by bangs/side flows.
        if bottom_y <= fy + fh * 1.15:
            return []

    return [
        HairFlow(
            id=200,
            flow_type="back_hair",
            points=[
                (center_x, top_y),
                (center_x, (top_y + bottom_y) / 2.0),
                (center_x, bottom_y),
            ],
            side="center",
            confidence=0.58,
        )
    ]


def detect_hair_feature_flows(
    hair_mask: np.ndarray,
    face_bbox: tuple[int, int, int, int] | None,
) -> list[HairFlow]:
    contours = _largest_contours(hair_mask, count=4)
    if len(contours) <= 1:
        return []

    flows = []
    if face_bbox is not None:
        fx, fy, fw, fh = face_bbox
        center = fx + fw / 2.0
    else:
        center = hair_mask.shape[1] / 2.0

    for i, contour in enumerate(contours[1:4]):
        area = cv2.contourArea(contour)
        if area < max(8, hair_mask.size * 0.0007):
            continue
        m = cv2.moments(contour)
        if abs(m["m00"]) < 1e-6:
            continue
        cx = m["m10"] / m["m00"]
        cy = m["m01"] / m["m00"]
        x, y, w, h = cv2.boundingRect(contour)
        if max(w, h) / max(1.0, min(w, h)) < 1.55:
            continue

        pts = _simplified_contour_points(
            contour,
            epsilon_ratio=0.035,
            min_vertices=3,
            max_vertices=7,
        )
        if len(pts) < 3:
            continue
        flows.append(
            HairFlow(
                id=300 + i,
                flow_type="hair_feature",
                points=pts,
                side=_side_of_x(cx, center, max(4, w * 0.15)),
                confidence=0.62,
            )
        )
    return flows


def analyze_hair_flows(
    hair: CharacterPartCandidate,
    face: CharacterPartCandidate | None,
    image_rgb: np.ndarray,
    subject_bbox: tuple[int, int, int, int] | None = None,
) -> list[HairFlow]:
    face_bbox = face.bbox if face is not None else None
    flows = []
    flows.extend(detect_bangs_flow(hair.mask, face_bbox))
    flows.extend(detect_side_hair_flows(hair.mask, face_bbox))
    flows.extend(
        detect_back_hair_flow(
            hair.mask,
            subject_bbox or hair.bbox,
            face_bbox,
        )
    )
    flows.extend(detect_hair_feature_flows(hair.mask, face_bbox))

    main, accent = _dominant_hair_colors(image_rgb, hair.mask)
    for f in flows:
        f.color = accent
    return flows


def _hair_base_shapes(
    hair: CharacterPartCandidate,
    image_rgb: np.ndarray,
    budget: int,
    start_id: int,
) -> list[Shape]:
    if budget <= 0:
        return []

    main, _ = _dominant_hair_colors(image_rgb, hair.mask)
    contours = _largest_contours(hair.mask, count=max(1, min(3, budget)))
    out = []
    sid = start_id

    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < max(6, hair.mask.size * 0.0006):
            continue
        pts = _simplified_contour_points(contour)
        if len(pts) < 3:
            continue
        out.append(
            Shape(
                id=sid,
                shape_type="polygon",
                fill_color=main,
                points=pts,
                source_role="character_hair_base",
                layer_name="character_hair_base",
                semantic_type="character_hair",
                character_part="hair",
                part_confidence=hair.confidence,
                importance=1.0,
            )
        )
        sid += 1
        if len(out) >= budget:
            break
    return out


def _flow_to_shape(
    flow: HairFlow,
    color: tuple[int, int, int],
    sid: int,
    hair_bbox: tuple[int, int, int, int],
) -> Shape | None:
    if len(flow.points) < 2:
        return None

    _, _, w, h = hair_bbox
    if flow.flow_type == "hair_feature" and len(flow.points) >= 3:
        return Shape(
            id=sid,
            shape_type="polygon",
            fill_color=color,
            points=flow.points,
            source_role="character_hair_feature",
            layer_name="character_hair_detail",
            semantic_type="character_hair_feature",
            character_part="hair",
            part_confidence=flow.confidence,
            side_hint=flow.side,
            importance=0.96,
        )

    stroke = max(0.8, min(w, h) * 0.012)
    return Shape(
        id=sid,
        shape_type="line",
        fill_color=None,
        stroke_color=color,
        stroke_width=stroke,
        points=[flow.points[0], flow.points[-1]],
        source_role=f"character_{flow.flow_type}",
        layer_name="character_hair_detail",
        semantic_type=f"character_{flow.flow_type}",
        character_part="hair",
        part_confidence=flow.confidence,
        side_hint=flow.side,
        importance=0.95,
    )


def build_hair_shapes(
    hair: CharacterPartCandidate,
    flows: list[HairFlow],
    image_rgb: np.ndarray,
    budget: int,
    *,
    start_id: int,
) -> list[Shape]:
    if budget <= 0:
        return []

    main, accent = _dominant_hair_colors(image_rgb, hair.mask)

    # Keep at least one silhouette shape. More complex/long hair may use two.
    base_budget = 1
    if budget >= 6 and hair.area_ratio >= 0.025:
        base_budget = 2

    out = _hair_base_shapes(
        hair,
        image_rgb,
        base_budget,
        start_id,
    )
    sid = start_id + len(out)

    remaining = max(0, budget - len(out))
    ranked = sorted(
        flows,
        key=lambda f: (
            f.flow_type == "bangs",
            f.flow_type == "side_hair",
            f.flow_type == "hair_feature",
            f.confidence,
        ),
        reverse=True,
    )

    for flow in ranked:
        if remaining <= 0:
            break
        shape = _flow_to_shape(flow, accent, sid, hair.bbox)
        if shape is None:
            continue
        out.append(shape)
        sid += 1
        remaining -= 1

    return out[:budget]
