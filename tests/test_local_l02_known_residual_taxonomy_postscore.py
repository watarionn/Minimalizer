"""Source-free negative contracts for postscore-only residual class accounting."""
import numpy as np
import pytest
from local_l02_known_residual_taxonomy_postscore import (
    audit_known_residual_taxonomy, ResidualTaxonomyHold,
)


def fixture():
    alpha = np.full((3, 5), 255, dtype=np.uint8)
    cls = np.array([[32, 0, 2, 7, 30], [32, 32, 25, 10, 5], [0, 0, 0, 0, 0]], dtype=np.uint8)
    owner = np.zeros((3, 5), dtype=np.uint8)
    owner[1, 3] = 2
    owner[1, 4] = 1
    owner[2, 0] = 2  # unknown owner, never a known false positive
    positive = np.zeros((3, 5), dtype=np.uint8)
    positive[0, :] = 1
    positive[1, 0] = 1
    known = positive.copy()
    known[1, 3] = 1  # known negative owner
    return dict(source_alpha=alpha, class_ids=cls, frozen_owner=owner,
                reviewed_outerwear=positive, reviewed_known=known)


def test_residual_bound_and_unknown_accounting():
    data = fixture()
    originals = {k: v.copy() for k, v in data.items()}
    r = audit_known_residual_taxonomy(**data)
    assert r['known_outerwear_fn'] == 6
    assert r['class32_only_max_possible_recovery'] == 2
    assert r['known_fn_remaining_even_if_all_class32_recovered'] == 4
    assert r['known_fn_in_classes_0_2_7_requiring_independent_review'] == 3
    assert r['known_false_owner_fp'] == 1
    assert r['unknown_assigned_not_counted_as_fp'] == 2
    assert r['missing_by_frozen_class'] == {'0': 1, '2': 1, '7': 1, '30': 1, '32': 2}
    assert (r['L02'], r['Phase4'], r['L03']) == ('HOLD', 'FAIL', 'NO_GO')
    for k, value in data.items():
        assert np.array_equal(value, originals[k])


@pytest.mark.parametrize('field, replacement, reason', [
    ('source_alpha', np.zeros((0, 0), dtype=np.uint8), 'INVALID_FROZEN_POSTSCORE_INPUT'),
    ('class_ids', np.zeros((2, 5), dtype=np.uint8), 'INVALID_FROZEN_POSTSCORE_INPUT'),
    ('reviewed_outerwear', np.full((3, 5), 2, dtype=np.uint8), 'INVALID_LABEL_DOMAIN'),
    ('frozen_owner', np.full((3, 5), 3, dtype=np.uint8), 'INVALID_LABEL_DOMAIN'),
])
def test_invalid_contract(field, replacement, reason):
    d = fixture();d[field] = replacement
    with pytest.raises(ResidualTaxonomyHold, match=reason):
        audit_known_residual_taxonomy(**d)


def test_reviewed_positive_outside_alpha_rejected():
    d=fixture();d['source_alpha'][0,0]=0
    with pytest.raises(ResidualTaxonomyHold, match='INVALID_SOURCE_OR_REVIEW_PROVENANCE'):
        audit_known_residual_taxonomy(**d)


def test_positive_not_known_rejected():
    d=fixture();d['reviewed_known'][0,0]=0
    with pytest.raises(ResidualTaxonomyHold, match='INVALID_SOURCE_OR_REVIEW_PROVENANCE'):
        audit_known_residual_taxonomy(**d)


def test_unreviewed_owner_is_not_known_false_positive():
    d=fixture();d['frozen_owner'][2,1]=2
    r=audit_known_residual_taxonomy(**d)
    assert r['known_false_owner_fp']==1
    assert r['unknown_assigned_not_counted_as_fp']==3
