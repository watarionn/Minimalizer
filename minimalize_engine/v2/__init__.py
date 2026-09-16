"""Minimalizer 2.0 core package."""

from .alpha_contract import (
    ALPHA_BACKGROUND_SCHEMA_VERSION,
    AlphaBackgroundCompatibilityReport,
    AlphaBackgroundPolicy,
    build_alpha_background_compatibility,
    resolve_alpha_background_route,
)
from .browser_migration import (
    BROWSER_MIGRATION_SCHEMA_VERSION,
    BrowserMigrationContract,
    BrowserRolloutStage,
    build_browser_migration_contract,
    resolve_browser_route,
)
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
from .performance_budget import (
    PERFORMANCE_BUDGET_SCHEMA_VERSION, PerformanceBudget, PerformanceMeasurement,
    PerformanceBudgetEvaluation, evaluate_performance_budget,
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
    "PERFORMANCE_BUDGET_SCHEMA_VERSION", "PerformanceBudget", "PerformanceMeasurement",
    "PerformanceBudgetEvaluation", "evaluate_performance_budget",
    "OUTPUT_FORMAT_SCHEMA_VERSION", "OutputFormatPolicy",
    "OutputFormatCompatibilityReport", "build_output_format_compatibility",
    "BROWSER_MIGRATION_SCHEMA_VERSION", "BrowserRolloutStage",
    "BrowserMigrationContract", "build_browser_migration_contract",
    "resolve_browser_route",
    "ALPHA_BACKGROUND_SCHEMA_VERSION", "AlphaBackgroundPolicy",
    "AlphaBackgroundCompatibilityReport", "build_alpha_background_compatibility",
    "resolve_alpha_background_route", "PUBLIC_CONTRACT_SCHEMA_VERSION", "PublicControlCompatibility",
    "PublicContractCompatibilityReport", "build_public_contract_compatibility",
]
