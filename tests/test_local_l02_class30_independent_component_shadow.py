"""Source-free regression for class30 support inheritance in mixed sleeve islands."""
import numpy as np
from local_l02_contact_density_partition_shadow import (
    _abstain_unsupported_class30_subcomponents,
)


def _fixture():
    cls = np.full((64, 64), 32, dtype=np.uint8)
    anime = np.full((64, 64), 10, dtype=np.uint8)
    eligible = np.zeros((64, 64), dtype=bool)
    eligible[10:50, 10:30] = True
    eligible[10:50, 30:40] = True
    cls[10:50, 30:40] = 30
    anime[10:50, 30:40] = 0
    return eligible, cls, anime


def test_class32_support_cannot_be_inherited_by_class30():
    eligible, cls, anime = _fixture()
    out, withheld, components = _abstain_unsupported_class30_subcomponents(
        eligible, cls, anime)
    assert withheld == 400 and components == 1
    assert np.count_nonzero(out) == 800
    assert not np.any(out[10:50, 30:40])


def test_class30_with_own_observer_support_kept():
    eligible, cls, anime = _fixture()
    anime[10:50, 30] = 10  # 40 independent class30 pixels, above existing 32
    out, withheld, components = _abstain_unsupported_class30_subcomponents(
        eligible, cls, anime)
    assert withheld == 0 and components == 0
    assert np.array_equal(out, eligible)


def test_class32_only_policy_unchanged():
    eligible, cls, anime = _fixture()
    cls[10:50, 30:40] = 32
    out, withheld, components = _abstain_unsupported_class30_subcomponents(
        eligible, cls, anime)
    assert withheld == 0 and components == 0
    assert np.array_equal(out, eligible)


def test_no_class30_pixels_or_review_annotations_needed():
    eligible = np.zeros((16, 16), dtype=bool)
    cls = np.zeros((16, 16), dtype=np.uint8)
    anime = np.zeros((16, 16), dtype=np.uint8)
    out, withheld, components = _abstain_unsupported_class30_subcomponents(
        eligible, cls, anime)
    assert not np.any(out)
    assert (withheld, components) == (0, 0)
