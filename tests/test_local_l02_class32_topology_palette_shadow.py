"""Source-free negative tests. No signed-character quality acceptance."""
import hashlib
import io
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_class32_topology_palette_shadow import (
    propose_class32_competitor_abstention, SourceOnlyAbstentionHold,
)


def sample():
    rgba = np.zeros((72, 72, 4), dtype=np.uint8)
    rgba[5:67, 5:67] = [190, 147, 89, 255]
    rgba[8:37, 8:37, :3] = [240, 240, 238]
    rgba[38:62, 38:62, :3] = [240, 240, 238]
    cls = np.zeros((72, 72), np.uint8)
    cls[5:67, 5:67] = 10
    cls[8:37, 8:37] = 2
    cls[38:62, 38:62] = 32
    owner = np.zeros((72, 72), np.uint8)
    owner[5:67, 5:67] = 2
    owner[8:37, 8:37] = 0
    stream = io.BytesIO()
    Image.fromarray(rgba).save(stream, format='PNG')
    raw = stream.getvalue()
    return dict(source_bytes=raw, expected_source_sha256=hashlib.sha256(raw).hexdigest(),
                class_ids=cls, frozen_owner=owner)


def test_shadow_only_and_original_immutable():
    x = sample()
    original = x['frozen_owner'].copy()
    new, receipt = propose_class32_competitor_abstention(**x)
    assert np.array_equal(x['frozen_owner'], original)
    assert receipt['uses_human_labels'] is False
    assert receipt['class2_is_ground_truth_negative'] is False
    assert receipt['candidate_only'] is True
    assert receipt['Phase4'] == 'FAIL' and receipt['production'] == 'NO_GO'
    assert np.all((new == original) | ((original == 2) & (new == 0) & (x['class_ids'] == 32)))
    assert receipt['owner_4_components_before'] == receipt['owner_4_components_after']
    assert receipt['candidate_abstained_px'] == np.count_nonzero(new != original)


def test_wrong_signed_sha_rejected():
    x = sample(); x['expected_source_sha256'] = '0' * 64
    with pytest.raises(SourceOnlyAbstentionHold, match='SIGNED_SOURCE_SHA_MISMATCH'):
        propose_class32_competitor_abstention(**x)


def test_invalid_owner_outside_source_rejected():
    x = sample(); x['frozen_owner'][0, 0] = 2
    with pytest.raises(SourceOnlyAbstentionHold, match='OWNER_OUTSIDE_SIGNED_ALPHA'):
        propose_class32_competitor_abstention(**x)


def test_invalid_taxonomy_rejected():
    x = sample(); x['class_ids'][5, 5] = 47
    with pytest.raises(SourceOnlyAbstentionHold, match='INVALID_FROZEN_TAXONOMY'):
        propose_class32_competitor_abstention(**x)


def test_no_seed_abstains_without_changing_owner():
    x = sample(); x['class_ids'][x['class_ids'] == 2] = 0
    new, receipt = propose_class32_competitor_abstention(**x)
    assert receipt['reason'] == 'INSUFFICIENT_SOURCE_ONLY_SEEDS'
    assert np.array_equal(new, x['frozen_owner'])


def test_source_shape_mismatch_rejected():
    x = sample(); x['class_ids'] = x['class_ids'][:-1]
    with pytest.raises(SourceOnlyAbstentionHold, match='INVALID_FROZEN_PREDICTIONS'):
        propose_class32_competitor_abstention(**x)


def test_replay_deterministic():
    x = sample()
    a, ar = propose_class32_competitor_abstention(**x)
    b, br = propose_class32_competitor_abstention(**x)
    assert np.array_equal(a, b) and ar == br
