from minimalizer_zerobase.refine.polygon_guard import validate_polygon_candidate

REF=((2,2),(10,2),(10,10),(2,10))
def test_small_fixed_topology_move_passes():
    assert validate_polygon_candidate(REF,((2.2,2),(10,2.2),(9.8,10),(2,9.8)),width=16,height=16).valid
def test_winding_flip_rejected():
    r=validate_polygon_candidate(REF,tuple(reversed(REF)),width=16,height=16)
    assert not r.valid and "winding" in r.reason
def test_self_intersection_rejected():
    r=validate_polygon_candidate(REF,((2,2),(10,10),(10,2),(2,10)),width=16,height=16,min_area_ratio=0)
    assert not r.valid
def test_large_shift_rejected():
    r=validate_polygon_candidate(REF,((7,2),(15,2),(15,10),(7,10)),width=16,height=16)
    assert not r.valid and "trust region" in r.reason
def test_area_collapse_rejected():
    r=validate_polygon_candidate(REF,((2,2),(10,2),(10,3),(2,3)),width=16,height=16)
    assert not r.valid and "area" in r.reason
