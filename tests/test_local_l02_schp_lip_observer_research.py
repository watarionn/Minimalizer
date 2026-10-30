"""Source-free fail-closed controls. These do not prove signed image quality."""
import hashlib
import io
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
import local_l02_schp_lip_observer_research as schp
from local_l02_schp_lip_observer_research import (
    SIZE, SCHPResearchHold, _decode_logits, _prepare,
    _validate_signed_source, run_offline_observer,
)


def signed():
    rgba = np.zeros((4, 5, 4), np.uint8)
    rgba[1:3, 1:4] = (120, 90, 40, 255)
    output = io.BytesIO()
    Image.fromarray(rgba).save(output, format='PNG')
    encoded = output.getvalue()
    return dict(encoded_source=encoded, source_rgba=rgba,
                expected_encoded_sha256=hashlib.sha256(encoded).hexdigest(),
                expected_rgba_sha256=hashlib.sha256(rgba.tobytes()).hexdigest())


def test_signed_source_and_exact_preprocessing():
    s = signed()
    _validate_signed_source(**s)
    tensor = _prepare(s['source_rgba'])
    assert tensor.shape == (1, 3, SIZE, SIZE)
    assert tensor.dtype == np.float32
    assert np.isfinite(tensor).all()
    # The fully transparent corner is composited white, not black.
    assert np.allclose(tensor[0, :, 0, 0], (1 - np.array([.406, .456, .485])) / [.225, .224, .229], atol=1e-5)


def test_external_pins_and_decoded_source_are_required():
    s = signed()
    s['expected_encoded_sha256'] = '0' * 64
    with pytest.raises(SCHPResearchHold, match='SHA_MISMATCH'):
        _validate_signed_source(**s)
    s = signed()
    s['source_rgba'] = s['source_rgba'].copy()
    s['source_rgba'][1, 1, 0] ^= 1
    s['expected_rgba_sha256'] = hashlib.sha256(s['source_rgba'].tobytes()).hexdigest()
    with pytest.raises(SCHPResearchHold, match='RGBA_BYTES_MISMATCH'):
        _validate_signed_source(**s)


def test_invalid_logits_fail_closed():
    alpha = signed()['source_rgba'][..., 3]
    with pytest.raises(SCHPResearchHold, match='LOGITS'):
        _decode_logits(np.zeros((1, 19, SIZE, SIZE), np.float32), alpha)
    x = np.zeros((1, 20, SIZE, SIZE), np.float32)
    x[0, 7, 0, 0] = np.nan
    with pytest.raises(SCHPResearchHold, match='LOGITS'):
        _decode_logits(x, alpha)


def test_projection_respects_alpha_and_does_not_promote_owner():
    alpha = signed()['source_rgba'][..., 3]
    x = np.zeros((1, 20, SIZE, SIZE), np.float32)
    x[0, 7] = 1
    result = _decode_logits(x, alpha)
    assert np.all(result[alpha > 0] == 7)
    assert np.all(result[alpha == 0] == 0)


def test_missing_or_wrong_model_pin_fails_before_import(tmp_path):
    s = signed()
    fake = tmp_path / 'checkpoint.onnx'
    fake.write_bytes(b'not-a-model')
    with pytest.raises(SCHPResearchHold, match='UNVERIFIED_SCHP_CHECKPOINT_PIN'):
        run_offline_observer(**s, onnx_path=fake, expected_onnx_sha256='0' * 64, expected_model_revision='a' * 40)
    with pytest.raises(SCHPResearchHold, match='MISSING_LOCAL_PINNED_ONNX'):
        run_offline_observer(**s, onnx_path=fake, expected_onnx_sha256='invalid', expected_model_revision='a' * 40)


def test_local_fake_session_observer_only_and_no_release(monkeypatch, tmp_path):
    import types
    s = signed()
    model = tmp_path / schp.SCHP_LIP20_INT8_FILENAME
    model.write_bytes(b'synthetic-model-bytes-only')
    # The fake model is only accepted by this isolated test's monkeypatch.
    # Real inference is hard-pinned to the public checkpoint SHA and size.
    monkeypatch.setattr(schp, 'SCHP_LIP20_INT8_SHA256', hashlib.sha256(model.read_bytes()).hexdigest())
    monkeypatch.setattr(schp, 'SCHP_LIP20_INT8_SIZE', model.stat().st_size)

    class FakeSession:
        def __init__(self, model_blob, sess_options, providers):
            # Simulate replacement of the file after authentication. The
            # session must receive the verified immutable bytes, not a path.
            assert type(model_blob) is bytes
            assert model_blob == b'synthetic-model-bytes-only'
            model.write_bytes(b'replaced-after-verified-snapshot')
            assert providers == ['CPUExecutionProvider']
        def get_inputs(self):
            return [types.SimpleNamespace(name='pixel_values')]
        def get_outputs(self):
            return [types.SimpleNamespace(name='logits')]
        def get_providers(self):
            return ['CPUExecutionProvider']
        def run(self, outputs, feeds):
            assert outputs == ['logits']
            assert feeds['pixel_values'].shape == (1, 3, SIZE, SIZE)
            x = np.zeros((1, 20, SIZE, SIZE), np.float32)
            x[0, 7] = 1.0
            return [x]

    fake_ort = types.SimpleNamespace(SessionOptions=lambda: types.SimpleNamespace(),
                                     InferenceSession=FakeSession)
    monkeypatch.setitem(sys.modules, 'onnxruntime', fake_ort)
    before = s['source_rgba'].copy()
    classes, receipt = run_offline_observer(
        **s, onnx_path=model,
        expected_onnx_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
        expected_model_revision=schp.SCHP_LIP20_INT8_REVISION)
    assert np.array_equal(before, s['source_rgba'])
    assert np.all(classes[before[..., 3] > 0] == 7)
    assert receipt['relevant_class_counts_opaque_only']['coat'] == 6
    assert receipt['human_annotations_used'] is False
    assert receipt['owner_modified'] is False
    assert receipt['dataset_licence_production_cleared'] is False
    assert receipt['Phase4'] == 'FAIL'
    assert receipt['production'] == 'NO_GO'


