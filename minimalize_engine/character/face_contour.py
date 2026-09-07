from __future__ import annotations

from dataclasses import dataclass, field
import math

import cv2
import numpy as np

from .heuristics import mask_bbox, mask_centroid


@dataclass(slots=True)
class FaceContourFitResult:
    refined_mask: np.ndarray
    refined_bbox: tuple[int, int, int, int]
    face_ellipse_bbox: tuple[int, int, int, int]
    center: tuple[float, float]
    width: float
    height: float
    chin_bias: float
    forehead_bias: float
    strategy: str
    confidence: float
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self, *, include_mask: bool = False) -> dict:
        data = {
            "refined_bbox": list(self.refined_bbox),
            "face_ellipse_bbox": list(self.face_ellipse_bbox),
            "center": list(self.center),
            "width": self.width,
            "height": self.height,
            "chin_bias": self.chin_bias,
            "forehead_bias": self.forehead_bias,
            "strategy": self.strategy,
            "confidence": self.confidence,
            "diagnostics": self.diagnostics,
            "enabled": True,
        }
        if include_mask:
            data["refined_mask"] = self.refined_mask
        return data


def _clamp_bbox(
    bbox: tuple[float, float, float, float],
    bounds: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    bx, by, bw, bh = bounds
    x, y, w, h = bbox
    x0 = max(bx, int(round(x)))
    y0 = max(by, int(round(y)))
    x1 = min(bx + bw, int(round(x + w)))
    y1 = min(by + bh, int(round(y + h)))
    return x0, y0, max(1, x1 - x0), max(1, y1 - y0)


def _ellipse_bbox(
    center: tuple[float, float],
    width: float,
    height: float,
    bounds: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    return _clamp_bbox(
        (
            center[0] - width / 2.0,
            center[1] - height / 2.0,
            width,
            height,
        ),
        bounds,
    )


def build_face_anchor_points(
    validation: dict | None,
) -> dict[str, tuple[float, float] | None]:
    validation = validation or {}

    def point(key: str) -> tuple[float, float] | None:
        raw = validation.get(key)
        if raw is None:
            return None
        return float(raw[0]), float(raw[1])

    return {
        "left_eye": point("left_eye"),
        "right_eye": point("right_eye"),
        "mouth": point("mouth"),
    }


def estimate_chin_bias(
    anchors: dict[str, tuple[float, float] | None],
    face_bbox_hint: tuple[int, int, int, int],
) -> float:
    mouth = anchors.get("mouth")
    if mouth is None:
        return 0.0
    _, y, _, h = face_bbox_hint
    mouth_y = (mouth[1] - y) / max(float(h), 1.0)
    # Mouth below ~72% suggests we should trim less aggressively.
    return float(np.clip((mouth_y - 0.66) / 0.24, -0.45, 0.65))


def estimate_forehead_bias(
    anchors: dict[str, tuple[float, float] | None],
    face_bbox_hint: tuple[int, int, int, int],
) -> float:
    eyes = [
        p for p in [anchors.get("left_eye"), anchors.get("right_eye")]
        if p is not None
    ]
    if not eyes:
        return 0.0
    _, y, _, h = face_bbox_hint
    eye_y = float(sum(p[1] for p in eyes) / len(eyes))
    eye_rel = (eye_y - y) / max(float(h), 1.0)
    # High eyes need a little more forehead; low eyes need less.
    return float(np.clip((0.43 - eye_rel) / 0.24, -0.45, 0.65))


def _fit_observed_ellipse(
    mask: np.ndarray,
) -> tuple[tuple[float, float], float, float, float, str]:
    binary = (mask > 0).astype(np.uint8) * 255
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = list(contours)
    if not contours:
        x, y, w, h = mask_bbox(binary)
        return (x + w / 2.0, y + h / 2.0), float(w), float(h), 0.0, "bbox"

    contour = max(contours, key=cv2.contourArea)
    if len(contour) >= 5:
        (cx, cy), (a, b), angle = cv2.fitEllipse(contour)
        width = float(a)
        height = float(b)
        # OpenCV can swap axes depending on rotation. Convert to a stable
        # axis-aligned abstraction while preserving approximate area.
        theta = math.radians(float(angle))
        axis_w = abs(width * math.cos(theta)) + abs(height * math.sin(theta))
        axis_h = abs(width * math.sin(theta)) + abs(height * math.cos(theta))
        return (float(cx), float(cy)), max(2.0, axis_w), max(2.0, axis_h), float(angle), "fitEllipse"

    x, y, w, h = cv2.boundingRect(contour)
    return (x + w / 2.0, y + h / 2.0), float(w), float(h), 0.0, "bbox"


def estimate_face_ellipse_bbox(
    head_bbox: tuple[int, int, int, int],
    face_bbox_hint: tuple[int, int, int, int],
    anchors: dict[str, tuple[float, float] | None],
    *,
    observed_center: tuple[float, float] | None = None,
    observed_width: float | None = None,
    observed_height: float | None = None,
    observed_mask_area: int | None = None,
    shrink_strength: float = 0.22,
    chin_trim_strength: float = 0.18,
    forehead_expand_strength: float = 0.10,
) -> tuple[int, int, int, int]:
    hx, hy, hw, hh = head_bbox
    fx, fy, fw, fh = face_bbox_hint
    anchors = anchors or {}

    cx = float(observed_center[0]) if observed_center is not None else fx + fw / 2.0
    cy = float(observed_center[1]) if observed_center is not None else fy + fh / 2.0
    width = float(observed_width if observed_width is not None else fw)
    height = float(observed_height if observed_height is not None else fh)

    eyes = [
        p for p in [anchors.get("left_eye"), anchors.get("right_eye")]
        if p is not None
    ]
    mouth = anchors.get("mouth")

    if len(eyes) >= 2:
        eye_span = abs(eyes[-1][0] - eyes[0][0])
        eye_center_x = (eyes[0][0] + eyes[-1][0]) / 2.0
        width = max(width, eye_span * 1.75)
        cx = cx * 0.55 + eye_center_x * 0.45
    elif len(eyes) == 1:
        width = max(width, fw * 0.70)
        cx = cx * 0.82 + eyes[0][0] * 0.18

    if eyes and mouth is not None:
        eye_y = float(sum(p[1] for p in eyes) / len(eyes))
        eye_mouth = max(1.0, mouth[1] - eye_y)
        height = max(height, eye_mouth * 2.55)
        target_cy = eye_y + eye_mouth * 0.72
        cy = cy * 0.58 + target_cy * 0.42

    # Match the ellipse area to the observed semantic face mass. This is the
    # key alpha10-dev2 correction for both too-small and too-large face bases.
    if observed_mask_area is not None and observed_mask_area > 0:
        ellipse_area = math.pi * max(width / 2.0, 1.0) * max(height / 2.0, 1.0)
        area_scale = math.sqrt(observed_mask_area / max(ellipse_area, 1.0))
        area_scale = float(np.clip(area_scale, 0.74, 1.32))
        width *= area_scale
        height *= area_scale

    # shrink_strength is mainly a protection against broad skin bboxes. Let
    # strong observed contour evidence override most of the generic shrink.
    shrink = float(np.clip(shrink_strength, 0.0, 0.55))
    fill = 0.0
    if observed_mask_area is not None:
        fill = observed_mask_area / max(float(fw * fh), 1.0)
    shrink_effect = shrink * float(np.clip((0.64 - fill) / 0.64, 0.0, 1.0))
    width *= 1.0 - shrink_effect * 0.34
    height *= 1.0 - shrink_effect * 0.24

    chin_bias = estimate_chin_bias(anchors, face_bbox_hint)
    forehead_bias = estimate_forehead_bias(anchors, face_bbox_hint)
    chin_trim = float(np.clip(chin_trim_strength, 0.0, 0.45))
    forehead_expand = float(np.clip(forehead_expand_strength, 0.0, 0.30))

    height *= 1.0 - chin_trim * 0.22 * max(0.0, -chin_bias)
    height *= 1.0 + forehead_expand * 0.18 * max(0.0, forehead_bias)
    cy -= height * forehead_expand * 0.055 * max(0.0, forehead_bias)
    cy -= height * chin_trim * 0.035 * max(0.0, -chin_bias)

    min_width = max(4.0, fw * 0.58)
    min_height = max(5.0, fh * 0.58)
    max_width = max(min_width, hw * 0.82)
    max_height = max(min_height, hh * 0.90)
    width = float(np.clip(width, min_width, max_width))
    height = float(np.clip(height, min_height, max_height))

    cx = float(np.clip(cx, hx + width / 2.0, hx + hw - width / 2.0))
    cy = float(np.clip(cy, hy + height / 2.0, hy + hh - height / 2.0))
    return _ellipse_bbox((cx, cy), width, height, head_bbox)


def rasterize_face_ellipse(
    bbox: tuple[int, int, int, int],
    canvas_shape: tuple[int, int] | tuple[int, int, int],
) -> np.ndarray:
    h, w = canvas_shape[:2]
    x, y, bw, bh = bbox
    out = np.zeros((h, w), dtype=np.uint8)
    center = (int(round(x + bw / 2.0)), int(round(y + bh / 2.0)))
    axes = (max(1, int(round(bw / 2.0))), max(1, int(round(bh / 2.0))))
    cv2.ellipse(out, center, axes, 0.0, 0.0, 360.0, 255, thickness=-1)
    return out


def refine_face_mask_with_ellipse(
    face_candidate_mask: np.ndarray,
    ellipse_mask: np.ndarray,
    *,
    skin_mask: np.ndarray | None = None,
) -> np.ndarray:
    candidate = (face_candidate_mask > 0).astype(np.uint8) * 255
    ellipse = (ellipse_mask > 0).astype(np.uint8) * 255
    overlap = cv2.bitwise_and(candidate, ellipse)

    # Keep observed face pixels close to the fitted ellipse boundary. The small
    # dilation avoids cutting cheeks/forehead just because the source mask is
    # blocky while the output abstraction is elliptical.
    k = max(3, int(round(min(candidate.shape[:2]) * 0.006)) | 1)
    allowed = cv2.dilate(
        ellipse,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)),
    )
    refined = cv2.bitwise_and(candidate, allowed)

    if skin_mask is not None:
        skin = cv2.bitwise_and(refined, (skin_mask > 0).astype(np.uint8) * 255)
        if np.count_nonzero(skin) >= max(6, int(np.count_nonzero(refined) * 0.42)):
            # Do not replace the mask entirely with skin. Merge it with the
            # ellipse overlap so eyes/mouth-adjacent facial mass remains.
            refined = cv2.bitwise_or(skin, overlap)

    if np.count_nonzero(refined) < max(6, int(np.count_nonzero(candidate) * 0.50)):
        return candidate
    return refined


