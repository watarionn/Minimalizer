"""Source-free lineage and postscore ordering guards for the staged strict replay.

These checks do not assert semantic owner quality or unknown-character PASS.
"""
import hashlib
import numpy as np
import pytest
from tools.research import local_l02_canonical_strict_signed_replay as m


def test_guarded_wrapper_source_pin_is_exact_and_distinct_from_stale_h08():
    actual = hashlib.sha256((m.Path(m.__file__).parent / 'local_l02_composed_dual_contact_shadow.py').read_bytes()).hexdigest()
    assert actual == m.PINNED_GUARDED_WRAPPER_SHA256
    assert m.PINNED_COMPOSED['H08'] == '3e46769428946d54f0cc441ead77699a81839cd8e372ca39212e5b7825ee4a1a'
    assert m.PINNED_STRICT['H08'] == '32bb5266a479ce64571f190ffebe90b50c01329598408019b363c5ab0c9f0778'
    assert m.PINNED_COMPOSED['H08'] != '82313762a406ec225cf4a79675772c9bc71fefa77d6d48e6613b48cebf884552'


def test_wrapper_drift_fails_before_private_archive_read(monkeypatch, tmp_path):
    monkeypatch.setattr(m, 'PINNED_GUARDED_WRAPPER_SHA256', '0' * 64)
    def no_read(*a, **k):
        raise AssertionError('PRIVATE_READ_BEFORE_SOURCE_PIN')
    monkeypatch.setattr(m, 'verify_archives', no_read)
    with pytest.raises(ValueError, match='GUARDED_STAGING_WRAPPER_SHA_MISMATCH'):
        m.replay(tmp_path, 'H08')


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
    monkeypatch.setattr(m, 'verify_archives', lambda _: {'verified': 1})
    monkeypatch.setattr(m, 'load_source_only', lambda *a: (rgba, classes, frozen, classes.copy()))
    def first(**kwargs):
        events.append('compose')
        return composed.copy(), {'schema': 'compose'}
    def second(**kwargs):
        events.append('strict')
        return strict.copy(), {'schema': 'strict'}
    monkeypatch.setattr(m, 'propose_composed_dual_contact_shadow', first)
    monkeypatch.setattr(m, 'propose_enclosed_class32_shadow', second)
    monkeypatch.setattr(m, 'PINNED_COMPOSED', {'H08': hashlib.sha256(composed.tobytes()).hexdigest()})
    monkeypatch.setattr(m, 'PINNED_STRICT', {'H08': hashlib.sha256(strict.tobytes()).hexdigest()})
    def postscore(*args):
        events.append('postscore')
        assert events[:2] == ['compose', 'strict']
        owner = args[-1]
        tp = int(np.count_nonzero(owner))
        return {'TP': tp, 'known_FP': 0, 'known_FN': 3 - tp,
                'known_arm_FP': 0, 'known_underlayer_FP': 0}
    monkeypatch.setattr(m, 'postscore', postscore)
    # The private human masks are intentionally absent: it must fail closed
    # *after* both pinned proposals and postscore, never before the freeze.
    with pytest.raises(FileNotFoundError):
        m.replay(tmp_path, 'H08')
    assert events == ['compose', 'strict', 'postscore', 'postscore']
