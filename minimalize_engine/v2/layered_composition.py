from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.person_parts import PersonPartPartition


@dataclass(frozen=True, slots=True)
class LayeredCompositionConfig:
    background_color_count: int = 3
    background_blur_sigma: float = 5.0
    seam_fallback_radius: int = 1

    def __post_init__(self) -> None:
        if self.background_color_count < 1:
            raise ValueError("background_color_count must be positive")
        if not np.isfinite(self.background_blur_sigma) or self.background_blur_sigma < 0.0:
            raise ValueError("background_blur_sigma must be finite and non-negative")
        if self.seam_fallback_radius < 0:
            raise ValueError("seam_fallback_radius must be non-negative")


def _quantize_background(
    source_rgb: NDArray[np.uint8],
    background_mask: NDArray[np.bool_],
    config: LayeredCompositionConfig,
) -> NDArray[np.uint8]:
    source = np.asarray(source_rgb, dtype=np.uint8)
    result = source.copy()
    if not background_mask.any():
        return result
    blurred = cv2.GaussianBlur(
        source,
        (0, 0),
        sigmaX=config.background_blur_sigma,
        sigmaY=config.background_blur_sigma,
    ) if config.background_blur_sigma > 0.0 else source
    pixels = blurred[background_mask].reshape(-1, 3).astype(np.float32)
    if len(pixels) <= config.background_color_count:
        result[background_mask] = np.rint(pixels).astype(np.uint8)
        return result
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 20, 0.5)
    _compactness, labels, centers = cv2.kmeans(
        pixels,
        config.background_color_count,
        None,
        criteria,
        3,
        cv2.KMEANS_PP_CENTERS,
    )
    quantized = np.clip(np.rint(centers[labels[:, 0]]), 0, 255).astype(np.uint8)
    result[background_mask] = quantized
    return result




PART_LAYER_ORDER = (
    "left_leg",
    "right_leg",
    "torso",
    "left_arm",
    "right_arm",
    "head",
)


PART_SEAM_PAIRS = (
    ("head", "torso"),
    ("torso", "left_arm"),
    ("torso", "right_arm"),
    ("torso", "left_leg"),
    ("torso", "right_leg"),
)


def _seam_fallback_mask(
    partition: PersonPartPartition,
    part_coverage_masks: dict[str, NDArray[np.bool_]],
    fallback_coverage: NDArray[np.bool_],
    *,
    radius: int,
) -> NDArray[np.bool_]:
    """Find uncovered semantic seam pixels backed by the whole-person scene."""
    result = np.zeros_like(partition.subject_mask)
    if radius <= 0:
        return result
    kernel = np.ones((radius * 2 + 1, radius * 2 + 1), dtype=np.uint8)
    for first, second in PART_SEAM_PAIRS:
        first_mask = partition.part_masks.get(first)
        second_mask = partition.part_masks.get(second)
        if (
            first_mask is None
            or second_mask is None
            or not np.any(first_mask)
            or not np.any(second_mask)
        ):
            continue
        first_coverage = np.asarray(
            part_coverage_masks.get(first, np.zeros_like(first_mask)),
            dtype=np.bool_,
        )
        second_coverage = np.asarray(
            part_coverage_masks.get(second, np.zeros_like(second_mask)),
            dtype=np.bool_,
        )
        if (
            first_coverage.shape != partition.subject_mask.shape
            or second_coverage.shape != partition.subject_mask.shape
        ):
            raise ValueError("part coverage masks must match partition dimensions")
        near_second = cv2.dilate(
            second_mask.astype(np.uint8), kernel, iterations=1
        ).astype(np.bool_)
        near_first = cv2.dilate(
            first_mask.astype(np.uint8), kernel, iterations=1
        ).astype(np.bool_)
        result |= first_mask & near_second & ~first_coverage
        result |= second_mask & near_first & ~second_coverage

    fallback = np.asarray(fallback_coverage, dtype=np.bool_)
    if fallback.shape != partition.subject_mask.shape:
        raise ValueError("fallback coverage must match partition dimensions")
    return result & partition.subject_mask & fallback


