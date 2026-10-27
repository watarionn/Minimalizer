"""Source-free exact-stage runner contract; no signed images or labels."""
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_dual_owner_signed_replay import run_pinned_replay, SignedReplayHold


def fixture(tmp_path):
    rgba = np.zeros((64, 64, 4), dtype=np.uint8)
    rgba[..., :3] = (120, 80, 130)
    rgba[..., 3] = 255
    classes = np.full((64, 64), 32, dtype=np.uint8)
    owner = np.zeros((64, 64), dtype=np.uint8)
    owner[15:30, 8:18] = 1
    owner[15:30, 48:58] = 2
    buffer = io.BytesIO()
    Image.fromarray(rgba).save(buffer, format='PNG')
    raw = buffer.getvalue()
    source = tmp_path / 'source.png'
    source.write_bytes(raw)
    class_npz = tmp_path / 'class.npz'
    owner_npz = tmp_path / 'owner.npz'
    np.savez_compressed(class_npz, classids=classes)
    np.savez_compressed(owner_npz, owner=owner)
    digest = lambda b: hashlib.sha256(b).hexdigest()
    manifest = dict(
        schema='minimalizer/local-l02/signed-run30-replay-pin/v1',
        case='H08', stage='RUN30_HISTORICAL',
        encoded_source_sha256=digest(raw),
        decoded_rgba_sha256=digest(rgba.tobytes(order='C')),
        class_ids_sha256=digest(classes.tobytes(order='C')),
        composed_owner_sha256=digest(owner.tobytes(order='C')),
    )
    manifest_path = tmp_path / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, sort_keys=True))
    kwargs = dict(source_path=source, class_npz_path=class_npz,
                  owner_npz_path=owner_npz, manifest_path=manifest_path,
                  expected_manifest_sha256=digest(manifest_path.read_bytes()))
    return kwargs, manifest


def test_real_adapter_path_stays_research_only(tmp_path):
    kw, _ = fixture(tmp_path)
    receipt = run_pinned_replay(**kw)
    assert receipt['signed_source_encoded_and_decoded_verified']
    assert receipt['frozen_owner_transition_audit']['frozen_owner_pixels_modified'] == 0
    assert receipt['Phase4'] == 'FAIL' and receipt['production'] == 'NO_GO'
    assert receipt['new_unseen_signed_blind'] == 'PENDING'
    assert 'new_source_pixels_unscored' in receipt
    assert not (tmp_path / 'candidate.npz').exists()


def test_wrong_external_manifest_pin_rejected_before_source(tmp_path):
    kw, _ = fixture(tmp_path)
    kw['expected_manifest_sha256'] = '0' * 64
    kw['source_path'].unlink()
    with pytest.raises(SignedReplayHold, match='MANIFEST_SHA256_MISMATCH'):
        run_pinned_replay(**kw)


def test_wrong_stage_rejected_before_source(tmp_path):
    kw, manifest = fixture(tmp_path)
    manifest['stage'] = 'CURRENT_MAIN'
    kw['manifest_path'].write_text(json.dumps(manifest, sort_keys=True))
    kw['expected_manifest_sha256'] = hashlib.sha256(kw['manifest_path'].read_bytes()).hexdigest()
    kw['source_path'].unlink()
    with pytest.raises(SignedReplayHold, match='UNSUPPORTED_OR_INCOMPLETE_REPLAY_STAGE'):
        run_pinned_replay(**kw)


def test_wrong_signed_owner_rejected(tmp_path):
    kw, _ = fixture(tmp_path)
    with np.load(kw['owner_npz_path']) as z:
        owner = z['owner'].copy()
    owner[0, 0] = 1
    np.savez_compressed(kw['owner_npz_path'], owner=owner)
    with pytest.raises(SignedReplayHold, match='SIGNED_ADAPTER_HOLD:FROZEN_OWNER_SHA_MISMATCH'):
        run_pinned_replay(**kw)


def test_wrong_signed_class_rejected(tmp_path):
    kw, _ = fixture(tmp_path)
    with np.load(kw['class_npz_path']) as z:
        classes = z['classids'].copy()
    classes[0, 0] = 1
    np.savez_compressed(kw['class_npz_path'], classids=classes)
    with pytest.raises(SignedReplayHold, match='SIGNED_ADAPTER_HOLD:INDEPENDENT_CLASS_SHA_MISMATCH'):
        run_pinned_replay(**kw)


def test_corrupt_npz_fails_closed_without_private_traceback(tmp_path):
    kw, _ = fixture(tmp_path)
    kw['class_npz_path'].write_bytes(b'not a zip archive')
    with pytest.raises(SignedReplayHold, match='INVALID_PINNED_NPZ'):
        run_pinned_replay(**kw)
