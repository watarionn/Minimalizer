from dataclasses import replace

import numpy as np

from minimalize_engine.v2.facet import PlanarFacetConfig, fit_luminance_split
from minimalize_engine.v2.pipeline import PipelineConfig, minimalize_v2
from minimalize_engine.v2.regression import algorithm_digest


def _image() -> np.ndarray:
    image = np.zeros((48, 48, 3), dtype=np.uint8)
    image[:, :24] = (230, 80, 90)
    image[:, 24:] = (50, 90, 210)
    image[12:36, 18:30] = (245, 220, 70)
    return image


def test_luminance_split_recovers_horizontal_gradient_plane():
    lab_l = np.tile(np.linspace(20.0, 80.0, 40), (30, 1))
    mask = np.ones((30, 40), dtype=bool)
    split = fit_luminance_split(lab_l, mask, min_samples=40)
    assert split is not None
    a, b, _, variation, negative_mean, positive_mean, positive_fraction = split
    assert abs(a) > 0.9
    assert abs(b) < 0.1
    assert variation > 40.0
    assert positive_mean > negative_mean
    assert 0.45 <= positive_fraction <= 0.55


def test_constant_luminance_has_no_split():
    lab_l = np.full((20, 20), 50.0, dtype=np.float64)
    mask = np.ones((20, 20), dtype=bool)
    assert fit_luminance_split(lab_l, mask, min_samples=20) is None


def test_facet_stage_is_observational_until_scene_wiring():
    base = PipelineConfig()
    disabled = replace(base, facet=replace(base.facet, enabled_presets=()))
    enabled_result = minimalize_v2(_image(), presets=("minimal",), config=base)
    disabled_result = minimalize_v2(_image(), presets=("minimal",), config=disabled)
    assert algorithm_digest(enabled_result, "minimal") == algorithm_digest(disabled_result, "minimal")
    assert enabled_result.presets["minimal"].facet_reconstruction.metrics.candidate_count >= 0
    assert disabled_result.presets["minimal"].facet_reconstruction.metrics.candidate_count == 0


def test_facet_config_rejects_invalid_half_ratio():
    try:
        PlanarFacetConfig(min_source_half_ratio=0.5)
    except ValueError:
        return
    raise AssertionError("invalid half-area ratio was accepted")


def test_facet_overlay_mask_is_clipped_to_primitive_geometry():
    from minimalize_engine.v2.facet import PlanarFacetOverlay, facet_overlay_mask
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    loop = np.asarray([[4, 4], [15, 4], [15, 15], [4, 15]], dtype=np.float32)
    geometry = PrimitiveGeometry(kind="polygon", loops=(loop,))
    overlay = PlanarFacetOverlay(
        region_id=1, rgb=(200, 100, 50), line_a=1.0, line_b=0.0,
        line_c=0.0, variant_side=1,
    )
    mask = facet_overlay_mask((20, 20), geometry, overlay)
    assert mask.any()
    assert not mask[:, :4].any()
    assert not mask[:, 16:].any()
    assert not mask[:4, :].any()
    assert not mask[16:, :].any()


def test_scene_facets_are_opt_in_for_rendering():
    from minimalize_engine.v2.facet import PlanarFacetOverlay
    from minimalize_engine.v2.palette import PaletteEntry
    from minimalize_engine.v2.pipeline import SceneModel, SceneShape
    from minimalize_engine.v2.primitive import PrimitiveGeometry
    from minimalize_engine.v2.regression.debug import _render_scene

    loop = np.asarray([[0, 0], [19, 0], [19, 19], [0, 19]], dtype=np.float32)
    geometry = PrimitiveGeometry(kind="polygon", loops=(loop,))
    entry = PaletteEntry(0, (1,), 1, np.asarray([50.0, 0.0, 0.0]), (100, 100, 100), (0, 0))
    overlay = PlanarFacetOverlay(1, (200, 50, 50), 1.0, 0.0, 0.0, 1)
    scene = SceneModel(20, 20, (SceneShape(1, geometry, 0),), (entry,), (overlay,))
    base = _render_scene(scene)
    faceted = _render_scene(scene, include_facets=True)
    assert not np.array_equal(base, faceted)
    assert tuple(base[10, 15]) == (100, 100, 100)
    assert tuple(faceted[10, 15]) == (200, 50, 50)


def test_facet_gate_config_rejects_excessive_line_loss():
    from minimalize_engine.v2.facet import PlanarFacetGateConfig

    try:
        PlanarFacetGateConfig(max_long_line_loss=1.1)
    except ValueError:
        return
    raise AssertionError("invalid facet gate line-loss limit was accepted")
