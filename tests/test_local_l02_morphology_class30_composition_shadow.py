"""Source-free order, veto, SHA and provenance regressions."""
import hashlib
import numpy as np
import pytest
import local_l02_morphology_class30_composition_shadow as composition
import local_l02_contact_morphology_shadow as morphology


def fixture():
    rgba = np.full((64, 64, 4), 255, dtype=np.uint8)
    classes = np.full((64, 64), 32, dtype=np.uint8)
    anime = np.full((64, 64), 10, dtype=np.uint8)
    owner = np.zeros((64, 64), dtype=np.uint8)
    owner[12:52, 12:26] = 1
    classes[12:52, 36:40] = 30
    return rgba, classes, anime, owner


def test_morphology_precedes_optin_and_veto_cannot_resurrect(monkeypatch):
    rgba, cls, anime, owner = fixture()
    first = owner.copy()
    first[12:52, 26:36] = 1
    first[28, 40:50] = 1  # thin class32 spur

    def palette(*, baseline_owner, eligible_classes=(32,), **kwargs):
        if eligible_classes == (32,):
            assert np.array_equal(baseline_owner, owner)
            return first.copy(), {'schema': 'palette'}
        assert eligible_classes == (30, 32)
        out = baseline_owner.copy()
        out[12:52, 36:40] = 1
        out[28, 40:50] = 1  # opt-in attempts to resurrect vetoed spur
        return out, {'schema': 'optin'}

    monkeypatch.setattr(composition, 'propose_contact_density_palette_shadow', palette)
    monkeypatch.setattr(morphology, 'propose_contact_density_palette_shadow', palette)
    out, meta = composition.propose_morphology_then_class30_shadow(
        source_rgba=rgba, class_ids=cls, anime_classes=anime,
        pre_palette_owner=owner,
        expected_pre_palette_sha256=hashlib.sha256(owner.tobytes()).hexdigest())
    assert np.all(out[owner > 0] == 1)
    assert np.all(out[28, 40:50] == 0)
    assert meta['optin_attempted_veto_resurrection_px'] == 10
    assert meta['veto_resurrected_after_final_px'] == 0
    assert meta['new_class30_px'] > 0
    assert meta['Phase4'] == 'FAIL'


def test_wrong_stage_pin_rejected_before_any_inference(monkeypatch):
    rgba, cls, anime, owner = fixture()
    monkeypatch.setattr(composition, 'propose_contact_density_palette_shadow',
                        lambda **kwargs: pytest.fail('upstream must not run'))
    with pytest.raises(composition.MorphologyClass30Hold,
                       match='PRE_PALETTE_OWNER_SHA_MISMATCH'):
        composition.propose_morphology_then_class30_shadow(
            source_rgba=rgba, class_ids=cls, anime_classes=anime,
            pre_palette_owner=owner, expected_pre_palette_sha256='0' * 64)


def test_invalid_pin_rejected():
    rgba, cls, anime, owner = fixture()
    with pytest.raises(composition.MorphologyClass30Hold,
                       match='INVALID_PRE_PALETTE_PIN'):
        composition.propose_morphology_then_class30_shadow(
            source_rgba=rgba, class_ids=cls, anime_classes=anime,
            pre_palette_owner=owner, expected_pre_palette_sha256='unverified')


def test_class32_optin_cannot_bypass_morphology_approval(monkeypatch):
    """A fresh class32 region may become connected via class30 but is not approved."""
    rgba, cls, anime, owner = fixture()
    first = owner.copy()
    first[12:52, 26:36] = 1

    def palette(*, baseline_owner, eligible_classes=(32,), **kwargs):
        if eligible_classes == (32,):
            assert np.array_equal(baseline_owner, owner)
            return first.copy(), {'schema': 'palette'}
        assert eligible_classes == (30, 32)
        out = baseline_owner.copy()
        out[12:52, 36:40] = 1  # class30, legitimate opt-in
        out[20:25, 40:44] = 1   # class32, absent from morphology result
        return out, {'schema': 'optin'}

    monkeypatch.setattr(composition, 'propose_contact_density_palette_shadow', palette)
    monkeypatch.setattr(morphology, 'propose_contact_density_palette_shadow', palette)
    out, meta = composition.propose_morphology_then_class30_shadow(
        source_rgba=rgba, class_ids=cls, anime_classes=anime,
        pre_palette_owner=owner,
        expected_pre_palette_sha256=hashlib.sha256(owner.tobytes()).hexdigest())
    assert np.count_nonzero(out[20:25, 40:44]) == 0
    assert meta['unvetted_class32_optin_vetoed_px'] == 20
    assert meta['new_class30_px'] > 0
    assert meta['new_class32_px'] > 0  # previously morphology-approved sleeve
    assert meta['Phase4'] == 'FAIL'
