"""Source-free invariants for an unapproved sleeve shape-cleanup shadow."""
import numpy as np
import pytest
from local_l02_contact_morphology_shadow import (
    propose_contact_morphology_shadow, ContactMorphologyHold,
)
import local_l02_contact_morphology_shadow as module


def fake_input():
    rgba = np.full((64, 64, 4), 255, dtype=np.uint8)
    cls = np.full((64, 64), 32, dtype=np.uint8)
    anime = np.full((64, 64), 10, dtype=np.uint8)
    owner = np.zeros((64, 64), dtype=np.uint8)
    owner[12:52, 12:26] = 1
    return rgba, cls, anime, owner


def test_keeps_immutable_owner_and_full_sleeve_but_drops_thin_spur(monkeypatch):
    rgba, cls, anime, owner = fake_input()
    proposed = owner.copy()
    proposed[12:52, 26:36] = 1
    proposed[28, 36:50] = 1  # one-pixel spur, not source-supported area
    monkeypatch.setattr(module, 'propose_contact_density_palette_shadow',
                        lambda **kwargs: (proposed, {'schema': 'fixture'}))
    out, meta = propose_contact_morphology_shadow(
        source_rgba=rgba, class_ids=cls, anime_classes=anime,
        baseline_owner=owner)
    assert np.all(out[owner > 0] == owner[owner > 0])
    assert np.count_nonzero((out > 0) & (owner == 0)) >= 350
    assert np.all(out[28, 36:50] == 0)
    assert meta['semantic_quality_pass'] is False
    assert meta['Phase4'] == 'FAIL'


def test_unsupported_alpha_addition_rejected(monkeypatch):
    rgba, cls, anime, owner = fake_input()
    proposed = owner.copy()
    proposed[12:52, 26:36] = 1
    rgba[20:40, 27:35, 3] = 0
    monkeypatch.setattr(module, 'propose_contact_density_palette_shadow',
                        lambda **kwargs: (proposed, {'schema': 'fixture'}))
    with pytest.raises(ContactMorphologyHold, match='SOURCE_OR_OWNER_INVARIANT'):
        propose_contact_morphology_shadow(source_rgba=rgba,
            class_ids=cls, anime_classes=anime, baseline_owner=owner)


def test_source_only_replay_deterministic(monkeypatch):
    rgba, cls, anime, owner = fake_input()
    proposed = owner.copy()
    proposed[12:52, 26:36] = 1
    monkeypatch.setattr(module, 'propose_contact_density_palette_shadow',
                        lambda **kwargs: (proposed, {'schema': 'fixture'}))
    a, receipt_a = propose_contact_morphology_shadow(
        source_rgba=rgba, class_ids=cls, anime_classes=anime,
        baseline_owner=owner)
    b, receipt_b = propose_contact_morphology_shadow(
        source_rgba=rgba, class_ids=cls, anime_classes=anime,
        baseline_owner=owner)
    assert np.array_equal(a, b) and receipt_a == receipt_b
    assert not np.any((a > 0) & (rgba[..., 3] == 0))
