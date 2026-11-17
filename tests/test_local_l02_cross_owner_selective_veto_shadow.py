import numpy as np
import pytest
from local_l02_cross_owner_selective_veto_shadow import (
    propose_selective_cross_owner_veto, SelectiveVetoHold)
from local_l02_cross_owner_contact_gate import verify_no_new_cross_owner_contacts


def run(b, p, **kwargs):
    classes = np.zeros_like(b)
    classes[b == 1] = 5
    classes[b == 2] = 10
    classes[(b == 0) & (p > 0)] = 32
    alpha = np.full(b.shape, 255, dtype=np.uint8)
    return propose_selective_cross_owner_veto(
        before=b, proposed=p, source_alpha=alpha, class_ids=classes, **kwargs)


def test_conflicting_two_added_sides_retain_one_instead_of_both():
    b = np.zeros((12, 12), dtype=np.uint8)
    b[5, 2] = 1
    b[5, 9] = 2
    p = b.copy()
    p[5, 3:6] = 1
    p[5, 6:9] = 2
    out, info = run(b, p)
    assert info['source_only_retained_gain_vs_conservative'] > 0
    assert out[5, 2] == 1 and out[5, 9] == 2
    verify_no_new_cross_owner_contacts(before=b, after=out)


def test_new_addition_touching_frozen_opposite_is_forced_out():
    b = np.zeros((10, 10), dtype=np.uint8)
    b[5, 3] = 1
    b[5, 5] = 2
    p = b.copy()
    p[5, 4] = 1
    out, info = run(b, p)
    assert out[5, 4] == 0
    assert info['mandatory_added_pixels_removed'] == 1


def test_rejects_unauthorized_original_owner_erasure():
    b = np.zeros((7, 7), dtype=np.uint8)
    b[3, 2] = 1
    p = b.copy(); p[3, 2] = 0
    with pytest.raises(SelectiveVetoHold, match='UNAUTHORIZED'):
        run(b, p)


def test_rejects_budget_overflow_instead_of_unbounded_graph():
    b = np.zeros((8, 8), dtype=np.uint8)
    b[3, 1] = 1; b[3, 6] = 2
    p = b.copy(); p[3, 2:4] = 1; p[3, 4:6] = 2
    with pytest.raises(SelectiveVetoHold, match='BUDGET'):
        run(b, p, max_conflict_edges=0)


def test_safe_noop_and_preapproved_veto():
    b = np.zeros((8, 8), dtype=np.uint8)
    b[2, 1:4] = 1; b[6, 6] = 2
    p = b.copy(); p[2, 3] = 0
    allowed = np.zeros_like(b, dtype=bool); allowed[2, 3] = True
    out, info = run(b, p, allowed_abstentions=allowed)
    assert np.array_equal(out, p)
    assert info['semantic_quality_pass'] is False


def test_rejects_pixel_outside_source_and_unauthorized_class():
    b = np.zeros((8, 8), dtype=np.uint8)
    b[4, 2] = 1
    p = b.copy(); p[4, 3] = 1
    classes = np.zeros_like(b); classes[4, 2] = 5; classes[4, 3] = 32
    alpha = np.full(b.shape, 255, dtype=np.uint8); alpha[4, 3] = 0
    with pytest.raises(SelectiveVetoHold, match='OUTSIDE_SIGNED_SOURCE'):
        propose_selective_cross_owner_veto(
            before=b, proposed=p, source_alpha=alpha, class_ids=classes)
    alpha[4, 3] = 255; classes[4, 3] = 3
    with pytest.raises(SelectiveVetoHold, match='OWNER_CLASS_CONFLICT'):
        propose_selective_cross_owner_veto(
            before=b, proposed=p, source_alpha=alpha, class_ids=classes)


def test_preserves_large_connected_addition_that_conservative_prune_orphans():
    # A narrow cross-owner contact occurs at a 1px owner1 sleeve bridge.
    # Deleting both conflicting endpoints severs the bridge and drops a large
    # attached garment region. Selective removal drops owner2's one endpoint.
    b = np.zeros((35, 35), dtype=np.uint8)
    b[25, 5] = 1; b[25, 25] = 2
    p = b.copy()
    p[10:25, 5] = 1
    p[3:10, 2:17] = 1
    p[25, 20:25] = 2
    p[15:25, 20] = 2
    p[15, 6:20] = 2
    out, meta = run(b, p)
    assert meta['source_only_retained_gain_vs_conservative'] == 112
    assert np.all(out[3:10, 2:17] == 1)
    assert meta['detached_added_pixels_removed'] == 0
    verify_no_new_cross_owner_contacts(before=b, after=out)
