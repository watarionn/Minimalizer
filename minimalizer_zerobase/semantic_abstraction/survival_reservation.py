from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import cv2
import numpy as np


@dataclass(frozen=True)
class SurvivalReservation:
    reservation_id: str
    part_id: str
    mask: np.ndarray
    color: tuple[int, int, int]
    area_ratio: float
    cx: float
    cy: float
    priority: float


def _quantized_key(pixel: np.ndarray, step: int) -> tuple[int, int, int]:
    return tuple(int((int(v) // step) * step + step // 2) for v in pixel[:3])


def reserve_semantic_survival_signatures(
    rgb: np.ndarray,
    part_masks: Mapping[str, np.ndarray],
    *,
    max_reservations: int = 8,
    quantization_step: int = 32,
    min_subject_ratio: float = 0.002,
    max_subject_ratio: float = 0.035,
) -> tuple[SurvivalReservation, ...]:
    """Reserve compact source-supported signatures before geometry compression.

    Reservations are derived only from source pixels and authorized semantic masks.
    They contain no Golden, case-specific feature names, coordinates, or colors.
    """
    image = np.asarray(rgb, dtype=np.uint8)
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("rgb must be HxWx3")
    h, w = image.shape[:2]
    masks = {k: np.asarray(v, dtype=bool) for k, v in part_masks.items()}
    if any(v.shape != (h, w) for v in masks.values()):
        raise ValueError("part mask shape mismatch")

    subject = np.zeros((h, w), dtype=bool)
    for mask in masks.values():
        subject |= mask
    subject_area = max(1, h * w)
    rows: list[SurvivalReservation] = []

    for part_id in sorted(masks):
        authority = masks[part_id]
        if not np.any(authority):
            continue
        part_pixels = image[authority]
        base = np.median(part_pixels, axis=0).astype(float)
        keys = np.zeros((h, w), dtype=np.int32)
        for y, x in zip(*np.where(authority)):
            q = _quantized_key(image[y, x], quantization_step)
            keys[y, x] = (q[0] << 16) | (q[1] << 8) | q[2]

        seen = np.zeros((h, w), dtype=bool)
        for sy, sx in zip(*np.where(authority)):
            if seen[sy, sx]:
                continue
            key = keys[sy, sx]
            stack = [(int(sy), int(sx))]
            seen[sy, sx] = True
            pts: list[tuple[int, int]] = []
            while stack:
                y, x = stack.pop()
                pts.append((y, x))
                for ny, nx in ((y - 1, x), (y, x - 1), (y, x + 1), (y + 1, x)):
                    if 0 <= ny < h and 0 <= nx < w and authority[ny, nx] and not seen[ny, nx] and keys[ny, nx] == key:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            ratio = len(pts) / subject_area
            if not (min_subject_ratio <= ratio <= max_subject_ratio):
                continue
            yy = np.fromiter((p[0] for p in pts), dtype=int)
            xx = np.fromiter((p[1] for p in pts), dtype=int)
            color = np.median(image[yy, xx], axis=0).astype(int)
            contrast = float(np.linalg.norm(color.astype(float) - base))
            chroma = float(color.max() - color.min())
            if contrast < 38.0 and chroma < 32.0:
                continue
            mask = np.zeros((h, w), dtype=bool)
            mask[yy, xx] = True
            cx = float(xx.mean() / max(1, w - 1))
            cy = float(yy.mean() / max(1, h - 1))
            priority = ratio * (1.0 + contrast / 255.0 + chroma / 510.0)
            rows.append(SurvivalReservation(
                reservation_id=f"{part_id}:{len(rows)}",
                part_id=part_id,
                mask=mask,
                color=tuple(int(v) for v in color),
                area_ratio=round(float(ratio), 9),
                cx=round(cx, 9),
                cy=round(cy, 9),
                priority=round(priority, 12),
            ))

    rows.sort(key=lambda r: (-r.priority, r.part_id, r.color, r.cy, r.cx))
    selected = rows[:max_reservations]
    return tuple(
        SurvivalReservation(
            reservation_id=f"survival:{i}",
            part_id=r.part_id,
            mask=r.mask,
            color=r.color,
            area_ratio=r.area_ratio,
            cx=r.cx,
            cy=r.cy,
            priority=r.priority,
        )
        for i, r in enumerate(selected)
    )
