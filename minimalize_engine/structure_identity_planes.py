from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .models import Shape
from .structure_sleeve_completion import _face_box, _hand_component, _skin_like_from_face


@dataclass
class StructureIdentityPlaneResult:
    enabled: bool
    reason: str
    shapes: tuple[Shape, ...] = ()
    hand_count: int = 0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "shape_count": len(self.shapes),
            "hand_count": int(self.hand_count),
        }


def _median_color(rgb: np.ndarray, mask: np.ndarray) -> tuple[int, int, int]:
    pixels = rgb[mask > 0]
    if not len(pixels):
        return 200, 170, 155
    return tuple(int(v) for v in np.median(pixels, axis=0).astype(np.uint8))


def _distance_to(mask: np.ndarray, target: np.ndarray) -> float:
    if not np.any(mask) or not np.any(target):
        return float("inf")
    distance = cv2.distanceTransform(1 - (target > 0).astype(np.uint8), cv2.DIST_L2, 3)
    return float(distance[mask > 0].min())


def _coarse_hand_polygon(mask: np.ndarray) -> list[tuple[float, float]] | None:
    closed = cv2.morphologyEx(
        mask.astype(np.uint8), cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
    )
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    hull = cv2.convexHull(max(contours, key=cv2.contourArea))
    perimeter = float(cv2.arcLength(hull, True))
    chosen = None
    for ratio in (0.035, 0.05, 0.07, 0.09, 0.12):
        approx = cv2.approxPolyDP(hull, max(1.5, perimeter * ratio), True).reshape(-1, 2)
        chosen = approx
        if 3 <= len(approx) <= 6:
            break
    if chosen is None or len(chosen) < 3:
        return None
    return [(float(x), float(y)) for x, y in chosen[:6]]


def _hand_geometry_hint(face_mask: np.ndarray) -> np.ndarray:
    ys, xs = np.where(face_mask > 0)
    if not len(xs):
        return face_mask.astype(np.uint8)
    fw = max(int(xs.max()) - int(xs.min()) + 1, 1)
    fh = max(int(ys.max()) - int(ys.min()) + 1, 1)
    kx = max(5, int(round(fw * 0.55)) | 1)
    ky = max(5, int(round(fh * 0.45)) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kx, ky))
    return cv2.dilate((face_mask > 0).astype(np.uint8), kernel)


def build_identity_hand_planes(
    rgb: np.ndarray,
    subject_mask: np.ndarray,
    face_mask: np.ndarray | None,
    *,
    left_arm_mask: np.ndarray | None = None,
    right_arm_mask: np.ndarray | None = None,
    start_id: int = 965000,
) -> StructureIdentityPlaneResult:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        return StructureIdentityPlaneResult(False, "rgb_required")
    if subject_mask.shape != rgb.shape[:2] or face_mask is None or face_mask.shape != rgb.shape[:2]:
        return StructureIdentityPlaneResult(False, "mask_shape_mismatch")
    face_box = _face_box(face_mask)
    if face_box is None:
        return StructureIdentityPlaneResult(False, "face_missing")

    subject = (subject_mask > 0).astype(np.uint8)
    skin = _skin_like_from_face(rgb, face_mask)
    geometry_face = _hand_geometry_hint(face_mask)
    geometry_box = _face_box(geometry_face)
    if geometry_box is None:
        return StructureIdentityPlaneResult(False, "face_geometry_missing")
    face_area = max(int((face_mask > 0).sum()), 1)
    shapes: list[Shape] = []

    for side, arm_mask in (("left", left_arm_mask), ("right", right_arm_mask)):
        hand = _hand_component(skin, geometry_face, side, geometry_box) & subject
        area = int(hand.sum())
        if area < 12 or area > int(face_area * 0.70):
            continue
        if arm_mask is not None and arm_mask.shape == hand.shape:
            arm = (arm_mask > 0).astype(np.uint8) & subject
            if np.any(arm) and _distance_to(hand, arm) > max(8.0, min(hand.shape) * 0.045):
                continue
        points = _coarse_hand_polygon(hand)
        if points is None:
            continue
        shapes.append(Shape(
            id=start_id + len(shapes),
            shape_type="polygon",
            fill_color=_median_color(rgb, hand),
            points=points,
            z_index=30710,
            importance=0.97,
            source_role=f"phase18_identity_hand_{side}",
            layer_name="foreground",
            semantic_type="character_hand_mass",
            character_part="hand",
            part_confidence=0.90,
            side_hint=side,
        ))

    if not shapes:
        return StructureIdentityPlaneResult(False, "hand_mass_missing")
    return StructureIdentityPlaneResult(True, "ok", tuple(shapes), hand_count=len(shapes))


