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
    PINNED_RUN30_4_TRIPLES, SourceOnlyAbstentionHold, _safe_to_remove,
    _enclosed_owner_voids,
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


def test_class32_abstention_cannot_create_four_neighbour_background_hole():
    # A 3x3 all-foreground patch except its lower-right corner has a
    # diagonal background neighbour. Removing its centre keeps owner
    # components unchanged but creates a NEW 4-connected background hole.
    owner_mask = np.ones((7, 7), dtype=bool)
    owner_mask[4, 4] = False
    assert _safe_to_remove(owner_mask, 3, 3) is False


def test_class32_abstention_allows_locally_simple_background_boundary():
    # Guard must not veto every safe boundary pixel; background remains
    # connected in both 4- and 8-neighbour definitions.
    owner_mask = np.ones((7, 7), dtype=bool)
    owner_mask[2:5, 5] = False
    assert _safe_to_remove(owner_mask, 3, 4) is True


def test_opt_in_seed_scale_guard_preserves_source_only_garment_neighborhood():
    # The radius is derived from the frozen garment seed, not review labels.
    # This is a conservative research veto, not proof of semantic quality.
    x = sample()
    original = x['frozen_owner'].copy()
    guarded, receipt = propose_class32_competitor_abstention(
        **x, protect_garment_seed_scale=True)
    assert receipt['seed_scale_guard_enabled'] is True
    assert receipt['seed_scale_px'] is not None
    assert receipt['seed_scale_px'] > 0
    assert receipt['seed_scale_guarded_owner_px'] > 0
    assert receipt['seed_scale_guard_preserved'] is True
    assert receipt['seed_scale_exposed_known_case_not_blind'] is True
    assert receipt['quality'] == 'UNASSESSED'
    assert receipt['Phase4'] == 'FAIL'
    assert np.array_equal(x['frozen_owner'], original)
    assert np.all((guarded == original) | ((original != 0) & (guarded == 0)))
    assert receipt['candidate_abstained_px'] == np.count_nonzero(guarded != original)


def test_seed_scale_guard_requires_explicit_boolean_opt_in():
    x = sample()
    with pytest.raises(SourceOnlyAbstentionHold, match='INVALID_SEED_SCALE_GUARD_MODE'):
        propose_class32_competitor_abstention(
            **x, protect_garment_seed_scale='yes')
    with pytest.raises(SourceOnlyAbstentionHold, match='INVALID_SEED_SCALE_GUARD_MODE'):
        propose_pinned_run30_4_shadow(
            case_id='H06', source_bytes=x['source_bytes'],
            class_ids=x['class_ids'], frozen_owner=x['frozen_owner'],
            protect_garment_seed_scale=1)


def test_seed_scale_guard_does_not_bypass_pinned_run30_provenance():
    x = sample()
    with pytest.raises(SourceOnlyAbstentionHold, match='RUN30_PROVENANCE_TRIPLE_MISMATCH'):
        propose_pinned_run30_4_shadow(
            case_id='H06', source_bytes=x['source_bytes'],
            class_ids=x['class_ids'], frozen_owner=x['frozen_owner'],
            protect_garment_seed_scale=True)


def test_full_image_void_counter_detects_opening_and_closed_hole():
    # A 4/8-owner component may remain intact while a new silhouette void
    # appears. Border-connected background is NOT an enclosed hole.
    owner = np.zeros((13, 13), dtype=bool)
    owner[2:11, 2:11] = True
    assert [_enclosed_owner_voids(owner, k) for k in (4, 8)] == [0, 0]
    owner[6, 6] = False
    assert [_enclosed_owner_voids(owner, k) for k in (4, 8)] == [1, 1]
    owner[2:7, 6] = False
    assert [_enclosed_owner_voids(owner, k) for k in (4, 8)] == [0, 0]


def test_whole_image_void_integrity_receipt_is_fail_closed():
    x = sample()
    result, receipt = propose_class32_competitor_abstention(**x)
    assert receipt['owner_enclosed_voids_preserved'] is True
    assert receipt['owner_enclosed_voids_4_8_before'] == receipt['owner_enclosed_voids_4_8_after']
    assert np.array_equal(x['frozen_owner'], sample()['frozen_owner'])
    assert receipt['quality'] == 'UNASSESSED'


