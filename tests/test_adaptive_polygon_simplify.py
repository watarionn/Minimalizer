import numpy as np
from minimalize_engine.analysis.shape_cleanup import _try_simplify_polygon, _polygon_local_iou
from minimalize_engine.models import Shape

def poly(points):
    return Shape(id=1, shape_type="polygon", fill_color=(10,20,30),
                 points=points, importance=0.5)

def test_adaptive_simplify_reduces_nearly_straight_vertices():
    s=poly([(0,0),(3,0.05),(6,-0.04),(10,0),(10,5),(7,5.03),(4,4.98),(0,5)])
    out=_try_simplify_polygon(s, 0.012, 0.045, 0.985)
    assert out is not None
    assert len(out.points) < len(s.points)
    assert _polygon_local_iou(np.asarray(s.points,np.float32), np.asarray(out.points,np.float32)) >= 0.985

def test_adaptive_simplify_rejects_shape_change():
    s=poly([(0,0),(5,0),(6,2),(10,2),(10,8),(6,8),(5,10),(0,10),(0,7),(3,5),(0,3)])
    out=_try_simplify_polygon(s, 0.08, 0.01, 0.999)
    assert out is None or _polygon_local_iou(np.asarray(s.points,np.float32), np.asarray(out.points,np.float32)) >= 0.999