@dataclass
class StructureMajorPropResult:
    enabled: bool
    reason: str
    shapes: tuple[Shape, ...] = ()
    prop_count: int = 0
    prop_type: str = "none"
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "shape_count": len(self.shapes),
            "prop_count": int(self.prop_count),
            "prop_type": self.prop_type,
            "confidence": round(float(self.confidence), 6),
        }


def _mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask > 0)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _mask_center(mask: np.ndarray) -> tuple[float, float] | None:
    ys, xs = np.where(mask > 0)
    if not len(xs):
        return None
    return float(np.median(xs)), float(np.median(ys))


def _coarse_prop_polygon(mask: np.ndarray, max_points: int = 6) -> list[tuple[float, float]] | None:
    closed = cv2.morphologyEx(
        mask.astype(np.uint8), cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
    )
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    perimeter = float(cv2.arcLength(contour, True))
    chosen = None
    for ratio in (0.025, 0.04, 0.055, 0.075, 0.10, 0.14):
        approx = cv2.approxPolyDP(contour, max(1.5, perimeter * ratio), True).reshape(-1, 2)
        chosen = approx
        if 3 <= len(approx) <= max_points:
            break
    if chosen is None or len(chosen) < 3:
        points = cv2.boxPoints(cv2.minAreaRect(contour)).reshape(-1, 2)
        if len(points) < 3:
            return None
        chosen = points
    return [(float(x), float(y)) for x, y in chosen[:max_points]]


def _line_mask(shape: tuple[int, int], a: tuple[float, float], b: tuple[float, float], thickness: int) -> np.ndarray:
    out = np.zeros(shape, dtype=np.uint8)
    cv2.line(
        out,
        (int(round(a[0])), int(round(a[1]))),
        (int(round(b[0])), int(round(b[1]))),
        1,
        max(1, int(thickness)),
        cv2.LINE_AA,
    )
    return out


def _bbox_dims(mask: np.ndarray) -> tuple[int, int, int, int, int, int] | None:
    box = _mask_bbox(mask)
    if box is None:
        return None
    x0, y0, x1, y1 = box
    return x0, y0, x1, y1, max(x1 - x0, 1), max(y1 - y0, 1)


