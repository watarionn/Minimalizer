"""Synthetic observer contracts; not signed-image quality evidence."""
import hashlib
import io
import sys
import types
from pathlib import Path
import numpy as np
import pytest
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
import local_l02_schp_atr_bag_observer_research as atr
from local_l02_schp_lip_observer_research import SCHPResearchHold


def signed():
    rgba = np.zeros((4, 5, 4), np.uint8)
    rgba[1:3, 1:4] = (100, 50, 20, 255)
    out = io.BytesIO()
    Image.fromarray(rgba).save(out, format='PNG')
    encoded = out.getvalue()
    return dict(encoded_source=encoded, source_rgba=rgba,
                expected_encoded_sha256=hashlib.sha256(encoded).hexdigest(),
                expected_rgba_sha256=hashlib.sha256(rgba.tobytes()).hexdigest())


def test_taxonomy_and_source_domain():
    assert atr.RELEVANT[16] == 'bag' and atr.RELEVANT[14] == 'left_arm'
    alpha = signed()['source_rgba'][..., 3]
    x = np.zeros((1, 18, atr.SIZE, atr.SIZE), np.float32)
    x[0, 16] = 1
    ids = atr._decode(x, alpha)
    assert np.all(ids[alpha > 0] == 16)
    assert np.all(ids[alpha == 0] == 0)
    assert atr._prepare(signed()['source_rgba']).shape == (1, 3, 512, 512)


def test_wrong_logits_rejected():
    alpha = signed()['source_rgba'][..., 3]
    with pytest.raises(SCHPResearchHold, match='ATR18_LOGITS'):
        atr._decode(np.zeros((1, 20, 512, 512), np.float32), alpha)
    x = np.zeros((1, 18, 512, 512), np.float32)
    x[0, 16, 0, 0] = np.inf
    with pytest.raises(SCHPResearchHold, match='ATR18_LOGITS'):
        atr._decode(x, alpha)


def test_checkpoint_pin_and_file_gate(tmp_path):
    model = tmp_path / atr.MODEL_FILENAME
    model.write_bytes(b'wrong-model')
    kw = dict(**signed(), onnx_path=model, expected_onnx_sha256=atr.MODEL_SHA256,
              expected_model_revision=atr.REVISION)
    with pytest.raises(SCHPResearchHold, match='CHECKPOINT_FILE'):
        atr.run_offline_atr_bag_observer(**kw)
    kw['expected_onnx_sha256'] = '0' * 64
    with pytest.raises(SCHPResearchHold, match='CHECKPOINT_PIN'):
        atr.run_offline_atr_bag_observer(**kw)


def test_fake_local_cpu_observer_only(monkeypatch, tmp_path):
    model = tmp_path / atr.MODEL_FILENAME
    model.write_bytes(b'synthetic-atr-only')
    pin = hashlib.sha256(model.read_bytes()).hexdigest()
    monkeypatch.setattr(atr, 'MODEL_SHA256', pin)
    monkeypatch.setattr(atr, 'MODEL_BYTES', model.stat().st_size)
    class FakeSession:
        def __init__(self, model_blob, sess_options, providers):
            assert model_blob == b'synthetic-atr-only'
            assert providers == ['CPUExecutionProvider']
            model.write_bytes(b'path-replaced-after-snapshot')
        def get_inputs(self):
            return [types.SimpleNamespace(name='pixel_values')]
        def get_outputs(self):
            return [types.SimpleNamespace(name='logits')]
        def get_providers(self):
            return ['CPUExecutionProvider']
        def run(self, outputs, feeds):
            assert outputs == ['logits']
            assert feeds['pixel_values'].shape == (1, 3, 512, 512)
            x = np.zeros((1, 18, 512, 512), np.float32)
            x[0, 16] = 1
            return [x]
    monkeypatch.setitem(sys.modules, 'onnxruntime',
                        types.SimpleNamespace(SessionOptions=lambda: types.SimpleNamespace(),
                                              InferenceSession=FakeSession))
    original = signed()
    before = original['source_rgba'].copy()
    ids, receipt = atr.run_offline_atr_bag_observer(
        **original, onnx_path=model, expected_onnx_sha256=pin,
        expected_model_revision=atr.REVISION)
    assert np.array_equal(original['source_rgba'], before)
    assert receipt['relevant_class_counts_opaque_only']['bag'] == 6
    assert np.count_nonzero(ids == 16) == 6
    assert receipt['owner_modified'] is False
    assert receipt['atr_training_data_rights_verified'] is False
    assert receipt['production'] == 'NO_GO'
