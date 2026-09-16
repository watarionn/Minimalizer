"""Minimalizer 2.0 core package."""

from .export import PNG_CONTRACT_VERSION, V2PngExport, V2PngMetadata, export_png
from .file_api import minimalize_file_png
from .migration import (
    MIGRATION_SCHEMA_VERSION,
    MigrationItem,
    MigrationReadinessReport,
    build_migration_readiness,
)
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
    "MinimalizerV2Result", "PipelineConfig", "PresetPipelineResult",
    "SceneModel", "SceneShape", "minimalize_v2", "run_preset_pipeline",
    "render_scene", "PNG_CONTRACT_VERSION", "V2PngExport", "V2PngMetadata",
    "export_png", "minimalize_file_png", "MIGRATION_SCHEMA_VERSION",
    "MigrationItem", "MigrationReadinessReport", "build_migration_readiness",
]
