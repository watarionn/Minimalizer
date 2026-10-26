import numpy as np
import pytest
from local_l02_neutral_sleeve_topology_shadow import (
    NeutralSleeveHold, propose_neutral_sleeve_abstention,
)


def scene():
    rgba = np.full((160, 300, 4), 255, dtype=np.uint8)
    rgba[:, :, :3] = (165, 108, 65)
    cls = np.zeros((160, 300), dtype=np.uint8)
    owner = np.zeros((160, 300), dtype=np.uint8)
    cls[10:140, 10:140] = 10
    owner[10:140, 10:140] = 2
    cls[70:85, 140:170] = 32
    owner[70:85, 140:170] = 2
    rgba[70:85, 140:170, :3] = 235
    return rgba, cls, owner


def test_neutral_cuff_removed_and_coat_seed_untouched():
    rgba, cls, owner = scene()
    out, info = propose_neutral_sleeve_abstention(
        rgba=rgba, class_ids=cls, frozen_owner=owner)
    assert info['removed'] == 450
    assert np.all(out[10:140, 10:140] == 2)
    assert not np.any(out[70:85, 140:170])
    assert info['owner_promotion_authorized'] is False
    assert info['Phase4'] == 'FAIL'


def test_mixed_owner_abstains_without_change():
    rgba, cls, owner = scene()
    owner[1:5, 1:5] = 1
    cls[1:5, 1:5] = 5
    out, info = propose_neutral_sleeve_abstention(
        rgba=rgba, class_ids=cls, frozen_owner=owner)
    assert np.array_equal(out, owner)
    assert info['decision'] == 'ABSTAIN_MIXED_OR_NO_COAT_SEED'


def test_neutral_coat_seed_abstains():
    rgba, cls, owner = scene()
    rgba[10:140, 10:140, :3] = 235
    out, info = propose_neutral_sleeve_abstention(
        rgba=rgba, class_ids=cls, frozen_owner=owner)
    assert np.array_equal(out, owner)
    assert info['decision'] == 'ABSTAIN_NEUTRAL_COAT_SEED'


def test_bridge_restoration_keeps_four_connected_parts():
    rgba, cls, owner = scene()
    # Two large coat islands joined by one neutral sleeve strip.
    cls[:] = 0
    owner[:] = 0
    cls[20:130, 10:110] = 10
    owner[20:130, 10:110] = 2
    cls[20:130, 160:260] = 10
    owner[20:130, 160:260] = 2
    cls[70:85, 110:160] = 32
    owner[70:85, 110:160] = 2
    rgba[70:85, 110:160, :3] = 235
    out, info = propose_neutral_sleeve_abstention(
        rgba=rgba, class_ids=cls, frozen_owner=owner)
    assert info['restored_bridges'] > 0
    assert info['removed'] > 0
    assert out.sum() < owner.sum()
    assert out[80, 20] == 2 and out[80, 220] == 2


@pytest.mark.parametrize('bad', ['alpha', 'class', 'owner_dtype', 'owner_id', 'owner_class'])
def test_invalid_source_or_provenance_rejected(bad):
    rgba, cls, owner = scene()
    if bad == 'alpha':
        rgba[70, 140, 3] = 0
    elif bad == 'class':
        cls[70, 140] = 47
    elif bad == 'owner_dtype':
        owner = owner.astype(np.int32)
    elif bad == 'owner_id':
        owner[70, 140] = 3
    else:
        cls[70, 140] = 25
    with pytest.raises(NeutralSleeveHold):
        propose_neutral_sleeve_abstention(
            rgba=rgba, class_ids=cls, frozen_owner=owner)


def test_budget_failure_is_not_quality_pass():
    rgba, cls, owner = scene()
    with pytest.raises(NeutralSleeveHold, match='OWNER_OR_RESTORE_BUDGET'):
        propose_neutral_sleeve_abstention(
            rgba=rgba, class_ids=cls, frozen_owner=owner,
            max_owner_pixels=10)
