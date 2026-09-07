from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class LoadedImage:
    rgb: np.ndarray
    alpha: np.ndarray | None = None

    @property
    def has_transparency(self) -> bool:
        return self.alpha is not None and bool(np.any(self.alpha < 250))


def load_image_bundle(
    path: str | Path,
    alpha_background: tuple[int, int, int] = (255, 255, 255),
) -> LoadedImage:
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"Could not read image: {path}")

    if image.ndim == 2:
        return LoadedImage(cv2.cvtColor(image, cv2.COLOR_GRAY2RGB), None)

    if image.shape[2] == 4:
        raw_rgb = cv2.cvtColor(image[:, :, :3], cv2.COLOR_BGR2RGB).astype(np.float32)
        alpha = image[:, :, 3].copy()
        a = (alpha.astype(np.float32) / 255.0)[:, :, None]
        bg = np.asarray(alpha_background, dtype=np.float32)[None, None, :]
        composite = np.clip(np.round(raw_rgb * a + bg * (1.0 - a)), 0, 255).astype(np.uint8)
        return LoadedImage(composite, alpha)

    return LoadedImage(cv2.cvtColor(image[:, :, :3], cv2.COLOR_BGR2RGB), None)


def load_image_data(path: str | Path) -> LoadedImage:
    return load_image_bundle(path)


def composite_alpha(rgb, alpha, background=(255, 255, 255)):
    if alpha is None:
        return rgb.copy()
    a = alpha.astype(np.float32)[..., None] / 255.0
    bg = np.empty_like(rgb, dtype=np.float32)
    bg[:] = np.asarray(background, dtype=np.float32)
    return np.clip(
        np.round(rgb.astype(np.float32) * a + bg * (1.0 - a)),
        0,
        255,
    ).astype(np.uint8)


def load_image(path: str | Path) -> np.ndarray:
    return load_image_bundle(path).rgb
