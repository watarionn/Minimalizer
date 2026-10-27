"""Source-free adversarial tests for a dormant research output contract."""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_signed_shadow_output_gate import (
    SignedShadowOutputHold, verify_signed_shadow_output,
)


def sample():
    rgba = np.full((40, 40, 4), 120, dtype=np.uint8)
    rgba[..., 3] = 255
    cls = np.full((40, 40), 32, dtype=np.uint8)
    owner = np.zeros((40, 40), dtype=np.uint8)
    owner[5:10, 5:10] = 1
    owner[30:35, 30:35] = 2
    return dict(source_rgba=rgba, class_ids=cls, before=owner,
                after=owner.copy(), receipt={'new_source_pixels': 0})


def test_noop_preserves_hold():
    kw = sample()
    audit = verify_signed_shadow_output(**kw)
    assert audit['new_source_pixels_verified'] == 0
    assert audit['Phase4'] == 'FAIL'


def test_valid_source_class32_extension():
    kw = sample()
    kw['after'][10, 6] = 1
    kw['receipt']['new_source_pixels'] = 1
    assert verify_signed_shadow_output(**kw)['new_source_pixels_verified'] == 1


def test_frozen_owner_erasure_rejected():
    kw = sample()
    kw['after'][5, 5] = 0
    with pytest.raises(SignedShadowOutputHold, match='FROZEN_OWNER_MODIFIED'):
        verify_signed_shadow_output(**kw)


def test_nonopaque_or_other_class_rejected():
    for change in ('alpha', 'class'):
        kw = sample()
        kw['after'][10, 6] = 1
        kw['receipt']['new_source_pixels'] = 1
        if change == 'alpha':
            kw['source_rgba'][10, 6, 3] = 128
        else:
            kw['class_ids'][10, 6] = 18
        with pytest.raises(SignedShadowOutputHold, match='UNSUPPORTED_OR_NONOPAQUE_ADDITION'):
            verify_signed_shadow_output(**kw)


def test_untrusted_receipt_count_rejected():
    kw = sample()
    kw['after'][10, 6] = 1
    with pytest.raises(SignedShadowOutputHold, match='SHADOW_RECEIPT_PIXEL_COUNT_MISMATCH'):
        verify_signed_shadow_output(**kw)


def test_new_owner_contact_rejected():
    kw = sample()
    kw['before'][15:20, 15:20] = 1
    kw['before'][15:20, 22:27] = 2
    kw['after'] = kw['before'].copy()
    kw['after'][17, 20:22] = 1
    kw['receipt']['new_source_pixels'] = 2
    with pytest.raises(SignedShadowOutputHold, match='NEW_CROSS_OWNER_CONTACT'):
        verify_signed_shadow_output(**kw)


def test_frozen_component_merge_rejected():
    kw = sample()
    kw['before'][5:10, 17:22] = 1
    kw['after'] = kw['before'].copy()
    kw['after'][7, 10:17] = 1
    kw['receipt']['new_source_pixels'] = 7
    with pytest.raises(SignedShadowOutputHold, match='FROZEN_COMPONENT_COUNT_CHANGED'):
        verify_signed_shadow_output(**kw)


def test_disconnected_island_rejected():
    kw = sample()
    kw['after'][20, 20] = 1
    kw['receipt']['new_source_pixels'] = 1
    with pytest.raises(SignedShadowOutputHold, match='FROZEN_COMPONENT_COUNT_CHANGED'):
        verify_signed_shadow_output(**kw)
