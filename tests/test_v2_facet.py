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
