from __future__ import annotations

import numpy as np
import pytest

from minimalizer_zerobase.evaluation.component_primitive_support import (
    measure_component_primitive_support,
)
from minimalizer_zerobase.semantic_abstraction.macro_geometry_reauthoring import (
    reauthor_macro_geometry_with_budget,
)


def _mask():
    hair = np.zeros((100, 100), bool)
    clothing = np.zeros((100, 100), bool)
    hair[10:40, 10:40] = True
    clothing[50:80, 10:40] = True
    clothing[50:80, 50:80] = True
    return hair, clothing


def test_support_is_measured_from_source_masks_and_emitted_geometry():
    hair, clothing = _mask()
    primitives, budget = reauthor_macro_geometry_with_budget(
        hair_mask=hair,
        clothing_mask=clothing,
        global_primitive_budget=5,
    )
    evidence = measure_component_primitive_support(
        role_masks={"hair": hair, "major_clothing": clothing},
        primitives=primitives,
        budget=budget,
    )
    assert evidence.source_components == 3
    assert evidence.represented_components == 3
    assert evidence.emitted_primitives == 3
    assert evidence.source_supported_primitives == 3
    assert evidence.component_survival_ratio == 1.0
    assert evidence.primitive_economy_ratio == 1.0


def test_missing_mask_fails_closed():
    hair, clothing = _mask()
    primitives, budget = reauthor_macro_geometry_with_budget(
        hair_mask=hair, clothing_mask=clothing, global_primitive_budget=5
    )
    with pytest.raises(ValueError):
        measure_component_primitive_support(
            role_masks={"hair": hair},
            primitives=primitives,
            budget=budget,
        )


def test_invalid_measurement_threshold_fails_closed():
    hair, clothing = _mask()
    primitives, budget = reauthor_macro_geometry_with_budget(
        hair_mask=hair, clothing_mask=clothing, global_primitive_budget=5
    )
    with pytest.raises(ValueError):
        measure_component_primitive_support(
            role_masks={"hair": hair, "major_clothing": clothing},
            primitives=primitives,
            budget=budget,
            min_component_coverage=1.1,
        )
