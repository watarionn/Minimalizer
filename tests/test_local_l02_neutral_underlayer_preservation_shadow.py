import sys
from pathlib import Path
import numpy as np
import pytest
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
import local_l02_neutral_underlayer_preservation_shadow as m


def fake_input():
    rgba = np.zeros((48, 48, 4), dtype=np.uint8)
    rgba[..., :3] = [235, 230, 225]
    rgba[..., 3] = 255
    classes = np.full((48, 48), 32, dtype=np.uint8)
    owner = np.zeros((48, 48), dtype=np.uint8)
    owner[4:44, 4:44] = 2
    classes[4:14, 4:44] = 10
    return rgba, classes, owner


def fake_hue(*, source_rgba, class_ids, frozen_owner):
    out = frozen_owner.copy()
    out[24:44, 4:44] = 0
    return out, {}


def test_provisional_layer_is_source_bound_and_disjoint(monkeypatch):
    monkeypatch.setattr(m, 'propose_hue_extended_owner_shadow', fake_hue)
    # Component-identity verification is the responsibility of the hue stage.
    monkeypatch.setattr(m, '_assert_component_identity', lambda *args: 1)
    rgba, cls, owner = fake_input()
    # 800px is smaller than the existing 1024px floor: abstain.
    coat, provisional, receipt = m.propose_neutral_underlayer_preservation_shadow(
        source_rgba=rgba, class_ids=cls, frozen_owner=owner)
    assert not provisional.any()
    assert receipt['underlayer_semantic_owner_authorized'] is False
    assert receipt['Phase4'] == 'FAIL'
    assert not np.any(provisional & (coat > 0))


def test_large_neutral_component_retained_without_promotion(monkeypatch):
    monkeypatch.setattr(m, 'propose_hue_extended_owner_shadow', fake_hue)
    monkeypatch.setattr(m, '_assert_component_identity', lambda *args: 1)
    rgba, cls, owner = fake_input()
    rgba = np.zeros((64, 64, 4), dtype=np.uint8)
    rgba[..., :3] = [240, 240, 240]
    rgba[..., 3] = 255
    cls = np.full((64, 64), 32, dtype=np.uint8)
    owner = np.zeros((64, 64), dtype=np.uint8)
    owner[4:60, 4:60] = 2
    cls[4:14, 4:60] = 10
    def hue2(*, source_rgba, class_ids, frozen_owner):
        out = frozen_owner.copy(); out[14:60, 4:60] = 0; return out, {}
    monkeypatch.setattr(m, 'propose_hue_extended_owner_shadow', hue2)
    coat, candidate, receipt = m.propose_neutral_underlayer_preservation_shadow(
        source_rgba=rgba, class_ids=cls, frozen_owner=owner)
    assert candidate.sum() >= 1024
    assert np.all(owner[candidate] == 2)
    assert np.all(coat[candidate] == 0)
    assert receipt['human_labels_used_for_inference'] is False


@pytest.mark.parametrize('change', ['alpha','class','owner1','dtype','shape'])
def test_invalid_or_multicoat_input_fails_closed(change):
    rgba, cls, owner = fake_input()
    if change == 'alpha': rgba[5,5,3] = 0
    if change == 'class': cls[5,5] = 47
    if change == 'owner1': owner[5,5] = 1
    if change == 'dtype': cls = cls.astype(np.int16)
    if change == 'shape': cls = cls[:-1]
    with pytest.raises(m.NeutralUnderlayerHold):
        m.propose_neutral_underlayer_preservation_shadow(
            source_rgba=rgba, class_ids=cls, frozen_owner=owner)


