"""Source-free provenance tests; no signed source, labels or model weights."""
import hashlib
import io
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
import local_l02_dual_owner_signed_input_adapter as adapter


def fixture():
    rgba = np.zeros((32, 32, 4), dtype=np.uint8)
    rgba[..., :3] = (120, 80, 130)
    rgba[..., 3] = 255
    classes = np.full((32, 32), 32, np.uint8)
    owner = np.zeros((32, 32), np.uint8)
    owner[8:16, 3:9] = 1
    owner[8:16, 23:29] = 2
    buf = io.BytesIO()
    Image.fromarray(rgba, 'RGBA').save(buf, format='PNG')
    raw = buf.getvalue()
    dig = lambda b: hashlib.sha256(b).hexdigest()
    kw = dict(encoded_source=raw, source_rgba=rgba, class_ids=classes,
              composed_owner=owner, expected_encoded_source_sha256=dig(raw),
              expected_decoded_rgba_sha256=dig(rgba.tobytes()),
              expected_class_ids_sha256=dig(classes.tobytes()),
              expected_composed_owner_sha256=dig(owner.tobytes()))
    return kw


def test_authentic_inputs_reach_research_shadow(monkeypatch):
    kw = fixture()
    seen = []
    def shadow(**inputs):
        seen.append(inputs)
        return inputs['composed_owner'].copy(), {'schema': 'research-only', 'new_source_pixels': 0}
    monkeypatch.setattr(adapter, 'propose_dual_owner_lab_reach_shadow', shadow)
    proposed, receipt = adapter.propose_signed_dual_owner_lab_reach_shadow(**kw)
    assert len(seen) == 1
    assert np.array_equal(proposed, kw['composed_owner'])
    assert receipt['signed_source_encoded_and_decoded_verified']
    assert receipt['independent_class_bytes_verified']
    assert receipt['Phase4'] == 'FAIL' and receipt['production'] == 'NO_GO'


@pytest.mark.parametrize('field,reason', [
    ('expected_encoded_source_sha256', 'ENCODED_SOURCE_SHA_MISMATCH'),
    ('expected_decoded_rgba_sha256', 'DECODED_RGBA_SHA_OR_BYTES_MISMATCH'),
    ('expected_class_ids_sha256', 'INDEPENDENT_CLASS_SHA_MISMATCH'),
    ('expected_composed_owner_sha256', 'FROZEN_OWNER_SHA_MISMATCH'),
])
def test_stale_external_pin_rejected_before_shadow(monkeypatch, field, reason):
    kw = fixture()
    monkeypatch.setattr(adapter, 'propose_dual_owner_lab_reach_shadow',
                        lambda **_k: pytest.fail('unverified shadow invoked'))
    kw[field] = '0' * 64
    with pytest.raises(adapter.SignedDualOwnerInputHold, match=reason):
        adapter.propose_signed_dual_owner_lab_reach_shadow(**kw)


def test_decoded_alpha_change_is_not_hidden_by_valid_encoded_pin(monkeypatch):
    kw = fixture()
    monkeypatch.setattr(adapter, 'propose_dual_owner_lab_reach_shadow',
                        lambda **_k: pytest.fail('unverified shadow invoked'))
    kw['source_rgba'] = kw['source_rgba'].copy()
    kw['source_rgba'][0, 0, 3] = 0
    with pytest.raises(adapter.SignedDualOwnerInputHold, match='DECODED_RGBA_SHA_OR_BYTES_MISMATCH'):
        adapter.propose_signed_dual_owner_lab_reach_shadow(**kw)


def test_missing_external_pin_rejected():
    kw = fixture()
    kw['expected_class_ids_sha256'] = ''
    with pytest.raises(adapter.SignedDualOwnerInputHold, match='MISSING_EXTERNAL_SHA256_PIN'):
        adapter.propose_signed_dual_owner_lab_reach_shadow(**kw)


def test_reject_mocked_shadow_erasure_after_valid_pins(monkeypatch):
    kw = fixture()
    def corrupt(**inputs):
        out = inputs['composed_owner'].copy()
        out[8, 3] = 0
        return out, {'new_source_pixels': 0}
    monkeypatch.setattr(adapter, 'propose_dual_owner_lab_reach_shadow', corrupt)
    with pytest.raises(adapter.SignedDualOwnerInputHold,
                       match='SHADOW_POSTCONDITION_HOLD:FROZEN_OWNER_MODIFIED'):
        adapter.propose_signed_dual_owner_lab_reach_shadow(**kw)