def normalize_face_contour_mask(
    mask: np.ndarray,
    *,
    min_area: int = 12,
) -> np.ndarray:
    binary = (mask > 0).astype(np.uint8) * 255
    if np.count_nonzero(binary) < min_area:
        return binary
    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
    )
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(contours)
    if not contours:
        return binary
    contour = max(contours, key=cv2.contourArea)
    out = np.zeros_like(binary)
    cv2.drawContours(out, [contour], -1, 255, thickness=-1)
    return out


def fit_face_contour(
    image_rgb: np.ndarray | None,
    head_mask: np.ndarray,
    face_candidate_mask: np.ndarray,
    *,
    face_bbox_hint: tuple[int, int, int, int],
    validation: dict | None = None,
    skin_mask: np.ndarray | None = None,
    shrink_strength: float = 0.22,
    chin_trim_strength: float = 0.18,
    forehead_expand_strength: float = 0.10,
    width_scale: float = 1.00,
    height_scale: float = 1.00,
    center_x_shift_ratio: float = 0.00,
    center_y_shift_ratio: float = 0.00,
) -> FaceContourFitResult:
    candidate = normalize_face_contour_mask(face_candidate_mask)
    candidate_area = int(np.count_nonzero(candidate))
    head_bbox = mask_bbox(head_mask)
    observed_bbox = mask_bbox(candidate)
    observed_center = mask_centroid(candidate)
    observed_center_fit, observed_width, observed_height, observed_angle, observed_strategy = _fit_observed_ellipse(candidate)

    # A contour centroid is more stable than fitEllipse center when hair/skin
    # creates a small asymmetric bite, so blend the two.
    center = (
        observed_center[0] * 0.58 + observed_center_fit[0] * 0.42,
        observed_center[1] * 0.58 + observed_center_fit[1] * 0.42,
    )
    anchors = build_face_anchor_points(validation)
    ellipse_bbox = estimate_face_ellipse_bbox(
        head_bbox,
        face_bbox_hint,
        anchors,
        observed_center=center,
        observed_width=observed_width,
        observed_height=observed_height,
        observed_mask_area=candidate_area,
        shrink_strength=shrink_strength,
        chin_trim_strength=chin_trim_strength,
        forehead_expand_strength=forehead_expand_strength,
    )
    ellipse_mask = rasterize_face_ellipse(ellipse_bbox, candidate.shape)
    refined = refine_face_mask_with_ellipse(
        candidate,
        ellipse_mask,
        skin_mask=skin_mask,
    )
    refined = normalize_face_contour_mask(refined)
    refined_bbox = mask_bbox(refined)

    # Second-pass mass correction: the semantic face mask can become smaller
    # after skin/ellipse cleanup. Resize the output ellipse toward that final
    # mass rather than the pre-cleanup candidate. This prevents sparse,
    # featureless face candidates from turning into oversized oval plates.
    refined_area_now = int(np.count_nonzero(refined))
    ellipse_area_now = int(np.count_nonzero(ellipse_mask))
    second_pass_scale = 1.0
    if refined_area_now > 0 and ellipse_area_now > 0:
        ratio_now = ellipse_area_now / max(refined_area_now, 1)
        if ratio_now > 1.24 or ratio_now < 0.78:
            second_pass_scale = float(np.clip(
                math.sqrt(refined_area_now / max(float(ellipse_area_now), 1.0)),
                0.72,
                1.18,
            ))
            ex, ey, ew, eh = ellipse_bbox
            rcx, rcy = mask_centroid(refined)
            target_w = ew * second_pass_scale
            target_h = eh * second_pass_scale

            # Keep reliable detected features inside the ellipse with modest
            # breathing room. With no features, semantic mass fully controls it.
            feature_points = [v for v in anchors.values() if v is not None]
            if feature_points:
                xs = [v[0] for v in feature_points]
                ys = [v[1] for v in feature_points]
                target_w = max(target_w, (max(xs) - min(xs) + 1.0) * 1.55)
                target_h = max(target_h, (max(ys) - min(ys) + 1.0) * 2.15)
            ellipse_bbox = _ellipse_bbox(
                (float(rcx), float(rcy)),
                target_w,
                target_h,
                head_bbox,
            )
            ellipse_mask = rasterize_face_ellipse(ellipse_bbox, candidate.shape)

    # Phase 10.4: deterministic post-fit correction knobs used only when
    # Face-aware Retry has concrete geometry evidence. Defaults are neutral.
    ex, ey, ew, eh = ellipse_bbox
    width_scale = float(np.clip(width_scale, 0.72, 1.32))
    height_scale = float(np.clip(height_scale, 0.72, 1.32))
    center_x_shift_ratio = float(np.clip(center_x_shift_ratio, -0.18, 0.18))
    center_y_shift_ratio = float(np.clip(center_y_shift_ratio, -0.18, 0.18))
    correction_applied = (
        abs(width_scale - 1.0) > 1e-6
        or abs(height_scale - 1.0) > 1e-6
        or abs(center_x_shift_ratio) > 1e-6
        or abs(center_y_shift_ratio) > 1e-6
    )
    if correction_applied:
        correction_center = (
            ex + ew / 2.0 + ew * center_x_shift_ratio,
            ey + eh / 2.0 + eh * center_y_shift_ratio,
        )
        ellipse_bbox = _ellipse_bbox(
            correction_center,
            ew * width_scale,
            eh * height_scale,
            head_bbox,
        )
        ellipse_mask = rasterize_face_ellipse(ellipse_bbox, candidate.shape)

    x, y, w, h = ellipse_bbox
    chin_bias = estimate_chin_bias(anchors, face_bbox_hint)
    forehead_bias = estimate_forehead_bias(anchors, face_bbox_hint)
    overlap = np.count_nonzero((candidate > 0) & (ellipse_mask > 0))
    union = np.count_nonzero((candidate > 0) | (ellipse_mask > 0))
    iou = overlap / max(union, 1)
    coverage = overlap / max(candidate_area, 1)
    ellipse_area = int(np.count_nonzero(ellipse_mask))
    area_ratio = ellipse_area / max(candidate_area, 1)

    confidence = float(np.clip(
        0.42 * coverage
        + 0.28 * min(1.0, iou / 0.62)
        + 0.18 * min(1.0, 1.0 / max(abs(math.log(max(area_ratio, 1e-6))) + 0.55, 1.0))
        + 0.12 * (1.0 if any(v is not None for v in anchors.values()) else 0.55),
        0.0,
        1.0,
    ))

    strategy = f"{observed_strategy}+area_match"
    if any(v is not None for v in anchors.values()):
        strategy += "+feature_guided"

    return FaceContourFitResult(
        refined_mask=refined,
        refined_bbox=refined_bbox,
        face_ellipse_bbox=ellipse_bbox,
        center=(x + w / 2.0, y + h / 2.0),
        width=float(w),
        height=float(h),
        chin_bias=chin_bias,
        forehead_bias=forehead_bias,
        strategy=strategy,
        confidence=confidence,
        diagnostics={
            "candidate_area": candidate_area,
            "refined_area": int(np.count_nonzero(refined)),
            "ellipse_area": ellipse_area,
            "ellipse_to_candidate_area_ratio": float(area_ratio),
            "second_pass_scale": float(second_pass_scale),
            "retry_correction": {
                "applied": bool(correction_applied),
                "width_scale": float(width_scale),
                "height_scale": float(height_scale),
                "center_x_shift_ratio": float(center_x_shift_ratio),
                "center_y_shift_ratio": float(center_y_shift_ratio),
            },
            "candidate_ellipse_iou": float(iou),
            "candidate_ellipse_coverage": float(coverage),
            "observed_bbox": list(observed_bbox),
            "observed_center": [float(observed_center[0]), float(observed_center[1])],
            "observed_fit_center": [float(observed_center_fit[0]), float(observed_center_fit[1])],
            "observed_fit_width": float(observed_width),
            "observed_fit_height": float(observed_height),
            "observed_fit_angle": float(observed_angle),
            "anchors": {
                k: list(v) if v is not None else None
                for k, v in anchors.items()
            },
        },
    )
