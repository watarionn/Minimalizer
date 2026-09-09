from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .io.image_loader import load_image_data


@dataclass
class OpaqueSubjectRescue:
    enabled: bool
    reason: str
    rgba: np.ndarray | None = None
    background_rgb: tuple[int, int, int] | None = None
    border_dominant_fraction: float = 0.0
    foreground_area_ratio: float = 0.0
    center_fill_ratio: float = 0.0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "background_rgb": list(self.background_rgb) if self.background_rgb is not None else None,
            "border_dominant_fraction": round(float(self.border_dominant_fraction), 6),
            "foreground_area_ratio": round(float(self.foreground_area_ratio), 6),
            "center_fill_ratio": round(float(self.center_fill_ratio), 6),
        }

def _source_rgba(image_or_path) -> tuple[np.ndarray, np.ndarray | None]:
    if isinstance(image_or_path, (str, Path)):
        data = load_image_data(image_or_path)
        return data.rgb, data.alpha
    arr = np.asarray(image_or_path)
    if arr.ndim != 3 or arr.shape[2] not in {3, 4}:
        raise ValueError("image array must be HxWx3 or HxWx4")
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3] if arr.shape[2] == 4 else None
    return rgb, alpha


def _border_pixels(rgb: np.ndarray, ratio: float = 0.04) -> np.ndarray:
    h, w = rgb.shape[:2]
    border = max(2, int(round(min(h, w) * ratio)))
    return np.concatenate([
        rgb[:border].reshape(-1, 3),
        rgb[h - border :].reshape(-1, 3),
        rgb[border : h - border, :border].reshape(-1, 3),
        rgb[border : h - border, w - border :].reshape(-1, 3),
    ])


def _background_prototypes(border: np.ndarray) -> tuple[list[np.ndarray], list[tuple[int, int, int]], float]:
    bins = (border // 24).astype(np.int16)
    keys = bins[:, 0] * 121 + bins[:, 1] * 11 + bins[:, 2]
    values, counts = np.unique(keys, return_counts=True)
    order = np.argsort(counts)[::-1]
    prototypes: list[np.ndarray] = []
    colors: list[tuple[int, int, int]] = []
    dominant = 0.0
    total = max(len(border), 1)
    for rank, idx in enumerate(order[:8]):
        selected = keys == values[idx]
        fraction = float(counts[idx]) / float(total)
        if rank == 0:
            dominant = fraction
        if prototypes and fraction < 0.08:
            break
        color = np.median(border[selected], axis=0).astype(np.uint8)
        lab = cv2.cvtColor(color.reshape(1, 1, 3), cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
        prototypes.append(lab)
        colors.append(tuple(int(x) for x in color))
    return prototypes, colors, dominant


def prepare_rinka_opaque_subject_input(image_or_path) -> OpaqueSubjectRescue:
    rgb, alpha = _source_rgba(image_or_path)
    if alpha is not None and bool(np.any(alpha < 250)):
        occupancy = float((alpha >= 16).mean())
        if 0.025 <= occupancy <= 0.96:
            return OpaqueSubjectRescue(False, "alpha_subject")
    h, w = rgb.shape[:2]
    aspect = min(h, w) / max(float(max(h, w)), 1.0)
    if aspect < 0.88:
        return OpaqueSubjectRescue(False, "aspect_gate")

    border = _border_pixels(rgb)
    prototypes, colors, dominant = _background_prototypes(border)
    if not prototypes or dominant < 0.30:
        return OpaqueSubjectRescue(False, "border_gate", border_dominant_fraction=dominant)

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    centers = np.stack(prototypes)
    distance = np.linalg.norm(lab[:, :, None, :] - centers[None, None, :, :], axis=3).min(axis=2)
    mask = (distance > 24.0).astype(np.uint8)
    kernel = max(3, int(round(min(h, w) * 0.014)))
    if kernel % 2 == 0:
        kernel += 1
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((kernel, kernel), np.uint8))
    open_kernel = max(3, int(round(min(h, w) * 0.006)))
    if open_kernel % 2 == 0:
        open_kernel += 1
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((open_kernel, open_kernel), np.uint8))

    area_ratio = float(mask.mean())
    if not 0.20 <= area_ratio <= 0.72:
        return OpaqueSubjectRescue(False, "area_gate", background_rgb=colors[0], border_dominant_fraction=dominant, foreground_area_ratio=area_ratio)
    center = mask[int(h * 0.20) : int(h * 0.80), int(w * 0.20) : int(w * 0.80)]
    center_fill = float(center.mean()) if center.size else 0.0
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return OpaqueSubjectRescue(False, "empty_mask", background_rgb=colors[0], border_dominant_fraction=dominant)
    cx, cy = float(xs.mean()), float(ys.mean())
    center_distance = float(np.hypot((cx - w * 0.5) / max(w * 0.5, 1.0), (cy - h * 0.5) / max(h * 0.5, 1.0)))
    if center_fill < 0.28 or center_distance > 0.40:
        return OpaqueSubjectRescue(False, "center_gate", background_rgb=colors[0], border_dominant_fraction=dominant, foreground_area_ratio=area_ratio, center_fill_ratio=center_fill)

    rgba = np.dstack([rgb, mask.astype(np.uint8) * 255])
    return OpaqueSubjectRescue(True, "accepted", rgba=rgba, background_rgb=colors[0], border_dominant_fraction=dominant, foreground_area_ratio=area_ratio, center_fill_ratio=center_fill)
