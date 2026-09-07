from __future__ import annotations

import cv2
import numpy as np

from ..models import Region
from .part_types import SideHint


def get_subject_bbox(alpha_mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(alpha_mask > 0)
    if len(xs) == 0:
        return (0, 0, alpha_mask.shape[1], alpha_mask.shape[0])
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    return (x0, y0, x1 - x0 + 1, y1 - y0 + 1)


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    return get_subject_bbox(mask)


def mask_centroid(mask: np.ndarray) -> tuple[float, float]:
    ys, xs = np.nonzero(mask > 0)
    if len(xs) == 0:
        return (mask.shape[1] / 2.0, mask.shape[0] / 2.0)
    return (float(xs.mean()), float(ys.mean()))


def normalize_bbox(
    bbox: tuple[int, int, int, int],
    image_shape: tuple[int, ...],
) -> tuple[float, float, float, float]:
    h, w = image_shape[:2]
    x, y, bw, bh = bbox
    return (x / w, y / h, bw / w, bh / h)


def estimate_body_axis_x(subject_mask: np.ndarray) -> float:
    h, w = subject_mask.shape[:2]
    ys, xs = np.nonzero(subject_mask > 0)
    if len(xs) == 0:
        return w / 2.0

    # Central/lower pixels are more stable than raised hands, hats, or weapons.
    y0 = int(np.percentile(ys, 25))
    y1 = int(np.percentile(ys, 88))
    keep = (ys >= y0) & (ys <= y1)
    core_xs = xs[keep]
    if len(core_xs) < 8:
        core_xs = xs
    return float(np.median(core_xs))


def estimate_head_bbox_from_distance(
    subject_mask: np.ndarray,
    subject_bbox: tuple[int, int, int, int],
    body_axis_x: float,
    preset: str,
) -> tuple[int, int, int, int]:
    """
    Find a head-like dense blob near the upper central part of the subject.

    Distance transform makes this robust to raised arms: a hand/weapon is thin,
    while a head usually contains a wider filled disk.
    """
    h, w = subject_mask.shape[:2]
    x, y, bw, bh = subject_bbox
    dist = cv2.distanceTransform((subject_mask > 0).astype(np.uint8), cv2.DIST_L2, 5)

    upper = np.zeros_like(dist)
    top = y
    bottom_ratio = {
        "portrait": 0.62,
        "upper_body": 0.52,
        "full_body": 0.40,
        "chibi": 0.48,
    }.get(preset, 0.46)
    bottom = min(h, y + int(round(bh * bottom_ratio)))

    x_margin = bw * (0.42 if preset == "portrait" else 0.34)
    xa = max(0, int(round(body_axis_x - x_margin)))
    xb = min(w, int(round(body_axis_x + x_margin)))

    upper[top:bottom, xa:xb] = dist[top:bottom, xa:xb]
    yy, xx = np.indices(upper.shape)
    horizontal_penalty = 1.0 - np.clip(
        np.abs(xx - body_axis_x) / max(bw * 0.42, 1.0),
        0.0,
        0.72,
    )
    vertical_norm = np.clip((yy - y) / max(bh, 1), 0.0, 1.0)
    vertical_bonus = 1.0 - 0.45 * vertical_norm
    score = upper * horizontal_penalty * vertical_bonus

    cy, cx = np.unravel_index(int(np.argmax(score)), score.shape)
    radius = float(dist[cy, cx])

    if radius < 2.0:
        # Geometry fallback.
        head_h_ratio = {
            "portrait": 0.38,
            "upper_body": 0.30,
            "full_body": 0.20,
            "chibi": 0.30,
        }.get(preset, 0.24)
        hh = max(8, int(round(bh * head_h_ratio)))
        hw = max(8, int(round(hh * 0.90)))
        cx = int(round(body_axis_x))
        cy = y + hh // 2
    else:
        hh = max(10, int(round(radius * 4.2)))
        hw = max(10, int(round(radius * 3.7)))
        # Avoid implausibly huge heads caused by sleeves/coat masses.
        hh = min(hh, max(10, int(round(bh * 0.34))))
        hw = min(hw, max(10, int(round(bw * 0.52))))

    x0 = max(x, int(round(cx - hw / 2)))
    y0 = max(y, int(round(cy - hh / 2)))
    x1 = min(x + bw, int(round(cx + hw / 2)))
    y1 = min(y + bh, int(round(cy + hh / 2)))
    return (x0, y0, max(1, x1 - x0), max(1, y1 - y0))


def estimate_head_zone(
    subject_bbox: tuple[int, int, int, int],
    preset: str,
) -> tuple[int, int, int, int]:
    x, y, w, h = subject_bbox
    ratio = {
        "portrait": 0.42,
        "upper_body": 0.34,
        "full_body": 0.23,
        "chibi": 0.34,
    }.get(preset, 0.27)
    hh = max(1, int(round(h * ratio)))
    hw = min(w, max(1, int(round(hh * 0.95))))
    return (x + (w - hw) // 2, y, hw, hh)


def estimate_face_zone(
    head_bbox: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    x, y, w, h = head_bbox
    return (
        x + int(round(w * 0.18)),
        y + int(round(h * 0.18)),
        max(1, int(round(w * 0.64))),
        max(1, int(round(h * 0.66))),
    )


def estimate_torso_zone(
    subject_bbox: tuple[int, int, int, int],
    head_bbox: tuple[int, int, int, int],
    preset: str,
    body_axis_x: float | None = None,
) -> tuple[int, int, int, int]:
    sx, sy, sw, sh = subject_bbox
    hx, hy, hw, hh = head_bbox
    axis = body_axis_x if body_axis_x is not None else sx + sw / 2

    top = min(sy + sh - 1, hy + int(round(hh * 0.72)))
    bottom_ratio = {
        "portrait": 0.96,
        "upper_body": 0.83,
        "full_body": 0.58,
        "chibi": 0.67,
    }.get(preset, 0.62)
    bottom = sy + int(round(sh * bottom_ratio))
    width_ratio = {
        "portrait": 0.76,
        "upper_body": 0.58,
        "full_body": 0.42,
        "chibi": 0.54,
    }.get(preset, 0.48)
    tw = max(hw, int(round(sw * width_ratio)))
    x0 = int(round(axis - tw / 2))
    x0 = max(sx, min(x0, sx + sw - tw))
    return (x0, top, min(tw, sw), max(1, bottom - top))


def estimate_leg_zone(
    subject_bbox: tuple[int, int, int, int],
    torso_bbox: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    sx, sy, sw, sh = subject_bbox
    tx, ty, tw, th = torso_bbox
    top = max(sy, ty + int(round(th * 0.70)))
    return (sx, top, sw, max(1, sy + sh - top))


def split_mask_by_vertical_axis(
    mask: np.ndarray,
    axis_x: float,
) -> tuple[np.ndarray, np.ndarray]:
    left = np.zeros_like(mask, dtype=np.uint8)
    right = np.zeros_like(mask, dtype=np.uint8)
    cut = int(round(axis_x))
    left[:, :cut] = mask[:, :cut]
    right[:, cut:] = mask[:, cut:]
    return left, right


def bbox_overlap_ratio(
    a: tuple[int, int, int, int],
    b: tuple[int, int, int, int],
) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x0, y0 = max(ax, bx), max(ay, by)
    x1, y1 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    denom = max(1, min(aw * ah, bw * bh))
    return float(inter / denom)


def mask_overlap_ratio(a: np.ndarray, b: np.ndarray) -> float:
    aa = a > 0
    bb = b > 0
    denom = max(1, int(np.count_nonzero(aa)))
    return float(np.count_nonzero(aa & bb) / denom)


def estimate_side_hint(
    centroid: tuple[float, float],
    body_axis_x: float,
    tolerance_ratio: float = 0.04,
    subject_width: float | None = None,
) -> SideHint:
    tol = (subject_width or 100.0) * tolerance_ratio
    if centroid[0] < body_axis_x - tol:
        return "left"
    if centroid[0] > body_axis_x + tol:
        return "right"
    return "center"


def is_elongated_region(
    bbox: tuple[int, int, int, int],
    threshold: float = 2.4,
) -> bool:
    _, _, w, h = bbox
    ratio = max(w, h) / max(1.0, min(w, h))
    return ratio >= threshold


def is_prop_like_region(
    region: Region,
    subject_bbox: tuple[int, int, int, int],
    body_axis_x: float,
) -> float:
    x, y, w, h = region.bbox
    sx, sy, sw, sh = subject_bbox
    aspect = max(w, h) / max(1.0, min(w, h))
    cx, cy = region.centroid
    lateral = abs(cx - body_axis_x) / max(sw / 2.0, 1.0)

    score = 0.0
    if aspect >= 3.2:
        score += 0.42
    elif aspect >= 2.2:
        score += 0.22
    if lateral >= 0.55:
        score += 0.24
    if region.semantic_type == "elongated":
        score += 0.22
    if 0.0005 <= region.area_ratio <= 0.04:
        score += 0.10
    if region.is_accent:
        score -= 0.08

    # Lower-body elongated regions are usually shoes, boots, coat tails, or
    # split-leg clothing rather than held props.
    if cy > sy + sh * 0.78:
        score *= 0.30

    return float(np.clip(score, 0.0, 1.0))