def test_composed_provenance_preserves_original_abstained_source_pixels(monkeypatch):
    rgba = np.zeros((64, 64, 4), dtype=np.uint8)
    rgba[..., :3] = [240, 240, 240]
    rgba[..., 3] = 255
    cls = np.full((64, 64), 32, dtype=np.uint8)
    owner = np.zeros((64, 64), dtype=np.uint8)
    owner[4:60, 4:60] = 2
    cls[4:14, 4:60] = 10
    composed = owner.copy()
    composed[14:60, 4:60] = 0
    cls[3, 10] = 30
    composed[3, 10] = 2  # connected permitted source promotion
    hue_reference = owner.copy()
    hue_reference[14:60, 4:60] = 0
    monkeypatch.setattr(m, 'propose_hue_extended_owner_shadow',
                        lambda **kwargs: (hue_reference, {}))
    coat, candidate, receipt = m.propose_neutral_underlayer_preservation_shadow(
        source_rgba=rgba, class_ids=cls, frozen_owner=owner,
        composed_owner=composed, anime_classes=np.full(cls.shape, 10, dtype=np.uint8))
    assert np.array_equal(coat, composed)
    assert candidate.sum() >= 1024
    assert receipt['provenance_stage'] == 'composed_owner_provenance'
    assert receipt['composed_owner_input_promotions'] == 1
    assert receipt['composed_class30_independent_support_verified'] is True
    assert receipt['underlayer_semantic_owner_authorized'] is False
    assert receipt['Phase4'] == 'FAIL'
    assert not np.any(candidate & (coat > 0))


@pytest.mark.parametrize('bad', ['alpha', 'reassign', 'promote_bad_class', 'owner1', 'dtype', 'shape', 'erase_coat_core', 'erase_extension'])
def test_composed_invalid_contract_fails_closed(bad):
    rgba = np.zeros((64, 64, 4), dtype=np.uint8)
    rgba[..., :3] = [240, 240, 240]
    rgba[..., 3] = 255
    cls = np.full((64, 64), 32, dtype=np.uint8)
    owner = np.zeros((64, 64), dtype=np.uint8)
    owner[4:60, 4:60] = 2
    cls[4:14, 4:60] = 10
    composed = owner.copy()
    if bad == 'alpha':
        rgba[5, 5, 3] = 0
    elif bad == 'reassign':
        composed[5, 5] = 1
    elif bad == 'promote_bad_class':
        composed[0, 0] = 2
    elif bad == 'owner1':
        composed[0, 0] = 1
    elif bad == 'erase_coat_core':
        # Removing a 3x3 interior patch preserves 4/8 component counts,
        # but silently destroys signed class10 coat pixels.
        composed[6:9, 6:9] = 0
    elif bad == 'erase_extension':
        # Previously retained class30 source pixels are not hue abstentions.
        cls[20, 20] = 30
        composed[20, 20] = 0
    elif bad == 'dtype':
        composed = composed.astype(np.int16)
    elif bad == 'shape':
        composed = composed[:-1]
    with pytest.raises(m.NeutralUnderlayerHold):
        m.propose_neutral_underlayer_preservation_shadow(
            source_rgba=rgba, class_ids=cls, frozen_owner=owner, composed_owner=composed)


def test_composed_class32_coat_color_erasure_requires_hue_provenance(monkeypatch):
    """A class32 hole can preserve topology but is not hue-authorized."""
    rgba = np.zeros((64, 64, 4), dtype=np.uint8)
    rgba[..., :3] = [240, 240, 240]
    rgba[..., 3] = 255
    cls = np.full((64, 64), 32, dtype=np.uint8)
    owner = np.zeros((64, 64), dtype=np.uint8)
    owner[4:60, 4:60] = 2
    cls[4:14, 4:60] = 10
    hue_reference = owner.copy()
    hue_reference[40:60, 4:60] = 0
    composed = hue_reference.copy()
    composed[20:23, 20:23] = 0  # extra class32 interior hole
    for connectivity in (1, 2):
        structure = ndimage.generate_binary_structure(2, connectivity)
        assert ndimage.label(owner == 2, structure)[1] == ndimage.label(
            composed == 2, structure)[1]
    monkeypatch.setattr(m, 'propose_hue_extended_owner_shadow',
                        lambda **kwargs: (hue_reference, {}))
    with pytest.raises(
            m.NeutralUnderlayerHold,
            match='COMPOSED_CLASS32_ERASURE_NOT_IN_HUE_REPLAY'):
        m.propose_neutral_underlayer_preservation_shadow(
            source_rgba=rgba, class_ids=cls, frozen_owner=owner,
            composed_owner=composed)


