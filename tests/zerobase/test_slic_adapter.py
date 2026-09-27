import numpy as np
from minimalizer_zerobase.analyzers.slic_regions import SLICRegionAdapter
from minimalizer_zerobase.core.coordinates import CoordinateSpace


def test_slic_is_repeatable_and_normalized_to_evidence():
    image = np.zeros((32, 32, 3), dtype=np.uint8)
    image[:,16:] = 255
    adapter = SLICRegionAdapter(n_segments=8, compactness=10)
    cs = CoordinateSpace(32,32)
    a = adapter.analyze(image, cs)
    b = adapter.analyze(image, cs)
    assert a and [x.to_json() for x in a] == [x.to_json() for x in b]
    assert all(x.evidence_type == "region" for x in a)
    assert all(x.coordinate_space == cs for x in a)
