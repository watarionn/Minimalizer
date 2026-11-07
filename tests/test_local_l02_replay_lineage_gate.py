"""Source-free negative controls for exact-PR replay dependency provenance."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_replay_lineage_gate import (
    ReplayLineageHold, _git_blob_sha, _verify_lineage, verify_pr_replay_lineage,
    PR_445_REPLAY_BLOBS,
)


def test_two_exact_source_blobs_pass_but_never_approve_quality(tmp_path):
    (tmp_path / 'local_l02_a.py').write_text('value = 1\n')
    (tmp_path / 'local_l02_b.py').write_text('value = 2\n')
    pins = {n: _git_blob_sha((tmp_path / (n + '.py')).read_bytes())
            for n in ('local_l02_a', 'local_l02_b')}
    result = _verify_lineage(tmp_path, pins)
    assert result['verified_dependency_blobs'] == 2
    assert result['Phase4'] == 'FAIL' and result['L02'] == 'HOLD'
    assert result['provenance_scope'] == 'PR_445_ONLY_NOT_MAIN'


def test_changed_source_rejected(tmp_path):
    f = tmp_path / 'local_l02_a.py'
    f.write_text('value = 1\n')
    pins = {'local_l02_a': _git_blob_sha(f.read_bytes())}
    f.write_text('value = 2\n')
    with pytest.raises(ReplayLineageHold, match='PR_L02_DEPENDENCY_BLOB_MISMATCH'):
        _verify_lineage(tmp_path, pins)


def test_missing_source_rejected(tmp_path):
    with pytest.raises(ReplayLineageHold, match='MISSING_OR_UNSAFE_DEPENDENCY'):
        _verify_lineage(tmp_path, {'local_l02_a': '0' * 40})


def test_symlink_source_rejected(tmp_path):
    target = tmp_path / 'external.py'
    target.write_text('x=1\n')
    (tmp_path / 'local_l02_a.py').symlink_to(target)
    with pytest.raises(ReplayLineageHold, match='MISSING_OR_UNSAFE_DEPENDENCY'):
        _verify_lineage(tmp_path, {'local_l02_a': _git_blob_sha(target.read_bytes())})


@pytest.mark.parametrize('pins', [{}, {'../local_l02_a': '0' * 40},
                                  {'local_l02_a': 'X' * 40},
                                  {'local_l02_a': '0' * 39}])
def test_malformed_external_pin_rejected(tmp_path, pins):
    with pytest.raises(ReplayLineageHold, match='INVALID_EXTERNAL_BLOB_PINS'):
        _verify_lineage(tmp_path, pins)


def test_real_staging_archive_detects_two_stale_dependencies():
    # Only run in an isolated checkout with the archived 2026-10-23 staging
    # tree. In an exact PR checkout the default pins should all pass.
    here = Path(__file__).resolve().parents[1] / 'tools' / 'research'
    stale = here / 'local_l02_cross_owner_contact_gate.py'
    if not stale.exists():
        pytest.skip('no staging tree')
    if _git_blob_sha(stale.read_bytes()) == '8c17798afbd92814f2e592adbdaf53ecfab30d7a':
        with pytest.raises(ReplayLineageHold, match='PR_L02_DEPENDENCY_BLOB_MISMATCH'):
            verify_pr_replay_lineage()


def test_unpinned_local_import_rejected_before_private_read(tmp_path):
    source = tmp_path / 'local_l02_a.py'
    source.write_text('from local_l02_hidden import sentinel\\n'.replace('\\n', '\n'))
    pins = {'local_l02_a': _git_blob_sha(source.read_bytes())}
    with pytest.raises(ReplayLineageHold, match='UNPINNED_LOCAL_REPLAY_IMPORT'):
        _verify_lineage(tmp_path, pins)


def test_unpinned_plain_import_rejected(tmp_path):
    source = tmp_path / 'local_l02_a.py'
    source.write_text('import local_l02_hidden\\n'.replace('\\n', '\n'))
    pins = {'local_l02_a': _git_blob_sha(source.read_bytes())}
    with pytest.raises(ReplayLineageHold, match='UNPINNED_LOCAL_REPLAY_IMPORT'):
        _verify_lineage(tmp_path, pins)


def test_pinned_transitive_import_allowed(tmp_path):
    (tmp_path / 'local_l02_a.py').write_text('from local_l02_b import value\\n'.replace('\\n', '\n'))
    (tmp_path / 'local_l02_b.py').write_text('value = 1\\n'.replace('\\n', '\n'))
    pins = {n: _git_blob_sha((tmp_path / (n + '.py')).read_bytes())
            for n in ('local_l02_a', 'local_l02_b')}
    assert _verify_lineage(tmp_path, pins)['verified_dependency_blobs'] == 2


def test_exact_pr_pins_include_frozen_owner_transition_audit():
    assert PR_445_REPLAY_BLOBS['local_l02_frozen_owner_transition_audit'] == (
        'b284d5699424284d7b9d72cf62be8e7ff2306a5c')


def test_invalid_source_syntax_rejected(tmp_path):
    source = tmp_path / 'local_l02_a.py'
    source.write_text('from local_l02_b import\\n'.replace('\\n', '\n'))
    pins = {'local_l02_a': _git_blob_sha(source.read_bytes())}
    with pytest.raises(ReplayLineageHold, match='INVALID_PINNED_SOURCE_SYNTAX'):
        _verify_lineage(tmp_path, pins)
