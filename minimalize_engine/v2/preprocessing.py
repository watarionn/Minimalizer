from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.types import ImageBundle

DEFAULT_ANALYSIS_MAX_SIDE = 768
DEFAULT_L0_LAMBDA = 0.010
DEFAULT_L0_KAPPA = 2.0
DEFAULT_EDGE_PERCENTILE = 99.0


@dataclass(frozen=True, slots=True)
class ShadingFlattenConfig:
    enabled: bool = False
    sr: int = 55
    max_level: int = 1
    sp_ratio: float = 0.015
    sp_min: int = 3
    sp_max: int = 60
    preserve_alpha_edges: bool = True

    def __post_init__(self) -> None:
        if self.sr <= 0:
            raise ValueError("shading flatten sr must be positive")
        if self.max_level < 0:
            raise ValueError("shading flatten max_level must be non-negative")
        if not np.isfinite(self.sp_ratio) or self.sp_ratio <= 0.0:
            raise ValueError("shading flatten sp_ratio must be finite and positive")
        if self.sp_min <= 0 or self.sp_max < self.sp_min:
            raise ValueError("shading flatten sp bounds must be positive and ordered")


def compute_shading_flatten_sp(
    height: int,
    width: int,
    *,
    sp_ratio: float = 0.015,
    sp_min: int = 3,
    sp_max: int = 60,
) -> int:
    if height <= 0 or width <= 0:
        raise ValueError("image dimensions must be positive")
    if not np.isfinite(sp_ratio) or sp_ratio <= 0.0:
        raise ValueError("sp_ratio must be finite and positive")
    if sp_min <= 0 or sp_max < sp_min:
        raise ValueError("sp bounds must be positive and ordered")
    short_side = min(int(height), int(width))
    value = int(round(short_side * float(sp_ratio)))
    return max(int(sp_min), min(int(sp_max), value))


def flatten_shading_rgb(
    rgb: NDArray[np.uint8],
    *,
    alpha: NDArray[np.floating] | None = None,
    config: ShadingFlattenConfig | None = None,
) -> NDArray[np.uint8]:
    image = _validate_rgb(rgb)
    active = config or ShadingFlattenConfig(enabled=True)
    if not active.enabled:
        return image.copy()

    work = np.ascontiguousarray(image[:, :, ::-1])
    transparent: NDArray[np.bool_] | None = None
    if alpha is not None:
        alpha_map = np.asarray(alpha, dtype=np.float32)
        if alpha_map.shape != image.shape[:2]:
            raise ValueError("shading flatten alpha must match image dimensions")
        if not np.all(np.isfinite(alpha_map)):
            raise ValueError("shading flatten alpha must be finite")
        alpha_map = np.clip(alpha_map, 0.0, 1.0)
        transparent = alpha_map <= 0.0
        if active.preserve_alpha_edges and transparent.any() and not transparent.all():
            mask = transparent.astype(np.uint8) * 255
            work = cv2.inpaint(work, mask, 3, cv2.INPAINT_TELEA)

    sp = compute_shading_flatten_sp(
        image.shape[0],
        image.shape[1],
        sp_ratio=active.sp_ratio,
        sp_min=active.sp_min,
        sp_max=active.sp_max,
    )
    shifted = cv2.pyrMeanShiftFiltering(
        np.ascontiguousarray(work),
        sp=sp,
        sr=int(active.sr),
        maxLevel=int(active.max_level),
    )
    flattened = np.ascontiguousarray(shifted[:, :, ::-1])
    if transparent is not None and transparent.any():
        # Inpainting exists only to keep transparent pixels from polluting the
        # Mean Shift boundary. Those synthetic colors must never become V2
        # analysis regions, so restore the original hidden RGB afterwards.
        flattened[transparent] = image[transparent]
    return flattened


