from __future__ import annotations

from pathlib import Path

from minimalize_engine.io.image_loader import load_image
from minimalize_engine.v2.analysis_guidance import AnalysisGuidance
from minimalize_engine.v2.export import V2PngExport, export_png
from minimalize_engine.v2.pipeline import PipelineConfig, minimalize_v2


def minimalize_file_png(
    input_path: str | Path,
    *,
    preset: str = "minimal",
    include_facets: bool = True,
    config: PipelineConfig | None = None,
    filename: str | None = None,
    guidance: AnalysisGuidance | None = None,
) -> V2PngExport:
    """Run the canonical V2 pipeline for one image file and return PNG bytes."""
    source_rgb = load_image(input_path)
    result = minimalize_v2(
        source_rgb,
        presets=(preset,),
        config=config,
        guidance=guidance,
    )
    return export_png(
        result,
        preset=preset,
        include_facets=include_facets,
        filename=filename,
    )
