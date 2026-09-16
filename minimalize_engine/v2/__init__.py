"""Minimalizer 2.0 core package."""

from .compatibility import (
    PUBLIC_CONTRACT_SCHEMA_VERSION,
    PublicContractCompatibilityReport,
    PublicControlCompatibility,
    build_public_contract_compatibility,
)
from .export import PNG_CONTRACT_VERSION, V2PngExport, V2PngMetadata, export_png
from .file_api import minimalize_file_png
from .output_contract import (
    OUTPUT_FORMAT_SCHEMA_VERSION,
    OutputFormatCompatibilityReport,
    OutputFormatPolicy,
    build_output_format_compatibility,
)
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
    "OUTPUT_FORMAT_SCHEMA_VERSION", "OutputFormatPolicy",
    "OutputFormatCompatibilityReport", "build_output_format_compatibility",
    "PUBLIC_CONTRACT_SCHEMA_VERSION", "PublicControlCompatibility",
    "PublicContractCompatibilityReport", "build_public_contract_compatibility",
]
