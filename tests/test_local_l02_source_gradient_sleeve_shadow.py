import numpy as np
import pytest
from local_l02_source_gradient_sleeve_shadow import (
    SourceGradientHold, propose_source_gradient_sleeve,
)


def scene():
    rgba = np.zeros((20, 30, 4), dtype=np.uint8)
    rgba[:, :, 3] = 255
    rgba[:, :, :3] = (120, 40, 80)
    classes = np.zeros((20, 30), dtype=np.uint8)
    seed = np.zeros((20, 30), dtype=bool)
    seed[8:12, 3:9] = True
    classes[seed] = 5
    sleeve = np.zeros_like(seed)
    sleeve[8:12, 9:20] = True
    classes[sleeve] = 32
    return rgba, classes, seed, sleeve


def run(a, c, b, s):
    return propose_source_gradient_sleeve(
        rgba=a, class_ids=c, outerwear_seed=b, sleeve_candidate=s)


def test_same_source_color_attached_sleeve_retained_without_owner_promotion():
    a, c, b, s = scene()
    out, info = run(a, c, b, s)
    assert np.array_equal(out, s)
    assert info['retained'] == int(s.sum())
    assert info['owner_promotion_authorized'] is False
    assert info['Phase4'] == 'FAIL'


def test_strong_source_seam_abstains_without_erasing_original_seed():
    a, c, b, s = scene()
    a[s, :3] = (245, 245, 245)
    out, info = run(a, c, b, s)
    assert not out.any()
    assert info['abstained'] == int(s.sum())
    assert np.all(b[8:12, 3:9])


def test_source_alpha_escape_rejected():
    a, c, b, s = scene()
    a[8, 12, 3] = 0
    with pytest.raises(SourceGradientHold, match='SOURCE_ALPHA'):
        run(a, c, b, s)


def test_wrong_class_rejected_without_owner_reassignment():
    a, c, b, s = scene()
    c[8, 12] = 25
    with pytest.raises(SourceGradientHold, match='CLASS_OWNER'):
        run(a, c, b, s)


def test_no_seed_and_empty_sleeve_are_abstentions():
    a, c, b, s = scene()
    b[:] = False
    out, info = run(a, c, b, s)
    assert not out.any() and info['owner_promotion_authorized'] is False
    s[:] = False
    out, info = run(a, c, b, s)
    assert not out.any() and info['Phase4'] == 'FAIL'


def test_graph_budget_rejected():
    a, c, b, s = scene()
    with pytest.raises(SourceGradientHold, match='BUDGET'):
        propose_source_gradient_sleeve(
            rgba=a, class_ids=c, outerwear_seed=b,
            sleeve_candidate=s, max_candidate_pixels=2)


def test_missing_seed_edge_evidence_rejected():
    a, c, b, s = scene()
    b[:] = False
    b[9, 8] = True
    c[8:12, 3:9] = 0
    c[9, 8] = 5
    with pytest.raises(SourceGradientHold, match='INSUFFICIENT'):
        run(a, c, b, s)
