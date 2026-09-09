from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Literal

from minimalize_engine import MinimalizeConfig, minimalize, minimalize_rinka_reference, rinka_reference_config
from minimalize_engine.color_strip import (
    ANALYSIS_MAX_SIDE as COLOR_STRIP_ANALYSIS_MAX_SIDE,
    DEFAULT_COLOR_COUNT as COLOR_STRIP_DEFAULT_COLOR_COUNT,
    DEFAULT_ORIENTATION as COLOR_STRIP_DEFAULT_ORIENTATION,
    DEFAULT_ORDER as COLOR_STRIP_DEFAULT_ORDER,
    DEFAULT_SELECTION_MODE as COLOR_STRIP_DEFAULT_SELECTION_MODE,
    DEFAULT_SIMILARITY as COLOR_STRIP_DEFAULT_SIMILARITY,
    DEFAULT_SIZE_MODE as COLOR_STRIP_DEFAULT_SIZE_MODE,
    ColorStripOrientation,
    ColorStripOrder,
    ColorStripSelectionMode,
    ColorStripSizeMode,
    color_strip_to_svg,
    extract_color_strip,
    render_color_strip,
)
from minimalize_engine.io.image_exporter import render_scene
from minimalize_engine.io.svg_exporter import scene_to_svg

OutputFormat = Literal["svg", "png"]
ProcessingMode = Literal["standard", "rinka_reference", "color_strip"]


@dataclass(frozen=True)
class RenderedResult:
    content: bytes
    media_type: str
    filename: str
    shape_count: int
    analysis_size: str
    source_size: str
    color_count: int | None = None
    color_similarity: float | None = None
    color_size_mode: ColorStripSizeMode | None = None
    color_order: ColorStripOrder | None = None
    color_orientation: ColorStripOrientation | None = None
    color_selection_mode: ColorStripSelectionMode | None = None


def build_config(
    level: int = 4,
    *,
    colors: int | None = None,
    max_shapes: int | None = None,
    background: str | None = None,
    analysis_max_side_cap: int | None = None,
) -> MinimalizeConfig:
    overrides: dict[str, object] = {}
    if colors is not None:
        overrides["palette_colors"] = colors
    if max_shapes is not None:
        overrides["target_max_shapes"] = max_shapes
    if background is not None:
        overrides["background_mode"] = background

    config = MinimalizeConfig.from_level(level, **overrides)
    if analysis_max_side_cap is not None and config.analysis_max_side > analysis_max_side_cap:
        config = config.with_overrides(analysis_max_side=analysis_max_side_cap)
    return config


def _render_result(scene, output_format: OutputFormat) -> RenderedResult:
    if output_format == "svg":
        content = scene_to_svg(scene).encode("utf-8")
        media_type = "image/svg+xml"
        filename = "minimalized.svg"
    elif output_format == "png":
        buffer = BytesIO()
        render_scene(scene).save(buffer, format="PNG")
        content = buffer.getvalue()
        media_type = "image/png"
        filename = "minimalized.png"
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

    return RenderedResult(
        content=content,
        media_type=media_type,
        filename=filename,
        shape_count=int(scene.metadata.get("shape_count", len(scene.shapes))),
        analysis_size=f"{scene.width}x{scene.height}",
        source_size=f"{scene.metadata.get('source_width', scene.width)}x{scene.metadata.get('source_height', scene.height)}",
    )


def minimalize_path(
    input_path: str | Path,
    config: MinimalizeConfig,
    output_format: OutputFormat = "svg",
) -> RenderedResult:
    return _render_result(minimalize(input_path, config), output_format)


def build_rinka_config(*, analysis_max_side_cap: int | None = None) -> MinimalizeConfig:
    config = rinka_reference_config(4)
    if analysis_max_side_cap is not None and config.analysis_max_side > analysis_max_side_cap:
        config = config.with_overrides(analysis_max_side=analysis_max_side_cap)
    return config


def minimalize_rinka_path(
    input_path: str | Path,
    output_format: OutputFormat = "svg",
    *,
    analysis_max_side_cap: int | None = None,
) -> RenderedResult:
    config = build_rinka_config(analysis_max_side_cap=analysis_max_side_cap)
    scene = minimalize_rinka_reference(
        input_path,
        level=4,
        analysis_max_side=config.analysis_max_side,
    )
    return _render_result(scene, output_format)


def color_strip_path(
    input_path: str | Path,
    output_format: OutputFormat = "svg",
    *,
    color_count: int = COLOR_STRIP_DEFAULT_COLOR_COUNT,
    similarity: float = COLOR_STRIP_DEFAULT_SIMILARITY,
    size_mode: ColorStripSizeMode = COLOR_STRIP_DEFAULT_SIZE_MODE,
    order: ColorStripOrder = COLOR_STRIP_DEFAULT_ORDER,
    orientation: ColorStripOrientation = COLOR_STRIP_DEFAULT_ORIENTATION,
    selection_mode: ColorStripSelectionMode = COLOR_STRIP_DEFAULT_SELECTION_MODE,
    analysis_max_side_cap: int | None = None,
) -> RenderedResult:
    analysis_max_side = COLOR_STRIP_ANALYSIS_MAX_SIDE
    if analysis_max_side_cap is not None:
        analysis_max_side = min(analysis_max_side, analysis_max_side_cap)

    document = extract_color_strip(
        input_path,
        color_count=color_count,
        similarity=similarity,
        size_mode=size_mode,
        order=order,
        orientation=orientation,
        selection_mode=selection_mode,
        analysis_max_side=analysis_max_side,
    )

    if output_format == "svg":
        content = color_strip_to_svg(document).encode("utf-8")
        media_type = "image/svg+xml"
        filename = "color-strip.svg"
    elif output_format == "png":
        buffer = BytesIO()
        render_color_strip(document).save(buffer, format="PNG")
        content = buffer.getvalue()
        media_type = "image/png"
        filename = "color-strip.png"
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

    return RenderedResult(
        content=content,
        media_type=media_type,
        filename=filename,
        shape_count=document.color_count,
        analysis_size=f"{document.analysis_width}x{document.analysis_height}",
        source_size=f"{document.source_width}x{document.source_height}",
        color_count=document.color_count,
        color_similarity=document.similarity,
        color_size_mode=document.size_mode,
        color_order=document.order,
        color_orientation=document.orientation,
        color_selection_mode=document.selection_mode,
    )
