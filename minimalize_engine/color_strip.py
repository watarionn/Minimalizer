from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw

COLOR_STRIP_VERSION = "v0.3"
DEFAULT_COLOR_COUNT = 5
DEFAULT_SIMILARITY = 18.0
DEFAULT_SIZE_MODE = "equal"
DEFAULT_ORDER = "least_first"
DEFAULT_ORIENTATION = "vertical"
DEFAULT_SELECTION_MODE = "dominant"
MIN_COLOR_COUNT = 3
MAX_COLOR_COUNT = 5
MIN_SIMILARITY = 6.0
MAX_SIMILARITY = 30.0
QUANTIZE_COLORS = 64
FEATURE_QUANTIZE_COLORS = 128
FEATURE_MERGE_SIMILARITY = 10.0
FEATURE_MIN_SHARE = 0.005
FEATURE_MIN_DOMINANT_DISTANCE = 12.0
FEATURE_CONTRAST_SCALE = 60.0
FEATURE_CHROMA_SCALE = 80.0
FEATURE_SHARE_SCALE = 0.05
ANALYSIS_MAX_SIDE = 512
OUTPUT_MAX_SIDE = 2048

ColorStripSizeMode = Literal["equal", "proportional"]
ColorStripOrder = Literal["least_first", "most_first"]
ColorStripOrientation = Literal["vertical", "horizontal"]
ColorStripSelectionMode = Literal["dominant", "featured"]


@dataclass(frozen=True)
class ColorStripColor:
    rgb: tuple[int, int, int]
    pixel_count: int
    share: float

    @property
    def hex(self) -> str:
        return "#{:02x}{:02x}{:02x}".format(*self.rgb)


@dataclass(frozen=True)
class ColorStripDocument:
    source_width: int
    source_height: int
    analysis_width: int
    analysis_height: int
    output_width: int
    output_height: int
    colors: tuple[ColorStripColor, ...]
    similarity: float
    size_mode: ColorStripSizeMode
    order: ColorStripOrder
    orientation: ColorStripOrientation
    selection_mode: ColorStripSelectionMode

    @property
    def color_count(self) -> int:
        return len(self.colors)


def _validate_options(
    color_count: int,
    similarity: float,
    size_mode: ColorStripSizeMode,
    order: ColorStripOrder,
    orientation: ColorStripOrientation,
    selection_mode: ColorStripSelectionMode,
) -> None:
    if not MIN_COLOR_COUNT <= color_count <= MAX_COLOR_COUNT:
        raise ValueError("Color Strip color_count must be between 3 and 5.")
    if not MIN_SIMILARITY <= similarity <= MAX_SIMILARITY:
        raise ValueError("Color Strip similarity must be between 6 and 30.")
    if size_mode not in {"equal", "proportional"}:
        raise ValueError("Color Strip size_mode must be equal or proportional.")
    if order not in {"least_first", "most_first"}:
        raise ValueError("Color Strip order must be least_first or most_first.")
    if orientation not in {"vertical", "horizontal"}:
        raise ValueError("Color Strip orientation must be vertical or horizontal.")
    if selection_mode not in {"dominant", "featured"}:
        raise ValueError("Color Strip selection_mode must be dominant or featured.")


def _fit_size(width: int, height: int, max_side: int) -> tuple[int, int]:
    if max(width, height) <= max_side:
        return width, height
    scale = max_side / max(width, height)
    return max(1, round(width * scale)), max(1, round(height * scale))


def _rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """Convert sRGB values to CIE L*a*b* using a D65 white point."""
    values = np.asarray(rgb, dtype=np.float64) / 255.0
    linear = np.where(
        values <= 0.04045,
        values / 12.92,
        ((values + 0.055) / 1.055) ** 2.4,
    )
    xyz = linear @ np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ],
        dtype=np.float64,
    ).T
    xyz = xyz / np.array([0.95047, 1.0, 1.08883], dtype=np.float64)

    delta = 6.0 / 29.0
    f = np.where(
        xyz > delta**3,
        np.cbrt(xyz),
        xyz / (3.0 * delta**2) + 4.0 / 29.0,
    )
    lightness = 116.0 * f[:, 1] - 16.0
    a_axis = 500.0 * (f[:, 0] - f[:, 1])
    b_axis = 200.0 * (f[:, 1] - f[:, 2])
    return np.column_stack((lightness, a_axis, b_axis))