def _validate_rgb(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    array = np.asarray(image)
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError("RGB image must have shape (H, W, 3)")
    if array.dtype != np.uint8:
        raise TypeError("RGB image must use uint8")
    if array.shape[0] <= 0 or array.shape[1] <= 0:
        raise ValueError("RGB image must not be empty")
    return array


def resize_for_analysis(
    source_rgb: NDArray[np.uint8],
    *,
    max_side: int = DEFAULT_ANALYSIS_MAX_SIDE,
) -> tuple[NDArray[np.uint8], float, float]:
    source = _validate_rgb(source_rgb)
    if max_side <= 0:
        raise ValueError("max_side must be positive")
    height, width = source.shape[:2]
    if max(height, width) <= max_side:
        return source.copy(), 1.0, 1.0

    scale = max_side / float(max(height, width))
    analysis_width = max(1, int(round(width * scale)))
    analysis_height = max(1, int(round(height * scale)))
    resized = cv2.resize(
        source,
        (analysis_width, analysis_height),
        interpolation=cv2.INTER_AREA,
    )
    return (
        resized.astype(np.uint8, copy=False),
        width / float(analysis_width),
        height / float(analysis_height),
    )


def rgb_to_canonical_lab(rgb: NDArray[np.uint8]) -> NDArray[np.float32]:
    image = _validate_rgb(rgb)
    rgb01 = image.astype(np.float32) / 255.0
    lab = cv2.cvtColor(rgb01, cv2.COLOR_RGB2LAB)
    return lab.astype(np.float32, copy=False)


def l0_gradient_smooth(
    rgb: NDArray[np.uint8],
    *,
    lambda_: float = DEFAULT_L0_LAMBDA,
    kappa: float = DEFAULT_L0_KAPPA,
    beta_max: float = 1.0e5,
) -> NDArray[np.uint8]:
    image = _validate_rgb(rgb)
    if lambda_ <= 0.0:
        raise ValueError("lambda_ must be positive")
    if kappa <= 1.0:
        raise ValueError("kappa must be greater than 1")
    if beta_max <= 0.0:
        raise ValueError("beta_max must be positive")

    source = image.astype(np.float64) / 255.0
    height, width = source.shape[:2]
    fy = np.arange(height, dtype=np.float64) / max(height, 1)
    fx = np.arange(width, dtype=np.float64) / max(width, 1)
    denominator = (
        4.0 * np.sin(np.pi * fy)[:, None] ** 2
        + 4.0 * np.sin(np.pi * fx)[None, :] ** 2
    )
    source_fft = np.fft.fft2(source, axes=(0, 1))
    result = source.copy()
    beta = 2.0 * lambda_

    while beta < beta_max:
        h = np.roll(result, -1, axis=1) - result
        v = np.roll(result, -1, axis=0) - result
        small = np.sum(h * h + v * v, axis=2) < (lambda_ / beta)
        h[small] = 0.0
        v[small] = 0.0
        divergence = (
            np.roll(h, 1, axis=1) - h
            + np.roll(v, 1, axis=0) - v
        )
        divergence_fft = np.fft.fft2(divergence, axes=(0, 1))
        solved = (
            source_fft + beta * divergence_fft
        ) / (1.0 + beta * denominator[:, :, None])
        result = np.real(np.fft.ifft2(solved, axes=(0, 1)))
        beta *= kappa

    result = np.clip(result, 0.0, 1.0)
    return np.rint(result * 255.0).astype(np.uint8)


def lab_edge_map(
    lab: NDArray[np.floating],
    *,
    percentile: float = DEFAULT_EDGE_PERCENTILE,
) -> NDArray[np.float32]:
    array = np.asarray(lab, dtype=np.float32)
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError("Lab image must have shape (H, W, 3)")
    if not 0.0 < percentile <= 100.0:
        raise ValueError("percentile must be in (0, 100]")
    gx_channels = []
    gy_channels = []
    for channel in range(3):
        plane = array[:, :, channel]
        gx_channels.append(cv2.Sobel(plane, cv2.CV_32F, 1, 0, ksize=3))
        gy_channels.append(cv2.Sobel(plane, cv2.CV_32F, 0, 1, ksize=3))
    gx = np.stack(gx_channels, axis=2)
    gy = np.stack(gy_channels, axis=2)
    magnitude = np.sqrt(np.sum(gx * gx + gy * gy, axis=2, dtype=np.float32))
    finite = magnitude[np.isfinite(magnitude)]
    if finite.size == 0:
        return np.zeros(magnitude.shape, dtype=np.float32)
    scale = float(np.percentile(finite, percentile))
    if scale <= 1.0e-12:
        return np.zeros(magnitude.shape, dtype=np.float32)
    return np.clip(magnitude / scale, 0.0, 1.0).astype(np.float32)


def _resize_optional_map(
    value: NDArray[np.floating] | None,
    source_shape: tuple[int, int],
    analysis_shape: tuple[int, int],
) -> NDArray[np.float32] | None:
    if value is None:
        return None
    array = np.asarray(value, dtype=np.float32)
    if array.shape != source_shape:
        raise ValueError(f"optional map must have source shape {source_shape}")
    if source_shape == analysis_shape:
        return array.copy()
    height, width = analysis_shape
    resized = cv2.resize(array, (width, height), interpolation=cv2.INTER_AREA)
    return np.clip(resized, 0.0, 1.0).astype(np.float32)


def build_image_bundle(
    source_rgb: NDArray[np.uint8],
    *,
    subject_prob: NDArray[np.floating] | None = None,
    subject_confidence: NDArray[np.floating] | None = None,
    alpha: NDArray[np.floating] | None = None,
    analysis_max_side: int = DEFAULT_ANALYSIS_MAX_SIDE,
    shading_flatten: ShadingFlattenConfig | None = None,
    l0_lambda: float = DEFAULT_L0_LAMBDA,
    l0_kappa: float = DEFAULT_L0_KAPPA,
) -> ImageBundle:
    source = _validate_rgb(source_rgb)
    analysis_rgb, scale_x, scale_y = resize_for_analysis(
        source,
        max_side=analysis_max_side,
    )
    source_shape = source.shape[:2]
    analysis_shape = analysis_rgb.shape[:2]
    analysis_alpha = _resize_optional_map(alpha, source_shape, analysis_shape)
    if shading_flatten is not None and shading_flatten.enabled:
        analysis_rgb = flatten_shading_rgb(
            analysis_rgb,
            alpha=analysis_alpha,
            config=shading_flatten,
        )
    structural_rgb = l0_gradient_smooth(
        analysis_rgb,
        lambda_=l0_lambda,
        kappa=l0_kappa,
    )
    analysis_lab = rgb_to_canonical_lab(analysis_rgb)
    structural_lab = rgb_to_canonical_lab(structural_rgb)
    edge_raw = lab_edge_map(analysis_lab)
    edge_structural = lab_edge_map(structural_lab)
    return ImageBundle(
        source_rgb=source.copy(),
        analysis_rgb=analysis_rgb,
        structural_rgb=structural_rgb,
        analysis_lab=analysis_lab,
        structural_lab=structural_lab,
        edge_raw=edge_raw,
        edge_structural=edge_structural,
        subject_prob=_resize_optional_map(subject_prob, source_shape, analysis_shape),
        subject_confidence=_resize_optional_map(
            subject_confidence,
            source_shape,
            analysis_shape,
        ),
        alpha=analysis_alpha,
        scale_x=scale_x,
        scale_y=scale_y,
    )