@pytest.mark.parametrize('hold_type', [m.ExtendedOwnerHold, ValueError])
def test_composed_unverifiable_hue_reference_fails_closed(monkeypatch, hold_type):
    rgba = np.zeros((64, 64, 4), dtype=np.uint8)
    rgba[..., :3] = [240, 240, 240]
    rgba[..., 3] = 255
    cls = np.full((64, 64), 32, dtype=np.uint8)
    owner = np.zeros((64, 64), dtype=np.uint8)
    owner[4:60, 4:60] = 2
    cls[4:14, 4:60] = 10
    def unverifiable(**kwargs):
        raise hold_type('MISSING_FROZEN_HUE_EVIDENCE')
    monkeypatch.setattr(m, 'propose_hue_extended_owner_shadow',
                        unverifiable)
    with pytest.raises(
            m.NeutralUnderlayerHold,
            match='COMPOSED_HUE_PROVENANCE_UNVERIFIED'):
        m.propose_neutral_underlayer_preservation_shadow(
            source_rgba=rgba, class_ids=cls, frozen_owner=owner,
            composed_owner=owner.copy())


def test_composed_cannot_resurrect_source_hue_abstention(monkeypatch):
    """Topology counts and deletion-subset checks miss coat re-admission."""
    rgba, cls, frozen = fake_input()
    hue_reference = frozen.copy()
    hue_reference[24:44, 4:44] = 0  # class32 abstained without splitting coat
    # A composed owner that reassigns the removed cuff to coat used to pass:
    # it has no extra erasures and its 4/8 component counts are unchanged.
    composed = frozen.copy()
    for connectivity in (1, 2):
        structure = ndimage.generate_binary_structure(2, connectivity)
        assert ndimage.label(frozen == 2, structure)[1] == ndimage.label(
            composed == 2, structure)[1]
    monkeypatch.setattr(m, 'propose_hue_extended_owner_shadow',
                        lambda **kwargs: (hue_reference, {}))
    with pytest.raises(m.NeutralUnderlayerHold,
                       match='COMPOSED_HUE_ABSTENTION_RESURRECTION'):
        m.propose_neutral_underlayer_preservation_shadow(
            source_rgba=rgba, class_ids=cls, frozen_owner=frozen,
            composed_owner=composed)
    # Keeping the hue abstention is allowed; the coat is never promoted.
    kept, candidate, receipt = m.propose_neutral_underlayer_preservation_shadow(
        source_rgba=rgba, class_ids=cls, frozen_owner=frozen,
        composed_owner=hue_reference.copy())
    assert np.array_equal(kept, hue_reference)
    assert not np.any(candidate & (kept > 0))
    assert receipt['Phase4'] == 'FAIL'


def test_boundary_core_keeps_two_coherent_source_islands(monkeypatch):
    """Only source-backed cuff interiors survive; no owner is promoted."""
    rgba = np.zeros((140, 140, 4), dtype=np.uint8)
    rgba[..., :3] = [240, 240, 240]
    rgba[..., 3] = 255
    cls = np.full((140, 140), 32, dtype=np.uint8)
    owner = np.zeros((140, 140), dtype=np.uint8)
    for left, right in ((10, 60), (80, 130)):
        owner[10:70, left:right] = 2
        cls[10:20, left:right] = 10
    def hue_two(*, source_rgba, class_ids, frozen_owner):
        out = frozen_owner.copy()
        out[20:70, 10:60] = 0
        out[20:70, 80:130] = 0
        return out, {}
    monkeypatch.setattr(m, 'propose_hue_extended_owner_shadow', hue_two)
    monkeypatch.setattr(m, '_assert_component_identity', lambda *args: 1)
    coat, core, receipt = m.propose_neutral_underlayer_boundary_core_shadow(
        source_rgba=rgba, class_ids=cls, frozen_owner=owner)
    assert core.sum() == 2 * 46 * 46
    assert receipt['original_provisional_source_pixels'] == 5000
    assert receipt['boundary_abstained_source_pixels'] == 5000 - core.sum()
    assert receipt['core_components_8'] == 2
    assert not np.any(core & (coat > 0))
    assert np.all(owner[core] == 2)
    assert receipt['underlayer_semantic_owner_authorized'] is False
    assert receipt['Phase4'] == 'FAIL'


