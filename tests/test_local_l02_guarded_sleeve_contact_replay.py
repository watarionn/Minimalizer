"""Source-free negative tests for Run32/contact-guard composition."""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_guarded_sleeve_contact_replay import propose_contact_safe_sleeve
from test_local_l02_guarded_sleeve_geodesic_shadow import scene


def test_run32_sleeve_keeps_baseline_and_never_claims_phase4():
    x = scene()
    out, receipt = propose_contact_safe_sleeve(**x)
    assert out[3, 1] == 1 and out[3, 9] == 2
    assert receipt['retained_additions_px'] <= receipt['proposed_additions_px']
    assert receipt['semantic_quality'] == 'FAIL'
    assert receipt['signed_source_verified_here'] is False
    assert receipt['Phase4'] == 'FAIL'
    assert receipt['contact_receipt']['frozen_owner_pixels_modified'] == 0


def test_new_cross_owner_diagonal_contact_is_pruned():
    x = scene()
    x['class_ids'][2, 4] = 32
    x['anime_classes'][2, 4] = 10
    x['frozen_candidate'][2, 4] = True
    out, receipt = propose_contact_safe_sleeve(**x)
    assert out[3, 1] == 1 and out[3, 9] == 2
    assert receipt['new_cross_owner_edges'] == 0
    assert receipt['frozen_owner_modified_px'] == 0


def test_alpha_and_input_validation_fail_closed():
    x = scene()
    x['source_alpha'][3, 1] = 0
    with pytest.raises(ValueError):
        propose_contact_safe_sleeve(**x)


def test_immutable_input_and_replay_determinism():
    x = scene()
    frozen = x['frozen_owner'].copy()
    a, receipt_a = propose_contact_safe_sleeve(**x)
    b, receipt_b = propose_contact_safe_sleeve(**x)
    assert np.array_equal(a, b)
    assert np.array_equal(x['frozen_owner'], frozen)
    assert receipt_a['owner_sha256'] == receipt_b['owner_sha256']


def test_adjacent_proposals_are_removed_not_frozen_owners():
    cls = np.zeros((7, 7), np.uint8)
    cls[3, 1] = 5
    cls[3, 4] = 10
    cls[3, 2:4] = 32
    anime = np.zeros_like(cls)
    anime[3, 2:4] = 10
    owner = np.zeros_like(cls)
    owner[3, 1] = 1
    owner[3, 4] = 2
    out, receipt = propose_contact_safe_sleeve(
        class_ids=cls, anime_classes=anime,
        source_alpha=np.full_like(cls, 255),
        frozen_candidate=np.isin(cls, (5, 10, 32)), frozen_owner=owner,
    )
    assert np.array_equal(out, owner)
    assert receipt['proposed_additions_px'] == 2
    assert receipt['pruned_additions_px'] == 2
    assert receipt['contact_receipt']['new_cross_owner_4_edges_blocked'] > 0