def compose_layered_rgb(
    background_rgb: NDArray[np.uint8],
    partition: PersonPartPartition,
    *,
    part_renders: dict[str, NDArray[np.uint8]],
    part_coverage_masks: dict[str, NDArray[np.bool_]] | None = None,
    subject_fallback_rgb: NDArray[np.uint8] | None = None,
    subject_fallback_coverage: NDArray[np.bool_] | None = None,
    seam_fallback_radius: int = 0,
) -> NDArray[np.uint8]:
    background = np.asarray(background_rgb, dtype=np.uint8)
    if background.ndim != 3 or background.shape[2] != 3:
        raise ValueError("background_rgb must have shape (H, W, 3)")
    if background.shape[:2] != partition.subject_mask.shape:
        raise ValueError("background and partition must have matching dimensions")
    canvas = background.copy()
    painted = np.zeros(partition.subject_mask.shape, dtype=np.bool_)
    for name in PART_LAYER_ORDER:
        mask = partition.part_masks.get(name)
        rendered = part_renders.get(name)
        if mask is None or rendered is None or not mask.any():
            continue
        image = np.asarray(rendered, dtype=np.uint8)
        if image.shape != background.shape:
            raise ValueError(f"{name} render must match background shape")
        canvas[mask] = image[mask]
        painted |= mask
    remainder = partition.subject_mask & ~painted
    fallback = None
    if subject_fallback_rgb is not None:
        fallback = np.asarray(subject_fallback_rgb, dtype=np.uint8)
        if fallback.shape != background.shape:
            raise ValueError("subject fallback must match background shape")
        if remainder.any():
            canvas[remainder] = fallback[remainder]

    if (
        fallback is not None
        and part_coverage_masks is not None
        and subject_fallback_coverage is not None
        and seam_fallback_radius > 0
    ):
        seam_mask = _seam_fallback_mask(
            partition,
            part_coverage_masks,
            subject_fallback_coverage,
            radius=seam_fallback_radius,
        )
        canvas[seam_mask] = fallback[seam_mask]
    return canvas



def render_partitioned_scene(
    scene_rgb: NDArray[np.uint8],
    source_rgb: NDArray[np.uint8],
    partition: PersonPartPartition,
    *,
    part_renders: dict[str, NDArray[np.uint8]] | None = None,
    part_coverage_masks: dict[str, NDArray[np.bool_]] | None = None,
    scene_coverage_mask: NDArray[np.bool_] | None = None,
    config: LayeredCompositionConfig | None = None,
) -> NDArray[np.uint8]:
    """Compose one V2 primitive render through explicit background/person layers.

    Phase 2 intentionally reuses the canonical V2 primitive render for each
    person part. The important invariant is that pixels can only enter the
    final image through their semantic layer mask, so background-colored
    primitives cannot paint over the protected subject silhouette.
    """
    active = config or LayeredCompositionConfig()
    scene = np.asarray(scene_rgb, dtype=np.uint8)
    source = np.asarray(source_rgb, dtype=np.uint8)
    if scene.shape != source.shape or scene.shape[:2] != partition.subject_mask.shape:
        raise ValueError("scene, source, and partition must have matching dimensions")

    background = _quantize_background(source, partition.background_mask, active)
    active_part_renders = part_renders or {
        name: scene
        for name, mask in partition.part_masks.items()
        if mask.any()
    }
    return compose_layered_rgb(
        background,
        partition,
        part_renders=active_part_renders,
        part_coverage_masks=part_coverage_masks,
        subject_fallback_rgb=scene,
        subject_fallback_coverage=scene_coverage_mask,
        seam_fallback_radius=active.seam_fallback_radius,
    )

def render_layered_preview(
    source_rgb: NDArray[np.uint8],
    partition: PersonPartPartition,
    *,
    config: LayeredCompositionConfig | None = None,
) -> NDArray[np.uint8]:
    active = config or LayeredCompositionConfig()
    source = np.asarray(source_rgb, dtype=np.uint8)
    if source.shape[:2] != partition.subject_mask.shape:
        raise ValueError("source and partition must have matching dimensions")
    canvas = _quantize_background(source, partition.background_mask, active)
    # This is intentionally a conservative Phase-1 compositor: it establishes
    # the layer contract while preserving subject pixels. Subsequent phases
    # replace each copied part with its own primitive render.
    canvas[partition.subject_mask] = source[partition.subject_mask]
    return canvas
