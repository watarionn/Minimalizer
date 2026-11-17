"""Source-free provenance and rejection tests; not a visual quality claim."""
import hashlib
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_sleeve_signed_source_adapter import (
    propose_signed_sleeve_contact_safe_shadow, SleeveSignedSourceHold,
)


def _sha(x):
    return hashlib.sha256(x).hexdigest()


def _scene():
    rgba = np.zeros((9, 15, 4), np.uint8)
    rgba[..., :3] = 150
    rgba[..., 3] = 255
    owner = np.zeros((9, 15), np.uint8)
    owner[4, 2] = 1
    cls = np.zeros_like(owner)
    cls[4, 2] = 5
    cls[4, 3:8] = 32
    anime = np.zeros_like(owner)
    anime[4, 3:8] = 10
    candidate = np.zeros_like(owner, bool)
    candidate[4, 2:8] = True
    buffer = io.BytesIO()
    Image.fromarray(rgba).save(buffer, format='PNG')
    encoded = buffer.getvalue()
    return dict(encoded_source=encoded, source_rgba=rgba, class_ids=cls,
        anime_classes=anime, frozen_candidate=candidate, frozen_owner=owner,
        expected_encoded_source_sha256=_sha(encoded),
        expected_rgba_sha256=_sha(rgba.tobytes()),
        expected_class_ids_sha256=_sha(cls.tobytes()),
        expected_anime_classes_sha256=_sha(anime.tobytes()),
        expected_candidate_sha256=_sha(candidate.tobytes()),
        expected_frozen_owner_sha256=_sha(owner.tobytes()))


def test_valid_signed_shadow_does_not_promote_quality():
    x = _scene()
    out, receipt = propose_signed_sleeve_contact_safe_shadow(**x)
    assert receipt['proposal_owner_sha256'] == _sha(out.tobytes())
    assert receipt['Phase4'] == 'FAIL' and receipt['L02'] == 'HOLD'
    assert receipt['supplied_class_anime_candidate_owner_digests_matched']
    assert receipt['external_pin_provenance_verified'] is False
    assert np.all(out[x['frozen_owner'] > 0] == x['frozen_owner'][x['frozen_owner'] > 0])


@pytest.mark.parametrize('key', ['expected_encoded_source_sha256', 'expected_rgba_sha256',
    'expected_class_ids_sha256', 'expected_anime_classes_sha256',
    'expected_candidate_sha256', 'expected_frozen_owner_sha256'])
def test_bad_external_pin_fails_closed(key):
    x = _scene()
    x[key] = '0' * 64
    with pytest.raises(SleeveSignedSourceHold):
        propose_signed_sleeve_contact_safe_shadow(**x)


def test_decoded_rgba_mismatch_even_with_matching_supplied_hash():
    x = _scene()
    x['source_rgba'][1, 1, 0] ^= 1
    x['expected_rgba_sha256'] = _sha(x['source_rgba'].tobytes())
    with pytest.raises(SleeveSignedSourceHold, match='SOURCE_DECODE_BYTES_MISMATCH'):
        propose_signed_sleeve_contact_safe_shadow(**x)


def test_candidate_must_preserve_frozen_owner():
    x = _scene()
    x['frozen_candidate'][4, 2] = False
    x['expected_candidate_sha256'] = _sha(x['frozen_candidate'].tobytes())
    with pytest.raises(SleeveSignedSourceHold, match='CANDIDATE_EXCLUDES_FROZEN_OWNER'):
        propose_signed_sleeve_contact_safe_shadow(**x)
