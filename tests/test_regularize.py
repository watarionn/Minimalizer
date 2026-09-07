from minimalize_engine.geometry.regularize import simplify_collinear


def test_simplify_collinear_terminates_on_degenerate_loop():
    points = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)]
    result = simplify_collinear(points, tolerance=10.0)
    assert len(result) >= 3
