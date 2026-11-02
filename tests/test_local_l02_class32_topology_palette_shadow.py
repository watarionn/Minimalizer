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
    propose_class32_competitor_abstention, propose_pinned_run30_4_shadow,
    PINNED_RUN30_4_TRIPLES, SourceOnlyAbstentionHold,
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
                class_ids=cls, frozen_owner=owner,
                expected_class_ids_sha256=hashlib.sha256(cls.tobytes(order='C')).hexdigest(),
                expected_frozen_owner_sha256=hashlib.sha256(owner.tobytes(order='C')).hexdigest())


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
    assert receipt['owner_8_components_before'] == receipt['owner_8_components_after']
    assert receipt['class_ids_sha_verified'] and receipt['frozen_owner_sha_verified']
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
    x['expected_class_ids_sha256'] = hashlib.sha256(x['class_ids'].tobytes(order='C')).hexdigest()
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


def test_one_pixel_terminal_branch_not_eroded_by_component_count_only():
    # A source-supported thin branch can disappear one endpoint at a time
    # without changing the number of 4-connected owner components.
    x = sample()
    x['frozen_owner'][20, 8:12] = 2
    x['class_ids'][20, 8:12] = 32
    x['expected_class_ids_sha256'] = hashlib.sha256(x['class_ids'].tobytes(order='C')).hexdigest()
    x['expected_frozen_owner_sha256'] = hashlib.sha256(x['frozen_owner'].tobytes(order='C')).hexdigest()
    original = x['frozen_owner'].copy()
    new, receipt = propose_class32_competitor_abstention(**x)
    assert np.array_equal(new[20, 8:12], original[20, 8:12])
    assert receipt['owner_4_components_before'] == receipt['owner_4_components_after']
    assert receipt['quality'] == 'UNASSESSED'


def test_changed_frozen_class_prediction_rejected_before_proposal():
    x = sample()
    x['class_ids'][40, 40] = 5
    with pytest.raises(SourceOnlyAbstentionHold, match='CLASS_IDS_SHA_MISMATCH'):
        propose_class32_competitor_abstention(**x)


def test_changed_frozen_owner_rejected_before_proposal():
    x = sample()
    x['frozen_owner'][40, 40] = 0
    with pytest.raises(SourceOnlyAbstentionHold, match='FROZEN_OWNER_SHA_MISMATCH'):
        propose_class32_competitor_abstention(**x)


def test_preserves_frozen_arm_sleeve_contact_not_just_component_counts():
    # A frozen arm (owner1) touches a class32 sleeve (owner2) at x37/38.
    # Removing the sleeve boundary would disconnect their contact while
    # both owner component counts could remain unchanged.
    x = sample()
    x['frozen_owner'][38:62, 37] = 1
    x['expected_frozen_owner_sha256'] = hashlib.sha256(
        x['frozen_owner'].tobytes(order='C')).hexdigest()
    original = x['frozen_owner'].copy()
    new, receipt = propose_class32_competitor_abstention(**x)
    assert np.array_equal(new[39:61, 37:39], original[39:61, 37:39])
    assert receipt['frozen_cross_owner_contact8_px'] > 0
    assert receipt['frozen_cross_owner_contact8_preserved'] is True
    assert receipt['owner_4_components_before'] == receipt['owner_4_components_after']
    assert receipt['owner_8_components_before'] == receipt['owner_8_components_after']
    assert receipt['quality'] == 'UNASSESSED'


def test_run30_pinned_replay_rejects_unlisted_case_without_fallback():
    x = sample()
    with pytest.raises(SourceOnlyAbstentionHold, match='UNPINNED_RUN30_CASE'):
        propose_pinned_run30_4_shadow(case_id='H99', source_bytes=x['source_bytes'],
                                      class_ids=x['class_ids'], frozen_owner=x['frozen_owner'])


def test_run30_pinned_replay_rejects_self_signed_synthetic_or_cross_run_mix():
    # Self-calculated hashes pass the generic research helper, but cannot
    # authenticate a frozen source/class/owner provenance triple.
    x = sample()
    generic, receipt = propose_class32_competitor_abstention(**x)
    assert generic.shape == x['class_ids'].shape
    assert receipt['source_sha_verified'] and receipt['class_ids_sha_verified']
    with pytest.raises(SourceOnlyAbstentionHold, match='RUN30_PROVENANCE_TRIPLE_MISMATCH'):
        propose_pinned_run30_4_shadow(case_id='H06', source_bytes=x['source_bytes'],
                                      class_ids=x['class_ids'], frozen_owner=x['frozen_owner'])


def test_run30_known_case_pins_are_distinct_and_exact_sha256_only():
    assert set(PINNED_RUN30_4_TRIPLES) == {'H04', 'H06', 'H08'}
    assert len(set(PINNED_RUN30_4_TRIPLES.values())) == 3
    for triple in PINNED_RUN30_4_TRIPLES.values():
        assert len(triple) == 3
        assert all(len(v) == 64 and set(v) <= set('0123456789abcdef') for v in triple)
