from __future__ import annotations

from dataclasses import dataclass
from math import exp

import cv2
import numpy as np


@dataclass
class StructureFaceResult:
    enabled: bool
    reason: str
    mask: np.ndarray | None = None
    bbox: tuple[int, int, int, int] | None = None
    score: float = 0.0
    skin_density: float = 0.0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "bbox": list(self.bbox) if self.bbox else None,
            "score": round(float(self.score), 6),
            "skin_density": round(float(self.skin_density), 6),
        }


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _skin_weight(rgb: np.ndarray, subject_mask: np.ndarray) -> np.ndarray:
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    mx = np.maximum.reduce([r, g, b])
    mn = np.minimum.reduce([r, g, b])
    skin = (
        (r >= g)
        & (g >= b - 6)
        & ((r - b) >= 10)
        & ((r - g) >= 2)
        & ((r - g) <= 68)
        & ((g - b) >= -6)
        & ((g - b) <= 58)
        & (mx >= 150)
        & ((mx - mn) <= 100)
        & (subject_mask > 0)
    )
    warmness = np.clip((r - b - 8) / 40.0, 0.0, 1.0).astype(np.float32)
    return skin.astype(np.float32) * (0.70 + 0.30 * warmness)


def _sum_rect(integral: np.ndarray, x: int, y: int, w: int, h: int) -> float:
    return float(
        integral[y + h, x + w]
        - integral[y, x + w]
        - integral[y + h, x]
        + integral[y, x]
    )


def locate_structure_face(rgb: np.ndarray, subject_mask: np.ndarray) -> StructureFaceResult:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        return StructureFaceResult(False, "rgb_required")
    if subject_mask.ndim != 2 or subject_mask.shape != rgb.shape[:2]:
        return StructureFaceResult(False, "mask_shape_mismatch")
    box = _bbox(subject_mask)
    if box is None:
        return StructureFaceResult(False, "empty_subject")

    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    if bw < 32 or bh < 48:
        return StructureFaceResult(False, "subject_too_small")

    skin = _skin_weight(rgb, subject_mask)
    skin_integral = cv2.integral(skin)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    dark = ((gray < 115) & (subject_mask > 0)).astype(np.float32)
    dark_integral = cv2.integral(dark)

    best = None
    subject_center_x = (x0 + x1) * 0.5
    target_y = y0 + bh * 0.34
    for width_ratio in (0.18, 0.22, 0.26):
        for height_ratio in (0.18, 0.22, 0.26):
            ww = max(18, int(round(bw * width_ratio)))
            hh = max(20, int(round(bh * height_ratio)))
            xmin = int(round(x0 + bw * 0.10))
            xmax = int(round(x1 - bw * 0.10 - ww))
            ymin = int(round(y0 + bh * 0.08))
            ymax = int(round(y0 + bh * 0.55 - hh))
            if xmax < xmin or ymax < ymin:
                continue
            step_x = max(3, ww // 10)
            step_y = max(3, hh // 10)
            for y in range(ymin, ymax + 1, step_y):
                for x in range(xmin, xmax + 1, step_x):
                    skin_density = _sum_rect(skin_integral, x, y, ww, hh) / float(ww * hh)
                    dark_density = _sum_rect(dark_integral, x, y, ww, hh) / float(ww * hh)
                    occupancy = float(subject_mask[y : y + hh, x : x + ww].mean())
                    cx = x + ww * 0.5
                    cy = y + hh * 0.5
                    center_prior = exp(-((cx - subject_center_x) / max(bw * 0.34, 1.0)) ** 2)
                    y_prior = exp(-((cy - target_y) / max(bh * 0.20, 1.0)) ** 2)
                    feature_prior = exp(-((dark_density - 0.08) / 0.10) ** 2)
                    score = (
                        3.20 * skin_density
                        + 0.60 * occupancy
                        + 0.65 * center_prior
                        + 1.15 * y_prior
                        + 0.35 * feature_prior
                    )
                    if best is None or score > best[0]:
                        best = (score, x, y, ww, hh, skin_density)

    if best is None:
        return StructureFaceResult(False, "candidate_missing")

    score, x, y, ww, hh, skin_density = best
    aspect_ratio = float(ww) / max(float(hh), 1.0)
    face_aspect = 0.35 <= aspect_ratio <= 1.25
    strict_skin = skin_density >= 0.12 and face_aspect
    relaxed_skin = (
        skin_density >= 0.05
        and 0.35 <= aspect_ratio <= 1.05
        and score >= 2.45
    )
    if not (strict_skin or relaxed_skin):
        return StructureFaceResult(
            False,
            "skin_density_gate",
            bbox=(x, y, ww, hh),
            score=score,
            skin_density=skin_density,
        )

    face = np.zeros(subject_mask.shape, dtype=np.uint8)
    center = (int(round(x + ww * 0.5)), int(round(y + hh * 0.52)))
    axes = (max(4, int(round(ww * 0.40))), max(5, int(round(hh * 0.46))))
    cv2.ellipse(face, center, axes, 0, 0, 360, 1, -1)
    face &= (subject_mask > 0).astype(np.uint8)
    if int(face.sum()) < 24:
        return StructureFaceResult(False, "face_area_gate")

    return StructureFaceResult(
        True,
        "ok",
        mask=face,
        bbox=(x, y, ww, hh),
        score=score,
        skin_density=skin_density,
    )
