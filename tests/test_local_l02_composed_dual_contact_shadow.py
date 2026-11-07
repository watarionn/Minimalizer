"""Fail-closed source-only stage composition. No private/annotation input."""
import numpy as np
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))

from tools.research import local_l02_composed_dual_contact_shadow as m


def _fixture():
    rgba = np.zeros((4, 5, 4), dtype=np.uint8)
    rgba[..., 3] = 255
    cls = np.zeros((4, 5), dtype=np.uint8)
    anime = np.full((4, 5), 10, dtype=np.uint8)
    owner = np.zeros((4, 5), dtype=np.uint8)
    cls[1, 1:4] = [5, 30, 32]
    owner[1, 1] = 1
    return rgba, cls, anime, owner


def _mock(monkeypatch, *, core=None, dual=None, final=None):
    def first(*, frozen_owner, **kw):
        return (core if core is not None else frozen_owner).copy(), {'schema': 'core'}
    def second(*, frozen_owner, **kw):
        return (dual if dual is not None else frozen_owner).copy(), {'schema': 'dual'}
    def third(*, baseline_owner, **kw):
        return (final if final is not None else baseline_owner).copy(), {'schema': 'contact'}
    monkeypatch.setattr(m, 'propose_composed_p0_shadow', first)
    monkeypatch.setattr(m, 'propose_class30_dual_seed_extension_shadow', second)
    monkeypatch.setattr(m, 'propose_independent_contact_shadow', third)


def test_fixed_order_additions_and_explicit_hold(monkeypatch):
    rgba, cls, anime, owner = _fixture()
    dual = owner.copy(); dual[1, 2] = 1
    final = dual.copy(); final[1, 3] = 1
    _mock(monkeypatch, dual=dual, final=final)
    result, meta = m.propose_composed_dual_contact_shadow(
        source_rgba=rgba, class_ids=cls, anime_classes=anime, frozen_owner=owner)
    assert np.array_equal(result, final)
    assert (meta['dual_stage_added_px'], meta['contact_stage_added_px']) == (1, 1)
    assert meta['human_annotations_used_for_inference'] is False
    assert meta['semantic_quality_pass'] is False
    assert meta['Phase4'] == 'FAIL' and meta['L03'] == 'NO_GO'


def test_earlier_owner_veto_cannot_be_resurrected(monkeypatch):
    rgba, cls, anime, owner = _fixture()
    core = owner.copy(); core[1, 1] = 0
    final = owner.copy()
    _mock(monkeypatch, core=core, final=final)
    with pytest.raises(m.DualContactHold, match='PREVIOUS_VETO_RESURRECTED'):
        m.propose_composed_dual_contact_shadow(
            source_rgba=rgba, class_ids=cls, anime_classes=anime, frozen_owner=owner)


def test_final_stage_cannot_delete_previous_owner(monkeypatch):
    rgba, cls, anime, owner = _fixture()
    final = owner.copy(); final[1, 1] = 0
    _mock(monkeypatch, final=final)
    with pytest.raises(m.DualContactHold, match='CORE_OWNER_ERASURE'):
        m.propose_composed_dual_contact_shadow(
            source_rgba=rgba, class_ids=cls, anime_classes=anime, frozen_owner=owner)


def test_no_additions_outside_source(monkeypatch):
    rgba, cls, anime, owner = _fixture()
    rgba[1, 3, 3] = 0
    final = owner.copy(); final[1, 3] = 1
    _mock(monkeypatch, final=final)
    with pytest.raises(m.DualContactHold, match='SOURCE_ALPHA_ESCAPE'):
        m.propose_composed_dual_contact_shadow(
            source_rgba=rgba, class_ids=cls, anime_classes=anime, frozen_owner=owner)


def test_no_class5_unowned_promotion(monkeypatch):
    rgba, cls, anime, owner = _fixture()
    cls[1, 2] = 5
    final = owner.copy(); final[1, 2] = 1
    _mock(monkeypatch, final=final)
    with pytest.raises(m.DualContactHold, match='UNAUTHORIZED_CLASS_PROMOTION'):
        m.propose_composed_dual_contact_shadow(
            source_rgba=rgba, class_ids=cls, anime_classes=anime, frozen_owner=owner)


def test_no_orphan_owner_component(monkeypatch):
    rgba, cls, anime, owner = _fixture()
    cls[3, 4] = 32
    final = owner.copy(); final[3, 4] = 1
    _mock(monkeypatch, final=final)
    with pytest.raises(ValueError, match='OWNER_COMPONENT_COUNT_CHANGED'):
        m.propose_composed_dual_contact_shadow(
            source_rgba=rgba, class_ids=cls, anime_classes=anime, frozen_owner=owner)

@pytest.mark.parametrize('introduced_at', ['core', 'dual'])
def test_contact_prune_may_remove_unsafe_earlier_stage_addition_but_not_frozen(monkeypatch, introduced_at):
    """P0: a new unsafe proposed pixel is not an immutable owner seed."""
    rgba = np.zeros((9, 9, 4), dtype=np.uint8)
    rgba[..., 3] = 255
    cls = np.zeros((9, 9), dtype=np.uint8)
    anime = np.full((9, 9), 10, dtype=np.uint8)
    frozen = np.zeros((9, 9), dtype=np.uint8)
    frozen[4, 2] = 1
    frozen[4, 4] = 2
    cls[4, 2] = 5
    cls[4, 4] = 10
    cls[4, 3] = 32
    unsafe = frozen.copy()
    unsafe[4, 3] = 1
    if introduced_at == 'core':
        _mock(monkeypatch, core=unsafe, dual=unsafe, final=unsafe)
    else:
        _mock(monkeypatch, core=frozen, dual=unsafe, final=unsafe)
    repaired, meta = m.propose_composed_dual_contact_shadow(
        source_rgba=rgba, class_ids=cls, anime_classes=anime, frozen_owner=frozen)
    assert np.array_equal(repaired, frozen)
    assert meta['pruned_earlier_stage_additions_px'] == 1
    assert meta['cross_owner_contact_addition_repair']['newly_added_owner_pixels_removed'] == 1
    assert meta['Phase4'] == 'FAIL'