def test_boundary_core_rejects_eroded_bridge_fragmentation(monkeypatch):
    """A narrow connection may not silently disappear to improve metrics."""
    rgba = np.zeros((120, 120, 4), dtype=np.uint8)
    rgba[..., 3] = 255
    owner = np.zeros((120, 120), dtype=np.uint8)
    cls = np.zeros((120, 120), dtype=np.uint8)
    candidate = np.zeros((120, 120), dtype=bool)
    candidate[20:65, 10:50] = True
    candidate[20:65, 70:110] = True
    candidate[41:43, 50:70] = True
    assert ndimage.label(candidate, structure=np.ones((3, 3)))[1] == 1
    monkeypatch.setattr(
        m, 'propose_neutral_underlayer_preservation_shadow',
        lambda **kwargs: (owner.copy(), candidate.copy(), {
            'schema': 'minimalizer/local-l02/test-source-only/v1'}))
    with pytest.raises(m.NeutralUnderlayerHold,
                       match='BOUNDARY_CORE_COMPONENT_RETENTION_HOLD'):
        m.propose_neutral_underlayer_boundary_core_shadow(
            source_rgba=rgba, class_ids=cls, frozen_owner=owner)


def test_boundary_core_refuses_zero_candidate(monkeypatch):
    rgba, cls, owner = fake_input()
    monkeypatch.setattr(m, 'propose_hue_extended_owner_shadow', fake_hue)
    monkeypatch.setattr(m, '_assert_component_identity', lambda *args: 1)
    with pytest.raises(m.NeutralUnderlayerHold,
                       match='BOUNDARY_CORE_COMPONENT_RETENTION_HOLD'):
        m.propose_neutral_underlayer_boundary_core_shadow(
            source_rgba=rgba, class_ids=cls, frozen_owner=owner)


def test_composed_unowned_class32_promotion_refused_even_if_connected(monkeypatch):
    """A source-backed class32 addition is not independently coat-authorized."""
    rgba = np.zeros((64, 64, 4), dtype=np.uint8)
    rgba[..., :3] = [240, 240, 240]
    rgba[..., 3] = 255
    cls = np.full((64, 64), 32, dtype=np.uint8)
    frozen = np.zeros((64, 64), dtype=np.uint8)
    frozen[4:60, 4:60] = 2
    cls[4:14, 4:60] = 10
    hue_reference = frozen.copy()
    hue_reference[14:60, 4:60] = 0
    monkeypatch.setattr(m, 'propose_hue_extended_owner_shadow',
                        lambda **kwargs: (hue_reference, {}))
    # Both alternatives touch the original coat and preserve component count.
    for class_id, should_reject in ((32, True), (30, False)):
        classes = cls.copy()
        classes[3, 10] = class_id
        composed = hue_reference.copy()
        composed[3, 10] = 2
        for connectivity in (1, 2):
            structure = ndimage.generate_binary_structure(2, connectivity)
            assert ndimage.label(hue_reference == 2, structure)[1] == (
                ndimage.label(composed == 2, structure)[1])
        if should_reject:
            with pytest.raises(m.NeutralUnderlayerHold,
                               match='INVALID_COMPOSED_OWNER_PROVENANCE'):
                m.propose_neutral_underlayer_preservation_shadow(
                    source_rgba=rgba, class_ids=classes,
                    frozen_owner=frozen, composed_owner=composed)
        else:
            coat, candidate, receipt = (
                m.propose_neutral_underlayer_preservation_shadow(
                    source_rgba=rgba, class_ids=classes,
                    frozen_owner=frozen, composed_owner=composed,
                    anime_classes=np.full(cls.shape, 10, dtype=np.uint8)))
            assert np.array_equal(coat, composed)
            assert receipt['composed_owner_input_promotions'] == 1
            assert receipt['underlayer_semantic_owner_authorized'] is False


