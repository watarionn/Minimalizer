"""Source-free strict-replay ordering tests for deferred executable imports.

The runner intentionally imports executable stages only after lineage and
wrapper verification. Patch the actual import targets, not removed runner
module globals. These tests do not assert semantic owner quality.
"""
import hashlib
import sys
import types

import numpy as np
import pytest

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))

from tools.research import local_l02_canonical_strict_signed_replay as m


def test_guarded_wrapper_source_pin_is_exact_and_distinct_from_stale_h08():
    actual = hashlib.sha256(
        (m.Path(m.__file__).parent / 'local_l02_composed_dual_contact_shadow.py').read_bytes()
    ).hexdigest()
    assert actual == m.PINNED_GUARDED_WRAPPER_SHA256
    assert m.PINNED_COMPOSED['H08'] == '3e46769428946d54f0cc441ead77699a81839cd8e372ca39212e5b7825ee4a1a'
    assert m.PINNED_STRICT['H08'] == '32bb5266a479ce64571f190ffebe90b50c01329598408019b363c5ab0c9f0778'
    assert m.PINNED_COMPOSED['H08'] != '82313762a406ec225cf4a79675772c9bc71fefa77d6d48e6613b48cebf884552'


def test_wrapper_drift_fails_before_private_archive_read(monkeypatch, tmp_path):
    monkeypatch.setattr(m, 'verify_pr_replay_lineage',
                        lambda: {'verified_dependency_blobs': 23})
    monkeypatch.setattr(m, 'PINNED_GUARDED_WRAPPER_SHA256', '0' * 64)
    # No private archives exist. The guard must fail before any stage import.
    with pytest.raises(ValueError, match='GUARDED_STAGING_WRAPPER_SHA_MISMATCH'):
        m.replay(tmp_path, 'H08')
    assert list(tmp_path.iterdir()) == []


def test_rejects_unpinned_character_before_private_read(tmp_path):
    with pytest.raises(ValueError, match='ONLY_PINNED_EXPOSED_CASES'):
        m.replay(tmp_path, 'H04')


def test_proposals_frozen_and_pinned_before_human_postscore(monkeypatch, tmp_path):
    rgba = np.zeros((5, 5, 4), dtype=np.uint8)
    rgba[..., 3] = 255
    classes = np.zeros((5, 5), dtype=np.uint8)
    frozen = np.zeros((5, 5), dtype=np.uint8)
    frozen[2, 1] = 1
    classes[2, 1] = 5
    classes[2, 2] = 32
    composed = frozen.copy()
    strict = composed.copy()
    strict[2, 2] = 1
    events = []

    def first(**kwargs):
        events.append('compose')
        return composed.copy(), {'schema': 'compose'}

    def second(**kwargs):
        events.append('strict')
        return strict.copy(), {'schema': 'strict'}

    def postscore(*args):
        events.append('postscore')
        assert events[:2] == ['compose', 'strict']
        owner = args[-1]
        tp = int(np.count_nonzero(owner))
        return {'TP': tp, 'known_FP': 0, 'known_FN': 3 - tp,
                'known_arm_FP': 0, 'known_underlayer_FP': 0}

    # These are synthetic import targets for the runner's *deferred* imports.
    # No real stage code or human reference is executed in this test.
    replay_stage = types.ModuleType('local_l02_no_merge_signed_replay')
    replay_stage.REVIEW = 'missing_human_review.zip'
    replay_stage.verify_archives = lambda _: {'verified': 1}
    replay_stage.load_source_only = lambda *a: (rgba, classes, frozen, classes.copy())
    replay_stage.postscore = postscore
    replay_stage.components = lambda owner: {1: 1, 2: 0}
    composed_stage = types.ModuleType('local_l02_composed_dual_contact_shadow')
    composed_stage.propose_composed_dual_contact_shadow = first
    strict_stage = types.ModuleType('local_l02_enclosed_class32_shadow')
    strict_stage.propose_enclosed_class32_shadow = second

    for name, module in (
        ('local_l02_no_merge_signed_replay', replay_stage),
        ('local_l02_composed_dual_contact_shadow', composed_stage),
        ('local_l02_enclosed_class32_shadow', strict_stage),
    ):
        monkeypatch.setitem(sys.modules, name, module)

    monkeypatch.setattr(m, 'verify_pr_replay_lineage',
                        lambda: {'verified_dependency_blobs': 23})
    monkeypatch.setattr(m, 'PINNED_COMPOSED',
                        {'H08': hashlib.sha256(composed.tobytes()).hexdigest()})
    monkeypatch.setattr(m, 'PINNED_STRICT',
                        {'H08': hashlib.sha256(strict.tobytes()).hexdigest()})

    # Synthetic in-memory doubles intentionally bypass only the cache guard.
    monkeypatch.setattr(m, '_reject_cached_replay_stages', lambda: None)

    # The missing human ZIP must fail only after both proposals are SHA-pinned,
    # source-only conditions pass, and both postscores run.
    with pytest.raises(FileNotFoundError):
        m.replay(tmp_path, 'H08')
    assert events == ['compose', 'strict', 'postscore', 'postscore']
    assert list(tmp_path.iterdir()) == []

def test_preloaded_stage_rejected_before_private_archive_read(monkeypatch, tmp_path):
    # Exact disk SHA cannot prove that an already-imported module is current.
    monkeypatch.setattr(m, 'verify_pr_replay_lineage',
                        lambda: {'verified_dependency_blobs': 23})
    stale = types.ModuleType('local_l02_no_merge_signed_replay')
    monkeypatch.setitem(sys.modules, 'local_l02_no_merge_signed_replay', stale)
    with pytest.raises(ValueError, match='PRELOADED_REPLAY_STAGE_HOLD'):
        m.replay(tmp_path, 'H08')
    assert list(tmp_path.iterdir()) == []