def _quantized_candidates(
    rgb_pixels: np.ndarray,
    *,
    color_limit: int = QUANTIZE_COLORS,
) -> list[tuple[int, tuple[int, int, int]]]:
    if len(rgb_pixels) == 0:
        return []

    pixel_row = Image.fromarray(rgb_pixels.reshape(1, -1, 3).astype(np.uint8), mode="RGB")
    quantized = pixel_row.quantize(
        colors=color_limit,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    palette = quantized.getpalette() or []
    candidates: list[tuple[int, tuple[int, int, int]]] = []
    for count, palette_index in quantized.getcolors(maxcolors=color_limit) or []:
        offset = palette_index * 3
        rgb = (
            int(palette[offset]),
            int(palette[offset + 1]),
            int(palette[offset + 2]),
        )
        candidates.append((int(count), rgb))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates


def _merge_candidates(
    candidates: list[tuple[int, tuple[int, int, int]]],
    similarity: float,
) -> list[tuple[int, tuple[int, int, int]]]:
    clusters: list[dict[str, object]] = []

    for count, rgb in candidates:
        rgb_array = np.array(rgb, dtype=np.float64)
        lab = _rgb_to_lab(rgb_array.reshape(1, 3))[0]

        if clusters:
            distances = [float(np.linalg.norm(lab - cluster["lab"])) for cluster in clusters]
            best_index = int(np.argmin(distances))
            if distances[best_index] <= similarity:
                cluster = clusters[best_index]
                cluster["count"] = int(cluster["count"]) + count
                cluster["sum_rgb"] = np.asarray(cluster["sum_rgb"]) + rgb_array * count
                mean_rgb = np.asarray(cluster["sum_rgb"]) / int(cluster["count"])
                cluster["lab"] = _rgb_to_lab(mean_rgb.reshape(1, 3))[0]
                continue

        clusters.append(
            {
                "count": count,
                "sum_rgb": rgb_array * count,
                "lab": lab,
            }
        )

    merged: list[tuple[int, tuple[int, int, int]]] = []
    for cluster in clusters:
        count = int(cluster["count"])
        mean_rgb = np.asarray(cluster["sum_rgb"]) / count
        rgb = tuple(int(round(value)) for value in np.clip(mean_rgb, 0, 255))
        merged.append((count, rgb))
    merged.sort(key=lambda item: item[0], reverse=True)
    return merged


def _feature_score(
    count: int,
    rgb: tuple[int, int, int],
    total_visible: int,
    dominant_labs: np.ndarray,
) -> tuple[float, float]:
    lab = _rgb_to_lab(np.asarray(rgb, dtype=np.float64).reshape(1, 3))[0]
    if len(dominant_labs):
        dominant_distance = float(np.min(np.linalg.norm(dominant_labs - lab, axis=1)))
    else:
        dominant_distance = FEATURE_CONTRAST_SCALE

    share = count / total_visible
    chroma = float(np.hypot(lab[1], lab[2]))
    contrast_score = min(dominant_distance / FEATURE_CONTRAST_SCALE, 1.0)
    chroma_score = min(chroma / FEATURE_CHROMA_SCALE, 1.0)
    share_score = min(share / FEATURE_SHARE_SCALE, 1.0)
    score = 0.45 * contrast_score + 0.35 * chroma_score + 0.20 * share_score
    return score, dominant_distance


def _select_feature_candidate(
    rgb_pixels: np.ndarray,
    dominant: list[tuple[int, tuple[int, int, int]]],
    similarity: float,
) -> tuple[int, tuple[int, int, int]] | None:
    total_visible = len(rgb_pixels)
    if total_visible == 0:
        return None

    dominant_rgbs = np.asarray([rgb for _, rgb in dominant], dtype=np.float64)
    dominant_labs = (
        _rgb_to_lab(dominant_rgbs)
        if len(dominant_rgbs)
        else np.empty((0, 3), dtype=np.float64)
    )
    feature_similarity = min(similarity, FEATURE_MERGE_SIMILARITY)
    candidates = _merge_candidates(
        _quantized_candidates(rgb_pixels, color_limit=FEATURE_QUANTIZE_COLORS),
        feature_similarity,
    )

    ranked: list[tuple[float, int, tuple[int, int, int]]] = []
    for count, rgb in candidates:
        share = count / total_visible
        if share < FEATURE_MIN_SHARE:
            continue
        score, dominant_distance = _feature_score(
            count,
            rgb,
            total_visible,
            dominant_labs,
        )
        if dominant_distance < FEATURE_MIN_DOMINANT_DISTANCE:
            continue
        ranked.append((score, count, rgb))

    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    _, count, rgb = ranked[0]
    return count, rgb


def _reassign_selected_counts(
    rgb_pixels: np.ndarray,
    selected: list[tuple[int, tuple[int, int, int]]],
) -> list[tuple[int, tuple[int, int, int]]]:
    if not selected:
        return []

    centers = np.asarray([rgb for _, rgb in selected], dtype=np.float64)
    center_labs = _rgb_to_lab(centers)
    pixel_labs = _rgb_to_lab(rgb_pixels)
    distances = np.linalg.norm(pixel_labs[:, None, :] - center_labs[None, :, :], axis=2)
    assignments = np.argmin(distances, axis=1)
    counts = np.bincount(assignments, minlength=len(selected))
    reassigned = [
        (int(counts[index]), rgb)
        for index, (_, rgb) in enumerate(selected)
        if int(counts[index]) > 0
    ]
    reassigned.sort(key=lambda item: item[0], reverse=True)
    return reassigned


def _select_colors(
    rgb_pixels: np.ndarray,
    merged: list[tuple[int, tuple[int, int, int]]],
    *,
    color_count: int,
    similarity: float,
    selection_mode: ColorStripSelectionMode,
) -> list[tuple[int, tuple[int, int, int]]]:
    if selection_mode == "dominant":
        return merged[:color_count]

    dominant_slots = max(1, color_count - 1)
    selected = list(merged[:dominant_slots])
    featured = _select_feature_candidate(rgb_pixels, selected, similarity)
    if featured is not None:
        selected.append(featured)

    if len(selected) < color_count:
        selected_rgbs = {rgb for _, rgb in selected}
        for candidate in merged[dominant_slots:]:
            if candidate[1] in selected_rgbs:
                continue
            selected.append(candidate)
            selected_rgbs.add(candidate[1])
            if len(selected) >= color_count:
                break

    return _reassign_selected_counts(rgb_pixels, selected[:color_count])


def extract_color_strip(
    input_path: str | Path,
    *,
    color_count: int = DEFAULT_COLOR_COUNT,
    similarity: float = DEFAULT_SIMILARITY,
    size_mode: ColorStripSizeMode = DEFAULT_SIZE_MODE,
    order: ColorStripOrder = DEFAULT_ORDER,
    orientation: ColorStripOrientation = DEFAULT_ORIENTATION,
    selection_mode: ColorStripSelectionMode = DEFAULT_SELECTION_MODE,
    analysis_max_side: int = ANALYSIS_MAX_SIDE,
    output_max_side: int = OUTPUT_MAX_SIDE,
) -> ColorStripDocument:
    """Extract representative colors and return a configurable Color Strip document."""
    _validate_options(
        color_count,
        similarity,
        size_mode,
        order,
        orientation,
        selection_mode,
    )

    with Image.open(input_path) as source:
        source_width, source_height = source.size
        rgba = source.convert("RGBA")

    analysis_width, analysis_height = _fit_size(source_width, source_height, analysis_max_side)
    if (analysis_width, analysis_height) != (source_width, source_height):
        # Nearest-neighbor sampling avoids inventing blended edge colors while
        # keeping dominant-color analysis bounded for very large source images.
        rgba = rgba.resize((analysis_width, analysis_height), Image.Resampling.NEAREST)

    pixels = np.asarray(rgba, dtype=np.uint8)
    visible = pixels[..., 3] > 0
    rgb_pixels = pixels[..., :3][visible]
    if rgb_pixels.size == 0:
        raise ValueError("Color Strip requires at least one visible pixel.")

    candidates = _quantized_candidates(rgb_pixels)
    merged = _merge_candidates(candidates, similarity)
    selected = _select_colors(
        rgb_pixels,
        merged,
        color_count=color_count,
        similarity=similarity,
        selection_mode=selection_mode,
    )
    total_visible = len(rgb_pixels)

    reverse = order == "most_first"
    colors = tuple(
        ColorStripColor(
            rgb=rgb,
            pixel_count=count,
            share=count / total_visible,
        )
        for count, rgb in sorted(selected, key=lambda item: item[0], reverse=reverse)
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
        similarity=float(similarity),
        size_mode=size_mode,
        order=order,
        orientation=orientation,
        selection_mode=selection_mode,
    )


def _bar_bounds(index: int, count: int, length: int) -> tuple[int, int]:
    """Return legacy equal-size bounds so v0.1 defaults remain byte-compatible."""
    start = round(index * length / count)
    end = round((index + 1) * length / count)
    return start, max(start + 1, end)


def _proportional_bounds(colors: tuple[ColorStripColor, ...], length: int) -> list[tuple[int, int]]:
    count = len(colors)
    if count == 0:
        return []
    if length < count:
        return [_bar_bounds(index, count, length) for index in range(count)]

    total_share = sum(color.share for color in colors)
    if total_share <= 0:
        return [_bar_bounds(index, count, length) for index in range(count)]

    # Reserve one pixel per selected color, then distribute the remaining pixels
    # by source share. This keeps tiny selected colors visible in raster output.
    remaining = length - count
    weighted = [(color.share / total_share) * remaining for color in colors]
    extras = [int(value) for value in weighted]
    remainder = remaining - sum(extras)
    ranked = sorted(
        range(count),
        key=lambda index: (weighted[index] - extras[index], -index),
        reverse=True,
    )
    for index in ranked[:remainder]:
        extras[index] += 1

    sizes = [1 + extra for extra in extras]
    bounds: list[tuple[int, int]] = []
    cursor = 0
    for size in sizes:
        end = cursor + size
        bounds.append((cursor, end))
        cursor = end
    return bounds


def _segment_bounds(document: ColorStripDocument) -> list[tuple[int, int]]:
    length = document.output_height if document.orientation == "vertical" else document.output_width
    if document.size_mode == "proportional":
        return _proportional_bounds(document.colors, length)
    return [_bar_bounds(index, document.color_count, length) for index in range(document.color_count)]


def color_strip_to_svg(document: ColorStripDocument) -> str:
    lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{document.output_width}" '
            f'height="{document.output_height}" viewBox="0 0 {document.output_width} {document.output_height}">'
        )
    ]
    for color, (start, end) in zip(document.colors, _segment_bounds(document), strict=True):
        if document.orientation == "vertical":
            lines.append(
                f'  <rect x="0" y="{start}" width="{document.output_width}" '
                f'height="{end - start}" fill="{color.hex}"/>'
            )
        else:
            lines.append(
                f'  <rect x="{start}" y="0" width="{end - start}" '
                f'height="{document.output_height}" fill="{color.hex}"/>'
            )
    lines.append("</svg>")
    return "\n".join(lines)


def render_color_strip(document: ColorStripDocument) -> Image.Image:
    image = Image.new("RGB", (document.output_width, document.output_height))
    draw = ImageDraw.Draw(image)
    for color, (start, end) in zip(document.colors, _segment_bounds(document), strict=True):
        if document.orientation == "vertical":
            draw.rectangle(
                (0, start, document.output_width - 1, min(document.output_height, end) - 1),
                fill=color.rgb,
            )
        else:
            draw.rectangle(
                (start, 0, min(document.output_width, end) - 1, document.output_height - 1),
                fill=color.rgb,
            )
    return image
