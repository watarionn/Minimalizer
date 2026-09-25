"""Minimalizer 2.0 core package."""

from .analysis_guidance import (
    AnalysisGuidance,
    LineGuide,
    SemanticGuide,
    StructuralGuide,
)
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
from .preprocessing import ShadingFlattenConfig
from .pipeline import (
    MinimalizerV2Result,
    PipelineConfig,
    PresetPipelineResult,
    SceneModel,
    SceneShape,
    minimalize_v2,
    run_preset_pipeline,
)
from .rembg_guidance import (
    RembgGuidanceConfig,
    build_rembg_guidance,
    create_rembg_session,
)
from .mediapipe_guidance import (
    MEDIAPIPE_MULTICLASS_LABELS,
    MediaPipeSemanticConfig,
    attach_mediapipe_semantics,
    build_mediapipe_semantic_guide,
    create_mediapipe_segmenter,
)
from .deeplsd_guidance import (
    DEEPLSD_INFERENCE_CONFIG,
    DeepLsdLineConfig,
    DeepLsdRuntime,
    LineDetectionSummary,
    attach_deeplsd_lines,
    build_deeplsd_line_guide,
    build_line_guide_from_segments,
    create_deeplsd_runtime,
)
from .rtmlib_guidance import (
    RTMLIB_STRUCTURAL_LABELS,
    RtmlibStructuralConfig,
    SkeletonSelection,
    attach_rtmlib_structure,
    build_rtmlib_structural_guide,
    build_structural_guide_from_pose,
    create_rtmlib_wholebody,
    select_primary_skeleton,
)
from .render import render_scene

__all__ = [
    "AnalysisGuidance", "SemanticGuide", "StructuralGuide", "LineGuide",
    "RembgGuidanceConfig", "build_rembg_guidance", "create_rembg_session",
    "MEDIAPIPE_MULTICLASS_LABELS", "MediaPipeSemanticConfig",
    "attach_mediapipe_semantics", "build_mediapipe_semantic_guide",
    "create_mediapipe_segmenter",
    "DEEPLSD_INFERENCE_CONFIG", "DeepLsdLineConfig", "DeepLsdRuntime",
    "LineDetectionSummary", "attach_deeplsd_lines", "build_deeplsd_line_guide",
    "build_line_guide_from_segments", "create_deeplsd_runtime",
    "RTMLIB_STRUCTURAL_LABELS", "RtmlibStructuralConfig", "SkeletonSelection",
    "attach_rtmlib_structure", "build_rtmlib_structural_guide",
    "build_structural_guide_from_pose", "create_rtmlib_wholebody",
    "select_primary_skeleton",
    "ShadingFlattenConfig", "MinimalizerV2Result", "PipelineConfig", "PresetPipelineResult",
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
