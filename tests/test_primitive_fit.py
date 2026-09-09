import cv2
import numpy as np

from minimalize_engine.character.primitive_fit import fit_best_primitive


def test_primitive_fit_ellipse_matches_round_mask():
    mask = np.zeros((80, 80), dtype=np.uint8)
    cv2.ellipse(mask, (40, 38), (18, 24), 0, 0, 360, 1, -1)
    fit = fit_best_primitive(mask, allowed=("ellipse",), polygon_vertices=(4, 6))
    assert fit is not None
    assert fit.kind == "ellipse"
    assert fit.shape_type == "ellipse"
    assert fit.iou >= 0.70
    assert fit.complexity == 4


def test_primitive_fit_compares_simple_polygon_candidates():
    mask = np.zeros((80, 80), dtype=np.uint8)
    points = np.array([[22, 18], [58, 18], [64, 62], [16, 62]], dtype=np.int32)
    cv2.fillPoly(mask, [points], 1)
    fit = fit_best_primitive(
        mask,
        allowed=("trapezoid", "rotated_rect", "polygon"),
        polygon_vertices=(4, 5, 6),
    )
    assert fit is not None
    assert fit.iou >= 0.60
    assert fit.complexity <= 6