def test_composed_class30_promotion_requires_frozen_independent_evidence(monkeypatch):
    """A class30 source label alone cannot make skin/underlayer into coat."""
    rgba = np.zeros((64, 64, 4), dtype=np.uint8)
    rgba[..., :3] = [240, 240, 240]
    rgba[..., 3] = 255
    classes = np.full((64, 64), 32, dtype=np.uint8)
    frozen = np.zeros((64, 64), dtype=np.uint8)
    frozen[4:60, 4:60] = 2
    classes[4:14, 4:60] = 10
    hue = frozen.copy()
    hue[14:60, 4:60] = 0
    classes[3, 10] = 30
    composed = hue.copy()
    composed[3, 10] = 2
    monkeypatch.setattr(m, 'propose_hue_extended_owner_shadow',
                        lambda **kwargs: (hue, {}))
    with pytest.raises(m.NeutralUnderlayerHold,
                       match='COMPOSED_INDEPENDENT_OBSERVER_REQUIRED'):
        m.propose_neutral_underlayer_preservation_shadow(
            source_rgba=rgba, class_ids=classes,
            frozen_owner=frozen, composed_owner=composed)
    independent = np.full(classes.shape, 10, dtype=np.uint8)
    independent[3, 10] = 0
    with pytest.raises(m.NeutralUnderlayerHold,
                       match='COMPOSED_CLASS30_INDEPENDENT_SUPPORT_HOLD'):
        m.propose_neutral_underlayer_preservation_shadow(
            source_rgba=rgba, class_ids=classes,
            frozen_owner=frozen, composed_owner=composed,
            anime_classes=independent)
    independent[3, 10] = 10
    coat, _, receipt = m.propose_neutral_underlayer_preservation_shadow(
        source_rgba=rgba, class_ids=classes, frozen_owner=frozen,
        composed_owner=composed, anime_classes=independent)
    assert np.array_equal(coat, composed)
    assert receipt['composed_class30_independent_support_verified'] is True
    assert receipt['underlayer_semantic_owner_authorized'] is False
    assert receipt['Phase4'] == 'FAIL'


def test_boundary_core_forwards_independent_observer(monkeypatch):
    rgba = np.zeros((64, 64, 4), dtype=np.uint8)
    rgba[..., 3] = 255
    classes = np.full((64, 64), 32, dtype=np.uint8)
    owner = np.zeros((64, 64), dtype=np.uint8)
    composed = owner.copy()
    independent = np.full((64, 64), 10, dtype=np.uint8)
    candidate = np.zeros((64, 64), dtype=bool)
    candidate[4:60, 4:60] = True
    captured = {}
    def capture(**kwargs):
        captured.update(kwargs)
        return owner.copy(), candidate.copy(), {
            'schema': 'minimalizer/local-l02/test-source-only/v1',
            'underlayer_semantic_owner_authorized': False,
        }
    monkeypatch.setattr(m, 'propose_neutral_underlayer_preservation_shadow', capture)
    _, core, receipt = m.propose_neutral_underlayer_boundary_core_shadow(
        source_rgba=rgba, class_ids=classes, frozen_owner=owner,
        composed_owner=composed, anime_classes=independent)
    assert captured['anime_classes'] is independent
    assert captured['composed_owner'] is composed
    assert core.sum() == 52 * 52
    assert receipt['underlayer_semantic_owner_authorized'] is False
    assert receipt['Phase4'] == 'FAIL'
