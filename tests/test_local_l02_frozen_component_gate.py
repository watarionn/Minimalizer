"""Research-only negative regressions for same-owner component collisions."""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_frozen_component_gate import FrozenComponentHold, prune_frozen_component_joins
from local_l02_guarded_sleeve_contact_replay import propose_contact_safe_sleeve


def test_same_owner_bridge_is_pruned_without_erasing_frozen_islands():
    old = np.zeros((7, 9), np.uint8)
    old[3, 1] = 1
    old[3, 7] = 1
    proposed = old.copy()
    proposed[3, 2:7] = 1
    safe, receipt = prune_frozen_component_joins(frozen_owner=old, proposed_owner=proposed)
    assert safe[3, 1] == safe[3, 7] == 1
    assert receipt['pruned_additions_px'] > 0
    assert receipt['frozen_component_identity_4_and_8'] == 'PRESERVED'


def test_diagonal_only_bridge_is_pruned_under_8_connectivity():
    old = np.zeros((7, 7), np.uint8)
    old[1, 1] = 2
    old[5, 5] = 2
    proposed = old.copy()
    proposed[2, 2] = proposed[3, 3] = proposed[4, 4] = 2
    safe, receipt = prune_frozen_component_joins(frozen_owner=old, proposed_owner=proposed)
    assert safe[1, 1] == safe[5, 5] == 2
    assert receipt['pruned_additions_px'] > 0


def test_frozen_erasure_or_reassignment_rejected():
    old = np.zeros((3, 3), np.uint8)
    old[1, 1] = 1
    for value in (0, 2):
        proposed = old.copy()
        proposed[1, 1] = value
        with pytest.raises(FrozenComponentHold):
            prune_frozen_component_joins(frozen_owner=old, proposed_owner=proposed)


def test_contact_wrapper_preserves_two_same_owner_islands():
    cls = np.zeros((7, 11), np.uint8)
    cls[3, 1] = cls[3, 9] = 5
    cls[3, 2:9] = 32
    anime = np.zeros_like(cls)
    anime[3, 2:9] = 10
    owner = np.zeros_like(cls)
    owner[3, 1] = owner[3, 9] = 1
    out, receipt = propose_contact_safe_sleeve(
        class_ids=cls, anime_classes=anime,
        source_alpha=np.full_like(cls, 255),
        frozen_candidate=np.isin(cls, (5, 10, 32)), frozen_owner=owner)
    assert out[3, 1] == out[3, 9] == 1
    assert receipt['component_receipt']['pruned_additions_px'] > 0
    assert receipt['same_owner_component_identity_4_and_8'] == 'PRESERVED'
