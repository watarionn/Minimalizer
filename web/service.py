from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Literal

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.io.image_exporter import render_scene
from minimalize_engine.io.svg_exporter import scene_to_svg

OutputFormat = Literal["svg", "png"]


@dataclass(frozen=True)
class RenderedResult:
    content: bytes
    media_type: str
    filename: str
    shape_count: int
    analysis_size: str
    source_size: str


def build_config(
    level: int = 4,
    *,
    colors: int | None = None,
    max_shapes: int | None = None,
    background: str | None = None,
) -> MinimalizeConfig:
    overrides: dict[str, object] = {}
    if colors is not None:
        overrides["palette_colors"] = colors
    if max_shapes is not None:
        overrides["target_max_shapes"] = max_shapes
    if background is not None:
        overrides["background_mode"] = background
    return MinimalizeConfig.from_level(level, **overrides)


def minimalize_path(
    input_path: str | Path,
    config: MinimalizeConfig,
    output_format: OutputFormat = "svg",
) -> RenderedResult:
    scene = minimalize(input_path, config)

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
