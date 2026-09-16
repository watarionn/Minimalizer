"""Minimalizer 2.0 core package."""

from .pipeline import (
    MinimalizerV2Result,
    PipelineConfig,
    PresetPipelineResult,
    SceneModel,
    SceneShape,
    minimalize_v2,
    run_preset_pipeline,
)
from .render import render_scene

__all__ = [
    "MinimalizerV2Result",
    "PipelineConfig",
    "PresetPipelineResult",
    "SceneModel",
    "SceneShape",
    "minimalize_v2",
    "run_preset_pipeline",
    "render_scene",
]
