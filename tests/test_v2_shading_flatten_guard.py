import numpy as np

from minimalize_engine.v2 import (
    PipelineConfig,
    ShadingFlattenConfig,
    ShadingFlattenGuardConfig,
    export_png,
    minimalize_v2,
)


def _gradient_image() -> np.ndarray:
    image = np.zeros((72, 96, 3), dtype=np.uint8)
    x = np.linspace(45, 145, 48, dtype=np.uint8)
    image[:, :48, 0] = x[None, :]
    image[:, :48, 1] = np.clip(x[None, :] + 25, 0, 255)
    image[:, :48, 2] = np.clip(x[None, :] + 45, 0, 255)
    image[:, 48:] = (210, 75, 95)
    return image


def test_shading_flatten_guard_records_decision_and_selects_one_path():
    image = _gradient_image()
    result = minimalize_v2(
        image,
        config=PipelineConfig(
            analysis_max_side=96,
            shading_flatten=ShadingFlattenConfig(enabled=True, sr=45),
            shading_flatten_guard=ShadingFlattenGuardConfig(
                enabled=True,
                max_polygon_vertex_ratio=10.0,
                max_part_polygon_vertex_ratio=10.0,
                max_initial_region_ratio=10.0,
                max_global_palette_delta=10,
                max_total_part_palette_ratio=10.0,
                max_single_part_palette_increase=10,
                max_relaxed_single_part_palette_increase=10,
                min_edge_energy_retention=0.01,
                max_subject_color_mae=1.0,
                max_subject_color_p95=1.0,
                min_region_reduction_ratio=0.0,
                min_polygon_reduction_ratio=0.0,
                min_part_polygon_reduction_ratio=0.0,
            ),
        ),
    )

    decision = result.shading_flatten_decision
    assert decision is not None
    assert decision.alpha_preserved is True
    assert decision.silhouette_preserved is True

    exported = export_png(result)
    assert exported.metadata.shading_flatten_evaluated is True
    assert exported.metadata.shading_flatten_accepted is decision.accepted
    assert exported.metadata.shading_flatten_reasons == decision.reasons


def test_shading_flatten_guard_rejects_color_drift_when_threshold_is_zero():
    image = _gradient_image()
    result = minimalize_v2(
        image,
        config=PipelineConfig(
            analysis_max_side=96,
            shading_flatten=ShadingFlattenConfig(enabled=True, sr=45),
            shading_flatten_guard=ShadingFlattenGuardConfig(
                enabled=True,
                max_polygon_vertex_ratio=10.0,
                max_part_polygon_vertex_ratio=10.0,
                max_initial_region_ratio=10.0,
                max_global_palette_delta=10,
                max_total_part_palette_ratio=10.0,
                max_single_part_palette_increase=10,
                max_relaxed_single_part_palette_increase=10,
                min_edge_energy_retention=0.01,
                max_subject_color_mae=0.0,
                max_subject_color_p95=1.0,
                min_region_reduction_ratio=0.0,
                min_polygon_reduction_ratio=0.0,
                min_part_polygon_reduction_ratio=0.0,
            ),
        ),
    )

    decision = result.shading_flatten_decision
    assert decision is not None
    assert decision.accepted is False
    assert "subject_color_mae" in decision.reasons
    assert decision.subject_color_mae > 0.0


def test_palette_growth_can_relax_when_parts_simplify_strongly():
    from minimalize_engine.v2.pipeline import _shading_part_palette_growth_is_safe

    guard = ShadingFlattenGuardConfig()
    safe, relaxed = _shading_part_palette_growth_is_safe(
        total_part_palette_ratio=30.0 / 28.0,
        max_part_palette_increase=3,
        part_polygon_reduction=(234.0 - 102.0) / 234.0,
        config=guard,
    )

    assert safe is True
    assert relaxed is True


def test_palette_growth_stays_blocked_without_simplification_payoff():
    from minimalize_engine.v2.pipeline import _shading_part_palette_growth_is_safe

    guard = ShadingFlattenGuardConfig()
    safe, relaxed = _shading_part_palette_growth_is_safe(
        total_part_palette_ratio=1.08,
        max_part_palette_increase=3,
        part_polygon_reduction=0.10,
        config=guard,
    )

    assert safe is False
    assert relaxed is False


def test_palette_total_growth_is_always_bounded():
    from minimalize_engine.v2.pipeline import _shading_part_palette_growth_is_safe

    guard = ShadingFlattenGuardConfig()
    safe, relaxed = _shading_part_palette_growth_is_safe(
        total_part_palette_ratio=1.35,
        max_part_palette_increase=3,
        part_polygon_reduction=0.60,
        config=guard,
    )

    assert safe is False
    assert relaxed is False


def test_default_guard_configuration_is_conservative():
    guard = ShadingFlattenGuardConfig()
    assert guard.enabled is False
    assert guard.max_polygon_vertex_ratio == 1.05
    assert guard.max_part_polygon_vertex_ratio == 1.20
    assert guard.max_initial_region_ratio == 1.10
    assert guard.max_global_palette_delta == 1
    assert guard.max_total_part_palette_ratio == 1.20
    assert guard.max_single_part_palette_increase == 2
    assert guard.max_relaxed_single_part_palette_increase == 4
    assert guard.palette_growth_relax_part_reduction_ratio == 0.25
