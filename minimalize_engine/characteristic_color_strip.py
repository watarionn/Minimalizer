from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from .color_strip import (
    ANALYSIS_MAX_SIDE,
    DEFAULT_COLOR_COUNT,
    DEFAULT_ORIENTATION,
    DEFAULT_ORDER,
    DEFAULT_SIZE_MODE,
    OUTPUT_MAX_SIDE,
    ColorStripColor,
    ColorStripDocument,
    ColorStripOrientation,
    ColorStripOrder,
    ColorStripSizeMode,
)
from .palette.feature_palette import extract_feature_palette, rgb_to_lab


def _fit_size(width: int, height: int, max_side: int) -> tuple[int, int]:
    if max(width, height) <= max_side:
        return width, height
    scale = max_side / max(width, height)
    return max(1, round(width * scale)), max(1, round(height * scale))


def _reassign_counts(
    rgb_pixels: np.ndarray,
    selected_rgbs: list[tuple[int, int, int]],
) -> list[int]:
    if not selected_rgbs:
        return []

    centers = np.asarray(selected_rgbs, dtype=np.float64)
    center_labs = rgb_to_lab(centers)
    pixel_labs = rgb_to_lab(rgb_pixels)
    distances = np.linalg.norm(pixel_labs[:, None, :] - center_labs[None, :, :], axis=2)
    assignments = np.argmin(distances, axis=1)
    return np.bincount(assignments, minlength=len(selected_rgbs)).astype(int).tolist()


def extract_characteristic_color_strip(
    input_path: str | Path,
    *,
    color_count: int = DEFAULT_COLOR_COUNT,
    size_mode: ColorStripSizeMode = DEFAULT_SIZE_MODE,
    order: ColorStripOrder = DEFAULT_ORDER,
    orientation: ColorStripOrientation = DEFAULT_ORIENTATION,
    analysis_max_side: int = ANALYSIS_MAX_SIDE,
    output_max_side: int = OUTPUT_MAX_SIDE,
    remove_background: bool = True,
) -> ColorStripDocument:
    """Build a ColorStripDocument from the AI-free feature-palette selector.

    This is intentionally a separate bridge from ``extract_color_strip`` so the
    existing dominant/featured Color Strip behavior stays backward-compatible
    while Minimalizer can evaluate characteristic-color selection in production.
    """
    if not 3 <= color_count <= 5:
        raise ValueError("Characteristic Color Strip color_count must be between 3 and 5.")
    if size_mode not in {"equal", "proportional"}:
        raise ValueError("Characteristic Color Strip size_mode must be equal or proportional.")
    if order not in {"least_first", "most_first"}:
        raise ValueError("Characteristic Color Strip order must be least_first or most_first.")
    if orientation not in {"vertical", "horizontal"}:
        raise ValueError("Characteristic Color Strip orientation must be vertical or horizontal.")

    with Image.open(input_path) as source:
        source_width, source_height = source.size
        rgba = source.convert("RGBA")

    analysis_width, analysis_height = _fit_size(source_width, source_height, analysis_max_side)
    if (analysis_width, analysis_height) != (source_width, source_height):
        rgba = rgba.resize((analysis_width, analysis_height), Image.Resampling.NEAREST)

    pixels = np.asarray(rgba, dtype=np.uint8)
    visible = pixels[..., 3] > 20
    rgb_pixels = pixels[..., :3][visible]
    if rgb_pixels.size == 0:
        raise ValueError("Characteristic Color Strip requires at least one visible pixel.")

    selected = extract_feature_palette(
        rgba,
        n_colors=color_count,
        remove_background=remove_background,
    )
    if remove_background and len(selected) < color_count:
        fallback = extract_feature_palette(
            rgba,
            n_colors=color_count,
            remove_background=False,
        )
        selected_rgbs = {color.rgb for color in selected}
        for color in fallback:
            if color.rgb in selected_rgbs:
                continue
            selected.append(color)
            selected_rgbs.add(color.rgb)
            if len(selected) >= color_count:
                break
    if not selected:
        raise ValueError("Characteristic Color Strip could not select representative colors.")

    selected_rgbs = [color.rgb for color in selected[:color_count]]
    selected = selected[:color_count]
    counts = _reassign_counts(rgb_pixels, selected_rgbs)
    total_visible = len(rgb_pixels)

    pairs = list(zip(counts, selected, strict=True))
    reverse = order == "most_first"
    pairs.sort(key=lambda pair: pair[0], reverse=reverse)

    colors = tuple(
        ColorStripColor(
            rgb=feature.rgb,
            pixel_count=int(count),
            share=float(count) / total_visible,
        )
        for count, feature in pairs
        if count > 0
    )

    output_width, output_height = _fit_size(source_width, source_height, output_max_side)
    return ColorStripDocument(
        source_width=source_width,
        source_height=source_height,
        analysis_width=analysis_width,
        analysis_height=analysis_height,
        output_width=output_width,
        output_height=output_height,
        colors=colors,
        similarity=0.0,
        size_mode=size_mode,
        order=order,
        orientation=orientation,
        selection_mode="featured",
    )