def test_reject_mocked_shadow_nonopaque_addition_after_valid_pins(monkeypatch):
    kw = fixture()
    kw['source_rgba'] = kw['source_rgba'].copy()
    kw['source_rgba'][16, 6, 3] = 128
    # Re-encode and independently pin this altered synthetic input.
    buf = io.BytesIO()
    Image.fromarray(kw['source_rgba'], 'RGBA').save(buf, format='PNG')
    kw['encoded_source'] = buf.getvalue()
    kw['expected_encoded_source_sha256'] = hashlib.sha256(kw['encoded_source']).hexdigest()
    kw['expected_decoded_rgba_sha256'] = hashlib.sha256(
        kw['source_rgba'].tobytes(order='C')).hexdigest()
    def corrupt(**inputs):
        out = inputs['composed_owner'].copy()
        out[16, 6] = 1
        return out, {'new_source_pixels': 1}
    monkeypatch.setattr(adapter, 'propose_dual_owner_lab_reach_shadow', corrupt)
    with pytest.raises(adapter.SignedDualOwnerInputHold,
                       match='SHADOW_POSTCONDITION_HOLD:UNSUPPORTED_OR_NONOPAQUE_ADDITION'):
        adapter.propose_signed_dual_owner_lab_reach_shadow(**kw)


@pytest.mark.parametrize('target,reason', [
    ('composed_owner', 'SHADOW_MUTATED_FROZEN_OWNER'),
    ('class_ids', 'SHADOW_MUTATED_INDEPENDENT_CLASS'),
    ('source_rgba', 'SHADOW_MUTATED_SIGNED_SOURCE'),
])
def test_reject_shadow_inplace_mutation_of_verified_input(monkeypatch, target, reason):
    kw = fixture()
    def corrupt(**inputs):
        inputs[target].flat[0] ^= 1
        return inputs['composed_owner'].copy(), {'new_source_pixels': 0}
    monkeypatch.setattr(adapter, 'propose_dual_owner_lab_reach_shadow', corrupt)
    with pytest.raises(adapter.SignedDualOwnerInputHold, match=reason):
        adapter.propose_signed_dual_owner_lab_reach_shadow(**kw)


@pytest.mark.parametrize('alias_kind', [
    'frozen_owner', 'frozen_owner_view', 'class_ids', 'rgba_channel',
])
def test_reject_shadow_output_alias_of_authenticated_input(monkeypatch, alias_kind):
    kw = fixture()
    def shadow(**inputs):
        if alias_kind == 'frozen_owner':
            proposed = inputs['composed_owner']
        elif alias_kind == 'frozen_owner_view':
            proposed = inputs['composed_owner'].view()
        elif alias_kind == 'class_ids':
            proposed = inputs['class_ids']
        else:
            proposed = inputs['source_rgba'][..., 0]
        return proposed, {'new_source_pixels': 0}
    monkeypatch.setattr(adapter, 'propose_dual_owner_lab_reach_shadow', shadow)
    with pytest.raises(adapter.SignedDualOwnerInputHold,
                       match='SHADOW_OUTPUT_ALIASES_SIGNED_INPUT'):
        adapter.propose_signed_dual_owner_lab_reach_shadow(**kw)


def test_reject_shadow_output_nonarray_before_postcondition(monkeypatch):
    kw = fixture()
    monkeypatch.setattr(adapter, 'propose_dual_owner_lab_reach_shadow',
                        lambda **_inputs: (None, {'new_source_pixels': 0}))
    with pytest.raises(adapter.SignedDualOwnerInputHold,
                       match='INVALID_SHADOW_OUTPUT_TYPE'):
        adapter.propose_signed_dual_owner_lab_reach_shadow(**kw)


def test_caller_mutation_after_pins_cannot_change_authenticated_shadow(monkeypatch):
    kw = fixture()
    expected = {key: kw[key].copy() for key in
                ('source_rgba', 'class_ids', 'composed_owner')}

    def shadow(**inputs):
        # Simulate a concurrent caller changing every original input after
        # signed verification but before the shadow reads its arguments.
        for key in expected:
            kw[key].fill(0)
            assert np.array_equal(inputs[key], expected[key])
            assert not np.shares_memory(inputs[key], kw[key])
        return inputs['composed_owner'].copy(), {
            'schema': 'research-only', 'new_source_pixels': 0}

    monkeypatch.setattr(adapter, 'propose_dual_owner_lab_reach_shadow', shadow)
    proposed, receipt = adapter.propose_signed_dual_owner_lab_reach_shadow(**kw)
    assert np.array_equal(proposed, expected['composed_owner'])
    assert receipt['signed_source_encoded_and_decoded_verified']
    assert receipt['Phase4'] == 'FAIL'


def test_reject_shadow_output_alias_of_mutable_original_caller_owner(monkeypatch):
    kw = fixture()
    original = kw['composed_owner']
    def shadow(**_inputs):
        return original, {'new_source_pixels': 0}
    monkeypatch.setattr(adapter, 'propose_dual_owner_lab_reach_shadow', shadow)
    with pytest.raises(adapter.SignedDualOwnerInputHold,
                       match='SHADOW_OUTPUT_ALIASES_SIGNED_INPUT'):
        adapter.propose_signed_dual_owner_lab_reach_shadow(**kw)