def test_class32_island_anchor_survives_abstention():
    # Source-predicted class32 can disappear inside an otherwise connected
    # owner component without changing the owner component count.
    x = sample()
    before = x['frozen_owner'].copy()
    result, receipt = propose_class32_competitor_abstention(**x)
    assert receipt['class32_owner_islands4_before'] >= 1
    assert receipt['class32_island_anchors_preserved'] is True
    assert np.count_nonzero((x['class_ids'] == 32) & (result != 0)) >= 1
    assert np.array_equal(before, x['frozen_owner'])
    assert receipt['quality'] == 'UNASSESSED'
    assert receipt['Phase4'] == 'FAIL'


def test_touching_class32_islands_of_different_owners_have_separate_anchors():
    # Adjacent sleeve/arm predictions are one class32 connected component
    # if owner IDs are ignored. Each frozen owner needs its OWN anchor.
    x = sample()
    x['frozen_owner'][39:61, 38:50] = 1
    x['expected_frozen_owner_sha256'] = hashlib.sha256(
        x['frozen_owner'].tobytes(order='C')).hexdigest()
    result, receipt = propose_class32_competitor_abstention(**x)
    assert receipt['class32_owner_islands4_before'] >= 2
    assert receipt['class32_island_anchors_preserved'] is True
    for owner_id in (1, 2):
        assert np.count_nonzero((x['class_ids'] == 32) &
                                (x['frozen_owner'] == owner_id) &
                                (result == owner_id)) >= 1
    assert receipt['quality'] == 'UNASSESSED'
    assert receipt['Phase4'] == 'FAIL'


def test_class32_owner_island_connectivity_is_preserved():
    # A class32 sleeve can fragment while its owner stays connected through
    # neighbouring garment classes. Track the sleeve topology separately.
    x = sample()
    result, receipt = propose_class32_competitor_abstention(**x)
    assert receipt['class32_owner_island_connectivity_preserved'] is True
    assert (receipt['class32_owner_islands4_before'] ==
            receipt['class32_owner_islands4_after'])
    assert receipt['quality'] == 'UNASSESSED'
    assert receipt['Phase4'] == 'FAIL'


def test_class32_garment_seam_is_preserved_per_frozen_owner():
    # Class32 is adjacent to class10 garment. A sleeve can lose its seam
    # without changing the owner's total number of connected components.
    # This source-only structural veto is NOT semantic owner proof.
    x = sample()
    original = x['frozen_owner'].copy()
    result, receipt = propose_class32_competitor_abstention(**x)
    assert receipt['frozen_class32_garment_seam8_px'] > 0
    assert receipt['frozen_class32_garment_seam8_preserved'] is True
    assert np.array_equal(original, x['frozen_owner'])
    assert receipt['quality'] == 'UNASSESSED'
    assert receipt['Phase4'] == 'FAIL'


def test_garment_seam_guard_does_not_grant_wrong_owner_authority():
    x = sample()
    x['frozen_owner'][39:61, 38:50] = 1
    x['expected_frozen_owner_sha256'] = hashlib.sha256(
        x['frozen_owner'].tobytes(order='C')).hexdigest()
    result, receipt = propose_class32_competitor_abstention(**x)
    for owner_id in (1, 2):
        garment = ((x['class_ids'] == 5) | (x['class_ids'] == 10)) & (
            x['frozen_owner'] == owner_id)
        from scipy import ndimage as ndi
        adjacent = ndi.binary_dilation(garment, structure=np.ones((3, 3), bool))
        seam = (x['class_ids'] == 32) & (x['frozen_owner'] == owner_id) & adjacent
        assert np.array_equal(result[seam], x['frozen_owner'][seam])
    assert receipt['frozen_class32_garment_seam8_preserved'] is True
    assert receipt['quality'] == 'UNASSESSED'
