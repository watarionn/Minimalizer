"""Offline checkpoint-acquisition guards; not signed-image quality tests."""
import hashlib
import io
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
import local_l02_atr_checkpoint_fetch_research as fetch


def _fixture(monkeypatch):
    data = b'public-pinned-model-sample'
    monkeypatch.setattr(fetch, 'SIZE', len(data))
    monkeypatch.setattr(fetch, 'SHA256', hashlib.sha256(data).hexdigest())
    return data


def test_success_and_offline_readback(monkeypatch, tmp_path):
    data = _fixture(monkeypatch)
    calls = []

    def fake_urlopen(url, timeout):
        calls.append((url, timeout))
        return io.BytesIO(data)

    monkeypatch.setattr(fetch, 'urlopen', fake_urlopen)
    result = fetch.fetch_pinned_atr_checkpoint(tmp_path)
    assert result.read_bytes() == data
    assert fetch.fetch_pinned_atr_checkpoint(tmp_path) == result
    assert len(calls) == 1


def test_bad_hash_fails_without_model_or_partial_file(monkeypatch, tmp_path):
    _fixture(monkeypatch)
    monkeypatch.setattr(fetch, 'urlopen', lambda *a, **kw: io.BytesIO(b'bad' * 20))
    with pytest.raises(fetch.CheckpointHold):
        fetch.fetch_pinned_atr_checkpoint(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_existing_mismatch_not_overwritten(monkeypatch, tmp_path):
    _fixture(monkeypatch)
    target = tmp_path / fetch.FILENAME
    target.write_bytes(b'bad')
    monkeypatch.setattr(fetch, 'urlopen', lambda *a, **kw: pytest.fail('network not allowed'))
    with pytest.raises(fetch.CheckpointHold, match='EXISTING_CHECKPOINT_MISMATCH'):
        fetch.fetch_pinned_atr_checkpoint(tmp_path)
    assert target.read_bytes() == b'bad'


def test_git_worktree_rejected(monkeypatch, tmp_path):
    _fixture(monkeypatch)
    (tmp_path / '.git').write_text('gitdir: /elsewhere')
    with pytest.raises(fetch.CheckpointHold, match='OUTSIDE_GIT'):
        fetch.fetch_pinned_atr_checkpoint(tmp_path)
