import numpy as np

from minimalizer_zerobase.evaluation.material_topology import (
    canonical_material_mask,
    tiny_component_area_threshold,
)


def test_components_and_holes_use_phase14_threshold_boundary():
    subject = np.zeros((40, 40), dtype=bool)
    subject[2:38, 2:38] = True
    threshold = tiny_component_area_threshold(int(subject.sum()))

    below = subject.copy()
    below[10, 10] = False
    below[30, 30] = True
    # An isolated component and an enclosed hole below threshold are noise.
    below[0, 0] = True
    below[20, 20] = False
    assert not canonical_material_mask(below, tiny_component_area_threshold=threshold)[0, 0]
    assert canonical_material_mask(below, tiny_component_area_threshold=threshold)[20, 20]

    at = subject.copy()
    at[0:threshold, 0] = True
    at[20:22, 20:24] = False  # exactly the floor threshold for this fixture
    canonical = canonical_material_mask(at, tiny_component_area_threshold=threshold)
    assert canonical[:threshold, 0].all()
    assert not canonical[20, 20]
