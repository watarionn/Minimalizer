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
    owners = np.zeros(seed.shape, dtype=np.uint8)
    owners[seed] = 1
    return rgba, classes, seed, sleeve, owners


def run(a, c, b, s, owners):
    return propose_source_gradient_sleeve(
        rgba=a, class_ids=c, outerwear_seed=b,
        sleeve_candidate=s, seed_owner_ids=owners)


def test_same_source_color_attached_sleeve_retained_without_owner_promotion():
    a, c, b, s, owners = scene()
    out, info = run(a, c, b, s, owners)
    assert np.array_equal(out, s)
    assert info['retained'] == int(s.sum())
    assert info['owner_promotion_authorized'] is False
    assert info['Phase4'] == 'FAIL'
    assert info['dual_owner_abstained_source_pixels'] == 0


def test_strong_source_seam_abstains_without_erasing_original_seed():
    a, c, b, s, owners = scene()
    a[s, :3] = (245, 245, 245)
    out, info = run(a, c, b, s, owners)
    assert not out.any()
    assert info['abstained'] == int(s.sum())
    assert np.all(b[8:12, 3:9])


def test_source_alpha_escape_rejected():
    a, c, b, s, owners = scene()
    a[8, 12, 3] = 0
    with pytest.raises(SourceGradientHold, match='SOURCE_ALPHA'):
        run(a, c, b, s, owners)


def test_wrong_class_rejected_without_owner_reassignment():
    a, c, b, s, owners = scene()
    c[8, 12] = 25
    with pytest.raises(SourceGradientHold, match='CLASS_OWNER'):
        run(a, c, b, s, owners)


def test_no_seed_and_empty_sleeve_are_abstentions():
    a, c, b, s, owners = scene()
    b[:] = False
    owners[:] = 0
    out, info = run(a, c, b, s, owners)
    assert not out.any() and info['owner_promotion_authorized'] is False
    s[:] = False
    out, info = run(a, c, b, s, owners)
    assert not out.any() and info['Phase4'] == 'FAIL'


def test_graph_budget_rejected():
    a, c, b, s, owners = scene()
    with pytest.raises(SourceGradientHold, match='BUDGET'):
        propose_source_gradient_sleeve(
            rgba=a, class_ids=c, outerwear_seed=b,
            sleeve_candidate=s, seed_owner_ids=owners, max_candidate_pixels=2)


def test_missing_seed_edge_evidence_rejected():
    a, c, b, s, owners = scene()
    b[:] = False
    owners[:] = 0
    b[9, 8] = True
    owners[9, 8] = 1
    c[8:12, 3:9] = 0
    c[9, 8] = 5
    with pytest.raises(SourceGradientHold, match='INSUFFICIENT'):
        run(a, c, b, s, owners)

def test_dual_owner_connected_sleeve_abstains_even_with_zero_color_seam():
    a, c, b, s, owners = scene()
    b[8:12, 20:26] = True
    c[8:12, 20:26] = 10
    owners[8:12, 20:26] = 2
    out, info = run(a, c, b, s, owners)
    assert not out.any()
    assert info['dual_owner_abstained_components'] == 1
    assert info['dual_owner_abstained_source_pixels'] == int(s.sum())
    assert info['owner_promotion_authorized'] is False


@pytest.mark.parametrize('corrupt', ['missing', 'wrong_shape', 'wrong_dtype',
                                     'outside_seed', 'wrong_owner_class', 'unknown_owner'])
def test_invalid_or_unverified_seed_owner_provenance_holds(corrupt):
    a, c, b, s, owners = scene()
    if corrupt == 'missing':
        owners = None
    elif corrupt == 'wrong_shape':
        owners = owners[:-1]
    elif corrupt == 'wrong_dtype':
        owners = owners.astype(np.int32)
    elif corrupt == 'outside_seed':
        owners[0, 0] = 1
    elif corrupt == 'wrong_owner_class':
        owners[9, 5] = 2
    else:
        owners[9, 5] = 3
    with pytest.raises(SourceGradientHold, match='FROZEN_SEED_OWNER'):
        run(a, c, b, s, owners)
