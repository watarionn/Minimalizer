"""Source-free fail-closed controls. These do not prove signed image quality."""
import hashlib
import io
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
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
    with pytest.raises(SCHPResearchHold, match='ONNX_SHA_MISMATCH'):
        run_offline_observer(**s, onnx_path=fake, expected_onnx_sha256='0' * 64, expected_model_revision='a' * 40)
    with pytest.raises(SCHPResearchHold, match='MISSING_LOCAL_PINNED_ONNX'):
        run_offline_observer(**s, onnx_path=fake, expected_onnx_sha256='invalid', expected_model_revision='a' * 40)


def test_local_fake_session_observer_only_and_no_release(monkeypatch, tmp_path):
    import types
    s = signed()
    model = tmp_path / 'fake.onnx'
    model.write_bytes(b'synthetic-model-bytes-only')

    class FakeSession:
        def __init__(self, path, sess_options, providers):
            assert path == str(model)
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
        expected_model_revision='a' * 40)
    assert np.array_equal(before, s['source_rgba'])
    assert np.all(classes[before[..., 3] > 0] == 7)
    assert receipt['relevant_class_counts_opaque_only']['coat'] == 6
    assert receipt['human_annotations_used'] is False
    assert receipt['owner_modified'] is False
    assert receipt['dataset_licence_production_cleared'] is False
    assert receipt['Phase4'] == 'FAIL'
    assert receipt['production'] == 'NO_GO'
