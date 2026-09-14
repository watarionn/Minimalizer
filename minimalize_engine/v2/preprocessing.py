from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.types import ImageBundle

DEFAULT_ANALYSIS_MAX_SIDE = 768
DEFAULT_L0_LAMBDA = 0.010
DEFAULT_L0_KAPPA = 2.0
DEFAULT_EDGE_PERCENTILE = 99.0


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
    l0_lambda: float = DEFAULT_L0_LAMBDA,
    l0_kappa: float = DEFAULT_L0_KAPPA,
) -> ImageBundle:
    source = _validate_rgb(source_rgb)
    analysis_rgb, scale_x, scale_y = resize_for_analysis(
        source,
        max_side=analysis_max_side,
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
    source_shape = source.shape[:2]
    analysis_shape = analysis_rgb.shape[:2]
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
        alpha=_resize_optional_map(alpha, source_shape, analysis_shape),
        scale_x=scale_x,
        scale_y=scale_y,
    )
