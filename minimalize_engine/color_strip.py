from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

COLOR_STRIP_VERSION = "v0.1"
DEFAULT_COLOR_COUNT = 5
DEFAULT_SIMILARITY = 18.0
MIN_COLOR_COUNT = 3
MAX_COLOR_COUNT = 5
MIN_SIMILARITY = 6.0
MAX_SIMILARITY = 30.0
QUANTIZE_COLORS = 64
ANALYSIS_MAX_SIDE = 512
OUTPUT_MAX_SIDE = 2048


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

    @property
    def color_count(self) -> int:
        return len(self.colors)


def _validate_options(color_count: int, similarity: float) -> None:
    if not MIN_COLOR_COUNT <= color_count <= MAX_COLOR_COUNT:
        raise ValueError("Color Strip color_count must be between 3 and 5.")
    if not MIN_SIMILARITY <= similarity <= MAX_SIMILARITY:
        raise ValueError("Color Strip similarity must be between 6 and 30.")


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


def _quantized_candidates(rgb_pixels: np.ndarray) -> list[tuple[int, tuple[int, int, int]]]:
    if len(rgb_pixels) == 0:
        return []

    pixel_row = Image.fromarray(rgb_pixels.reshape(1, -1, 3).astype(np.uint8), mode="RGB")
    quantized = pixel_row.quantize(
        colors=QUANTIZE_COLORS,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    palette = quantized.getpalette() or []
    candidates: list[tuple[int, tuple[int, int, int]]] = []
    for count, palette_index in quantized.getcolors(maxcolors=QUANTIZE_COLORS) or []:
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


def extract_color_strip(
    input_path: str | Path,
    *,
    color_count: int = DEFAULT_COLOR_COUNT,
    similarity: float = DEFAULT_SIMILARITY,
    analysis_max_side: int = ANALYSIS_MAX_SIDE,
    output_max_side: int = OUTPUT_MAX_SIDE,
) -> ColorStripDocument:
    """Extract dominant colors and return an equal-height Color Strip document."""
    _validate_options(color_count, similarity)

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
    selected = merged[:color_count]
    total_visible = sum(count for count, _ in merged)

    # Selection is based on most-used colors. Rendering intentionally reverses
    # that order so the least-used selected color is placed first/top.
    colors = tuple(
        ColorStripColor(
            rgb=rgb,
            pixel_count=count,
            share=count / total_visible,
        )
        for count, rgb in sorted(selected, key=lambda item: item[0])
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
    )


def _bar_bounds(index: int, count: int, height: int) -> tuple[int, int]:
    """Return equal-height bar bounds; shares are retained for a future size option."""
    top = round(index * height / count)
    bottom = round((index + 1) * height / count)
    return top, max(top + 1, bottom)


def color_strip_to_svg(document: ColorStripDocument) -> str:
    lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{document.output_width}" '
            f'height="{document.output_height}" viewBox="0 0 {document.output_width} {document.output_height}">'
        )
    ]
    for index, color in enumerate(document.colors):
        top, bottom = _bar_bounds(index, document.color_count, document.output_height)
        lines.append(
            f'  <rect x="0" y="{top}" width="{document.output_width}" '
            f'height="{bottom - top}" fill="{color.hex}"/>'
        )
    lines.append("</svg>")
    return "\n".join(lines)


def render_color_strip(document: ColorStripDocument) -> Image.Image:
    image = Image.new("RGB", (document.output_width, document.output_height))
    draw = ImageDraw.Draw(image)
    for index, color in enumerate(document.colors):
        top, bottom = _bar_bounds(index, document.color_count, document.output_height)
        draw.rectangle(
            (0, top, document.output_width - 1, min(document.output_height, bottom) - 1),
            fill=color.rgb,
        )
    return image