def test_public_checkpoint_pin_contract_is_fixed():
    assert schp.SCHP_LIP20_INT8_REVISION == '3cc2b2d00b16840652c1b7845fd78466dae7f157'
    assert schp.SCHP_LIP20_INT8_SHA256 == '871c9e209dc67d6be61c73dcc79cb49e638fcf5bbc35a19b4c7429eba0bfc046'
    assert schp.SCHP_LIP20_INT8_SIZE == 68314352
    assert schp.SCHP_LIP20_INT8_FILENAME == 'schp-lip-20-int8-static.onnx'


def test_checkpoint_file_identity_and_size_fail_closed(tmp_path):
    s = signed()
    fake = tmp_path / 'unrelated.onnx'
    fake.write_bytes(b'wrong-model')
    kwargs = dict(**s, onnx_path=fake,
                  expected_model_revision=schp.SCHP_LIP20_INT8_REVISION,
                  expected_onnx_sha256=schp.SCHP_LIP20_INT8_SHA256)
    with pytest.raises(SCHPResearchHold, match='UNVERIFIED_SCHP_CHECKPOINT_FILE'):
        run_offline_observer(**kwargs)
    fake = tmp_path / schp.SCHP_LIP20_INT8_FILENAME
    fake.write_bytes(b'wrong-model')
    kwargs['onnx_path'] = fake
    with pytest.raises(SCHPResearchHold, match='UNVERIFIED_SCHP_CHECKPOINT_FILE'):
        run_offline_observer(**kwargs)
    kwargs['expected_onnx_sha256'] = 'f' * 64
    with pytest.raises(SCHPResearchHold, match='UNVERIFIED_SCHP_CHECKPOINT_PIN'):
        run_offline_observer(**kwargs)


def test_signed_source_validation_returns_independent_readonly_snapshot():
    s = signed()
    verified = _validate_signed_source(**s)
    before = verified.copy()
    s['source_rgba'][:] = 0
    assert np.array_equal(verified, before)
    assert not np.shares_memory(verified, s['source_rgba'])
    assert not verified.flags.writeable
    with pytest.raises(ValueError):
        verified[1, 1, 0] = 0


def test_caller_mutation_after_signed_validation_does_not_change_inference(monkeypatch, tmp_path):
    import types
    s = signed()
    model = tmp_path / schp.SCHP_LIP20_INT8_FILENAME
    model.write_bytes(b'isolated-fake-onnx')
    pinned = hashlib.sha256(model.read_bytes()).hexdigest()
    monkeypatch.setattr(schp, 'SCHP_LIP20_INT8_SHA256', pinned)
    monkeypatch.setattr(schp, 'SCHP_LIP20_INT8_SIZE', model.stat().st_size)

    class FakeSession:
        def __init__(self, model_blob, sess_options, providers):
            assert model_blob == b'isolated-fake-onnx'
            assert providers == ['CPUExecutionProvider']
            # Mutate caller-owned source after validation but before preprocessing.
            s['source_rgba'][:] = 0
        def get_inputs(self):
            return [types.SimpleNamespace(name='pixel_values')]
        def get_outputs(self):
            return [types.SimpleNamespace(name='logits')]
        def get_providers(self):
            return ['CPUExecutionProvider']
        def run(self, outputs, feeds):
            assert outputs == ['logits']
            # The original brown opaque pixel must survive, not turn white.
            center = feeds['pixel_values'][0, :, SIZE // 2, SIZE // 2]
            expected = (np.array([120, 90, 40], np.float32) / 255 - schp.MEAN) / schp.STD
            assert np.allclose(center, expected, atol=1e-4)
            logits = np.zeros((1, 20, SIZE, SIZE), np.float32)
            logits[0, 7] = 1
            return [logits]

    fake_ort = types.SimpleNamespace(SessionOptions=lambda: types.SimpleNamespace(),
                                     InferenceSession=FakeSession)
    monkeypatch.setitem(sys.modules, 'onnxruntime', fake_ort)
    classes, receipt = run_offline_observer(
        **s, onnx_path=model, expected_onnx_sha256=pinned,
        expected_model_revision=schp.SCHP_LIP20_INT8_REVISION)
    assert np.count_nonzero(s['source_rgba']) == 0
    assert receipt['relevant_class_counts_opaque_only']['coat'] == 6
    assert np.count_nonzero(classes == 7) == 6
    assert receipt['Phase4'] == 'FAIL'
