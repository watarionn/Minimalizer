"""Source-only opt-in integration checks, never a semantic PASS."""
import numpy as np
import pytest
from tools.research import local_l02_composed_dual_contact_shadow as m
from tools.research import local_l02_selective_signed_comparison as runner


def fixture():
    rgba = np.zeros((35, 35, 4), dtype=np.uint8)
    rgba[..., 3] = 255
    classes = np.zeros((35, 35), dtype=np.uint8)
    anime = np.full((35, 35), 10, dtype=np.uint8)
    frozen = np.zeros((35, 35), dtype=np.uint8)
    frozen[25, 5] = 1; frozen[25, 25] = 2
    proposal = frozen.copy()
    proposal[10:25, 5] = 1
    proposal[3:10, 2:17] = 1
    proposal[25, 20:25] = 2
    proposal[15:25, 20] = 2
    proposal[15, 6:20] = 2
    classes[frozen == 1] = 5
    classes[frozen == 2] = 10
    classes[(frozen == 0) & (proposal > 0)] = 32
    return rgba, classes, anime, frozen, proposal


def test_optin_selective_preserves_more_than_default(monkeypatch):
    rgba, classes, anime, frozen, proposal = fixture()
    monkeypatch.setattr(m, 'propose_composed_p0_shadow',
                        lambda **kw: (frozen.copy(), {'schema': 'core'}))
    monkeypatch.setattr(m, 'propose_class30_dual_seed_extension_shadow',
                        lambda **kw: (frozen.copy(), {'schema': 'dual'}))
    monkeypatch.setattr(m, 'propose_independent_contact_shadow',
                        lambda **kw: (proposal.copy(), {'schema': 'contact'}))
    common = dict(source_rgba=rgba, class_ids=classes, anime_classes=anime, frozen_owner=frozen)
    default, d = m.propose_composed_dual_contact_shadow(**common)
    conservative, c = m.propose_composed_dual_contact_shadow(**common, contact_repair_mode='conservative')
    selective, s = m.propose_composed_dual_contact_shadow(**common, contact_repair_mode='selective')
    assert np.array_equal(default, conservative)
    assert s['net_added_source_supported_px'] > c['net_added_source_supported_px']
    assert s['contact_repair_mode'] == 'selective'
    assert d['contact_repair_mode'] == 'conservative'
    assert s['Phase4'] == 'FAIL' and s['production'] == 'NO_GO'


def test_rejects_invalid_mode_without_running_any_stages(monkeypatch):
    rgba, classes, anime, frozen, proposal = fixture()
    def must_not_call(**kw):
        raise AssertionError('stage should not run')
    monkeypatch.setattr(m, 'propose_composed_p0_shadow', must_not_call)
    with pytest.raises(m.DualContactHold, match='UNRECOGNIZED'):
        m.propose_composed_dual_contact_shadow(
            source_rgba=rgba, class_ids=classes, anime_classes=anime,
            frozen_owner=frozen, contact_repair_mode='auto')


def test_signed_runner_rejects_unpinned_case_before_private_archive_access():
    with pytest.raises(ValueError, match='UNPINNED'):
        runner.run(None, cases=('H04',))
    with pytest.raises(ValueError, match='DUPLICATED'):
        runner.run(None, cases=('H06', 'H06'))


def test_signed_comparison_uses_known_fn_and_freezes_all_candidates_before_labels(monkeypatch):
    # The postscore contract returns known_FN, never FN. Synthetic owner
    # arrays here are only a runner-contract fixture, not a quality claim.
    rgba = np.zeros((8, 8, 4), dtype=np.uint8)
    rgba[..., 3] = 255
    classes = np.full((8, 8), 32, dtype=np.uint8)
    anime = np.zeros((8, 8), dtype=np.uint8)
    owner = np.zeros((8, 8), dtype=np.uint8)
    owner[2, 2] = 1
    owner[5, 5] = 2
    calls = []
    monkeypatch.setattr(runner, 'verify_archives', lambda folder: {'pinned': 4})
    monkeypatch.setattr(runner, 'load_source_only',
                        lambda folder, case: (rgba, classes, owner, anime))
    def proposal(**kwargs):
        calls.append(('propose', kwargs['contact_repair_mode']))
        return owner.copy(), {'cross_owner_contact_addition_repair': {'verified': True}}
    monkeypatch.setattr(runner, 'propose_composed_dual_contact_shadow', proposal)
    monkeypatch.setattr(runner, 'verify_no_new_cross_owner_contacts', lambda **kwargs: None)
    monkeypatch.setattr(runner, 'components', lambda output: {'owner1_4': 1, 'owner2_4': 1})
    def score(folder, case, output):
        calls.append(('postscore', case))
        # Known positives/negatives are exposed only AFTER all four proposals.
        assert sum(k == 'propose' for k, _ in calls) == 4
        assert np.array_equal(output, owner)
        return {'TP': 5, 'known_FP': 2, 'known_FN': 7}
    monkeypatch.setattr(runner, 'postscore', score)
    result = runner.run(None)
    assert result['cases']['H06']['comparison'] == {
        'known_TP_delta': 0, 'known_FP_delta': 0, 'known_FN_delta': 0,
        'quality_pass': False, 'candidate_auto_promoted': False}
    assert result['cases']['H08']['comparison']['known_FN_delta'] == 0
    assert result['both_candidates_frozen_before_postscore'] is True
    assert result['Phase4'] == 'FAIL' and result['production'] == 'NO_GO'
    assert '_owner_for_postscore' not in str(result)
