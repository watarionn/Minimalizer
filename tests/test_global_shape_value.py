from minimalize_engine.analysis.shape_value import evaluate_global_shape_value
from minimalize_engine.models import Shape


def rect(i, x, y, w, h, color=(120,120,120), importance=0.2, sem='generic', part='unknown', layer='midground'):
    return Shape(i, 'rectangle', color, x=x, y=y, width=w, height=h,
                 importance=importance, semantic_type=sem, character_part=part, layer_name=layer)


def test_low_value_tiny_generic_is_removed():
    shapes = [
        rect(1, 10, 10, 1.5, 3.0, (118,118,118), 0.08),
        rect(2, 20, 20, 45, 45, (80,80,80), 0.85),
    ]
    out, rep = evaluate_global_shape_value(shapes, 100, 100, (120,120,120))
    assert [s.id for s in out] == [2]
    assert rep.removed_count == 1
    assert any(d.shape_id == 1 and d.reason == 'low_global_value' for d in rep.decisions)


def test_high_contrast_accent_is_kept():
    shapes = [rect(1, 10, 10, 2, 2, (250,20,20), 0.1)]
    out, rep = evaluate_global_shape_value(shapes, 100, 100, (120,120,120))
    assert len(out) == 1
    assert rep.removed_count == 0


def test_semantic_limb_is_protected_even_when_tiny():
    shapes = [rect(1, 10, 10, 1, 4, (120,120,120), 0.05, sem='character_limb', part='left_arm')]
    out, rep = evaluate_global_shape_value(shapes, 100, 100, (120,120,120))
    assert len(out) == 1
    assert rep.protected_count == 1


def test_switch_off_is_geometry_neutral():
    shapes = [rect(1, 10, 10, 1.5, 3.0, (118,118,118), 0.08)]
    out, rep = evaluate_global_shape_value(shapes, 100, 100, (120,120,120), enable=False)
    assert out == shapes
    assert not rep.enabled


def test_near_background_fragment_is_removed_even_if_global_value_is_middling():
    shapes = [rect(1, 30, 30, 8.3, 8.3, (124,124,124), 0.40, sem='structure')]
    out, rep = evaluate_global_shape_value(shapes, 100, 100, (120,120,120))
    assert out == []
    assert any(d.shape_id == 1 and d.reason == 'near_background_fragment' for d in rep.decisions)


def test_near_background_edge_cutout_is_preserved():
    shapes = [rect(1, 0, 30, 7, 7, (124,124,124), 0.35, sem='structure')]
    out, rep = evaluate_global_shape_value(shapes, 100, 100, (120,120,120))
    assert len(out) == 1
    assert not any(d.reason == 'near_background_fragment' for d in rep.decisions)


def test_near_background_fragment_with_visible_stroke_is_preserved():
    s = rect(1, 30, 30, 7, 7, (124,124,124), 0.35, sem='structure')
    s.stroke_color = (10,10,10)
    s.stroke_width = 1.0
    out, rep = evaluate_global_shape_value([s], 100, 100, (120,120,120))
    assert len(out) == 1
    assert not any(d.reason == 'near_background_fragment' for d in rep.decisions)