def _detect_long_linear_prop(
    rgb: np.ndarray,
    subject: np.ndarray,
    face_mask: np.ndarray,
    torso_mask: np.ndarray | None,
    head_mask: np.ndarray | None,
    left_arm_mask: np.ndarray | None,
    right_arm_mask: np.ndarray | None,
) -> tuple[float, str, np.ndarray] | None:
    subject_box = _bbox_dims(subject)
    face_center = _mask_center(face_mask)
    if subject_box is None or face_center is None:
        return None
    sx0, sy0, sx1, sy1, sw, sh = subject_box
    torso_box = _bbox_dims(torso_mask) if torso_mask is not None and torso_mask.shape == subject.shape else None
    axis = (torso_box[0] + torso_box[2]) * 0.5 if torso_box is not None else (sx0 + sx1) * 0.5
    body_width = torso_box[4] if torso_box is not None else max(sw * 0.38, 1.0)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 45, 125)
    vicinity = cv2.dilate(subject, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    edges = cv2.bitwise_and(edges, edges, mask=(vicinity * 255).astype(np.uint8))
    min_len = max(18, int(round(sh * 0.22)))
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180,
        threshold=max(18, int(round(min_len * 0.42))),
        minLineLength=min_len,
        maxLineGap=max(4, int(round(sh * 0.025))),
    )
    if lines is None:
        return None

    known_body = np.zeros_like(subject)
    for part in (torso_mask, head_mask, left_arm_mask, right_arm_mask):
        if part is not None and part.shape == subject.shape:
            known_body |= (part > 0).astype(np.uint8)
    face_box = _bbox_dims(face_mask)
    if face_box is not None:
        _fx0, _fy0, _fx1, fy1, fw, fh = face_box
        core_half = max(int(round(body_width * 0.72)), int(round(fw * 1.15)))
        core_x0 = max(0, int(round(axis - core_half)))
        core_x1 = min(subject.shape[1], int(round(axis + core_half)))
        core_y1 = min(subject.shape[0], max(fy1 + int(round(fh * 0.8)), sy1))
        known_body[max(0, fy1 - int(round(fh * 0.2))):core_y1, core_x0:core_x1] |= subject[max(0, fy1 - int(round(fh * 0.2))):core_y1, core_x0:core_x1]
    known_body = cv2.dilate(known_body, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))

    body_reference = np.zeros_like(subject)
    if torso_mask is not None and torso_mask.shape == subject.shape and np.any(torso_mask):
        body_reference = (torso_mask > 0).astype(np.uint8) & subject
    else:
        face_box = _bbox_dims(face_mask)
        if face_box is not None:
            _fx0, _fy0, _fx1, fy1, fw, fh = face_box
            ref_half = max(int(round(body_width * 0.65)), int(round(fw)))
            rx0 = max(0, int(round(axis - ref_half))); rx1 = min(subject.shape[1], int(round(axis + ref_half)))
            ry1 = min(subject.shape[0], fy1 + max(int(round(fh * 3.0)), int(round(sh * 0.45))))
            body_reference[fy1:ry1, rx0:rx1] = subject[fy1:ry1, rx0:rx1]
    body_rgb = _median_color(rgb, body_reference)
    body_lab = cv2.cvtColor(np.asarray(body_rgb, dtype=np.uint8).reshape(1, 1, 3), cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]

    best: tuple[float, str, np.ndarray] | None = None
    for row in lines[:, 0, :]:
        x1, y1, x2, y2 = [float(v) for v in row]
        length = float(np.hypot(x2 - x1, y2 - y1))
        if length < sh * 0.22:
            continue
        mid_x, mid_y = (x1 + x2) * 0.5, (y1 + y2) * 0.5
        lateral = abs(mid_x - axis) / max(float(body_width), 1.0)
        if lateral < 0.72:
            continue
        if mid_y > sy0 + sh * 0.72 and length < sh * 0.55:
            continue
        sample = _line_mask(subject.shape, (x1, y1), (x2, y2), max(2, int(round(body_width * 0.025))))
        denom = max(int(sample.sum()), 1)
        support = int((sample & subject).sum()) / denom
        if support < 0.24:
            continue
        outside_known = int((sample & subject & (1 - known_body)).sum()) / max(int((sample & subject).sum()), 1)
        if outside_known < 0.34:
            continue
        if torso_mask is not None and torso_mask.shape == subject.shape:
            torso_overlap = int((sample & (torso_mask > 0).astype(np.uint8)).sum()) / denom
            if torso_overlap > 0.48:
                continue
        if head_mask is not None and head_mask.shape == subject.shape:
            head_overlap = int((sample & (head_mask > 0).astype(np.uint8)).sum()) / denom
            if head_overlap > 0.42:
                continue
        angle = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        steep = abs(np.sin(np.radians(angle))) >= 0.58
        prop_type = "staff_like" if steep or length >= sh * 0.50 else "sword_like"
        score = 0.42 + min(0.28, length / max(float(sh), 1.0) * 0.40)
        score += min(0.16, lateral * 0.08) + min(0.10, support * 0.12)
        if prop_type == "staff_like":
            score += 0.05
        thickness = max(3, int(round(body_width * (0.045 if prop_type == "staff_like" else 0.060))))
        prop_mask = _line_mask(subject.shape, (x1, y1), (x2, y2), thickness) & subject
        if int(prop_mask.sum()) < max(18, int(subject.size * 0.0008)):
            continue
        band_radius = max(5, int(round(body_width * 0.20)))
        band = cv2.dilate(prop_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (band_radius * 2 + 1, band_radius * 2 + 1)))
        surround = (band > 0) & (prop_mask == 0)
        surround_occupancy = float(np.count_nonzero(surround & (subject > 0))) / max(float(np.count_nonzero(surround)), 1.0)
        if surround_occupancy > 0.42:
            continue
        prop_rgb = _median_color(rgb, prop_mask)
        pr, pg, pb = prop_rgb
        skin_like_prop = pr >= 135 and pg >= 70 and pb >= 55 and pr >= pg - 10 and pr >= pb + 7 and (pr - min(pg, pb)) <= 135
        if skin_like_prop:
            continue
        prop_lab = cv2.cvtColor(np.asarray(prop_rgb, dtype=np.uint8).reshape(1, 1, 3), cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
        if float(np.linalg.norm(prop_lab - body_lab)) < 12.0:
            continue
        candidate = (float(min(score, 1.0)), prop_type, prop_mask)
        if best is None or candidate[0] > best[0]:
            best = candidate
    return best


def _detect_microphone_prop(
    rgb: np.ndarray,
    subject: np.ndarray,
    face_mask: np.ndarray,
    left_arm_mask: np.ndarray | None,
    right_arm_mask: np.ndarray | None,
) -> tuple[float, str, np.ndarray] | None:
    face_box = _bbox_dims(face_mask)
    face_center = _mask_center(face_mask)
    if face_box is None or face_center is None:
        return None
    fx0, fy0, fx1, fy1, fw, fh = face_box
    h, w = subject.shape
    zone = np.zeros_like(subject)
    zone[max(0, int(fy0 - fh * 0.2)):min(h, int(fy1 + fh * 1.2)),
         max(0, int(face_center[0] - fw * 2.2)):min(w, int(face_center[0] + fw * 2.2))] = 1
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hue, sat, val = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    vivid = ((sat >= 105) & (val >= 70) & (zone > 0) & (subject > 0)).astype(np.uint8)
    vivid = cv2.morphologyEx(vivid, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(vivid, 8)
    arms = []
    for arm in (left_arm_mask, right_arm_mask):
        if arm is not None and arm.shape == subject.shape and np.any(arm):
            arms.append((arm > 0).astype(np.uint8))
    best = None
    for index in range(1, count):
        area = int(stats[index, cv2.CC_STAT_AREA])
        bw = int(stats[index, cv2.CC_STAT_WIDTH]); bh = int(stats[index, cv2.CC_STAT_HEIGHT])
        if area < max(8, int(face_mask.sum() * 0.015)) or area > int(face_mask.sum() * 0.45):
            continue
        if not 0.30 <= bw / max(float(bh), 1.0) <= 2.4:
            continue
        comp = (labels == index).astype(np.uint8)
        hp = hue[comp > 0]; sp = sat[comp > 0]; vp = val[comp > 0]
        if not len(hp):
            continue
        mean_h = float(np.mean(hp)); mean_s = float(np.mean(sp)); mean_v = float(np.mean(vp))
        color_ok = 145 <= mean_h <= 179 and 70 <= mean_v <= 180
        if not color_ok or mean_s < 175:
            continue
        cx, cy = [float(v) for v in centroids[index]]
        face_dist = float(np.hypot(cx - face_center[0], cy - face_center[1])) / max(float(fw), 1.0)
        arm_gap = min((_distance_to(comp, arm) for arm in arms), default=float("inf")) / max(float(fw), 1.0)
        if face_dist > 1.65 or arm_gap > 0.60:
            continue
        score = 0.58 + min(0.16, mean_s / 255.0 * 0.16) + min(0.14, area / max(float(face_mask.sum()), 1.0) * 0.7)
        score += 0.10 * max(0.0, 1.0 - arm_gap / 1.6)
        prop_mask = comp.copy()
        if arms:
            nearest_arm = min(arms, key=lambda arm: _distance_to(comp, arm))
            target = _mask_center(nearest_arm)
            if target is not None:
                vx, vy = target[0] - cx, target[1] - cy
                norm = max(float(np.hypot(vx, vy)), 1e-6)
                stem_len = max(10.0, min(max(float(fw) * 1.15, 14.0), norm * 0.60))
                end = (cx + vx / norm * stem_len, cy + vy / norm * stem_len)
                stem = _line_mask(subject.shape, (cx, cy), end, max(3, int(round(fw * 0.14)))) & subject
                prop_mask |= stem
        if best is None or score > best[0]:
            best = (float(min(score, 1.0)), "microphone_like", prop_mask)
    return best


def _detect_hat_prop(
    rgb: np.ndarray,
    subject: np.ndarray,
    head_mask: np.ndarray | None,
) -> tuple[float, str, np.ndarray] | None:
    if head_mask is None or head_mask.shape != subject.shape or not np.any(head_mask):
        return None
    dims = _bbox_dims((head_mask > 0).astype(np.uint8))
    if dims is None:
        return None
    hx0, hy0, hx1, hy1, hw, hh = dims
    h, w = subject.shape
    zone = np.zeros_like(subject)
    zone[max(0, int(hy0 - hh * 0.65)):min(h, int(hy0 + hh * 0.35)),
         max(0, int(hx0 - hw * 0.60)):min(w, int(hx1 + hw * 0.60))] = 1
    core = np.zeros_like(subject)
    core[max(0, hy0):min(h, int(hy0 + hh * 0.52)), max(0, hx0):min(w, hx1)] = 1
    protr = (subject & zone & (1 - core)).astype(np.uint8)
    protr = cv2.morphologyEx(protr, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(protr, 8)
    best = None
    for index in range(1, count):
        area = int(stats[index, cv2.CC_STAT_AREA])
        bw = int(stats[index, cv2.CC_STAT_WIDTH]); bh = int(stats[index, cv2.CC_STAT_HEIGHT])
        if area < max(18, int(hw * hh * 0.025)) or area > int(hw * hh * 0.65):
            continue
        if bw < hw * 0.75 or bh > hh * 0.65 or bw / max(float(bh), 1.0) < 1.25:
            continue
        cx, cy = [float(v) for v in centroids[index]]
        if cy > hy0 + hh * 0.22:
            continue
        comp = (labels == index).astype(np.uint8)
        x = int(stats[index, cv2.CC_STAT_LEFT]); y = int(stats[index, cv2.CC_STAT_TOP])
        crop = rgb[y:y + bh, x:x + bw]
        if crop.size == 0:
            continue
        edge = cv2.Canny(cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY), 45, 120)
        lines = cv2.HoughLinesP(edge, 1, np.pi / 180, threshold=max(8, int(bw * 0.22)), minLineLength=max(6, int(bw * 0.28)), maxLineGap=3)
        brim = 0.0
        if lines is not None:
            for row in lines[:, 0, :]:
                x1, y1, x2, y2 = [float(v) for v in row]
                angle = abs(float(np.degrees(np.arctan2(y2 - y1, x2 - x1))))
                angle = min(angle, 180.0 - angle)
                if angle <= 18.0:
                    brim = max(brim, float(np.hypot(x2 - x1, y2 - y1)) / max(float(bw), 1.0))
        if brim < 0.34:
            continue
        score = 0.54 + min(0.22, bw / max(float(hw), 1.0) * 0.14) + min(0.12, brim * 0.12)
        if best is None or score > best[0]:
            best = (float(min(score, 1.0)), "hat_like", comp)
    return best


def build_major_prop_plane(
    rgb: np.ndarray,
    subject_mask: np.ndarray,
    face_mask: np.ndarray | None,
    *,
    head_mask: np.ndarray | None = None,
    torso_mask: np.ndarray | None = None,
    left_arm_mask: np.ndarray | None = None,
    right_arm_mask: np.ndarray | None = None,
    start_id: int = 965100,
) -> StructureMajorPropResult:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        return StructureMajorPropResult(False, "rgb_required")
    if subject_mask.shape != rgb.shape[:2] or face_mask is None or face_mask.shape != rgb.shape[:2]:
        return StructureMajorPropResult(False, "mask_shape_mismatch")
    subject = (subject_mask > 0).astype(np.uint8)
    candidates = [
        _detect_long_linear_prop(
            rgb, subject, face_mask, torso_mask, head_mask, left_arm_mask, right_arm_mask
        ),
        _detect_microphone_prop(rgb, subject, face_mask, left_arm_mask, right_arm_mask),
        # Hat detection stays experimental: Otonose hair/ribbon still produces
        # false positives, so Phase 18 Checkpoint 4 only promotes high-precision
        # staff/sword and microphone props.
    ]
    candidates = [candidate for candidate in candidates if candidate is not None]
    if not candidates:
        return StructureMajorPropResult(False, "major_prop_missing")
    score, prop_type, prop_mask = max(candidates, key=lambda item: item[0])
    min_area_ratio = 0.00035 if prop_type == "microphone_like" else 0.0008
    min_area = max(24 if prop_type == "microphone_like" else 18, int(subject.size * min_area_ratio))
    if score < 0.70 or int(prop_mask.sum()) < min_area:
        return StructureMajorPropResult(False, "major_prop_confidence_gate", confidence=float(score))
    if prop_type == "microphone_like":
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        head = ((prop_mask > 0) & (hsv[:, :, 0] >= 145) & (hsv[:, :, 0] <= 179) & (hsv[:, :, 1] >= 175) & (hsv[:, :, 2] >= 70) & (hsv[:, :, 2] <= 180)).astype(np.uint8)
        head_points = _coarse_prop_polygon(head, max_points=6)
        stem = (prop_mask > 0).astype(np.uint8) & (1 - cv2.dilate(head, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))))
        stem_points = _coarse_prop_polygon(stem, max_points=4)
        mic_shapes = []
        if stem_points is not None:
            mic_shapes.append(Shape(id=start_id, shape_type="polygon", fill_color=_median_color(rgb, stem), points=stem_points, z_index=30715, importance=0.97, source_role="phase18_identity_prop_microphone_stem", layer_name="foreground", semantic_type="character_major_prop", character_part="prop", part_confidence=float(min(score, 0.99)), side_hint="unknown"))
        if head_points is not None:
            mic_shapes.append(Shape(id=start_id + len(mic_shapes), shape_type="polygon", fill_color=_median_color(rgb, head), points=head_points, z_index=30716, importance=0.99, source_role="phase18_identity_prop_microphone_head", layer_name="foreground", semantic_type="character_major_prop", character_part="prop", part_confidence=float(min(score, 0.99)), side_hint="unknown"))
        if mic_shapes:
            return StructureMajorPropResult(True, "ok", tuple(mic_shapes), prop_count=1, prop_type=prop_type, confidence=float(score))
    points = _coarse_prop_polygon(prop_mask, max_points=6)
    if points is None:
        return StructureMajorPropResult(False, "major_prop_polygon_failed", confidence=float(score))
    shape = Shape(id=start_id, shape_type="polygon", fill_color=_median_color(rgb, prop_mask), points=points, z_index=30715, importance=0.98, source_role=f"phase18_identity_prop_{prop_type}", layer_name="foreground", semantic_type="character_major_prop", character_part="prop", part_confidence=float(min(score, 0.99)), side_hint="unknown")
    return StructureMajorPropResult(True, "ok", (shape,), prop_count=1, prop_type=prop_type, confidence=float(score))
