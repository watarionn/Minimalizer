"""Research-only ATR18 dual-head provenance tests, not image-quality evidence."""
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


def _signed():
    rgba = np.zeros((3, 4, 4), np.uint8)
    rgba[0, 0] = (255, 0, 0, 255)
    rgba[0, 1] = (0, 255, 0, 255)
    rgba[1, 1] = (0, 0, 255, 255)
    encoded_io = io.BytesIO()
    Image.fromarray(rgba).save(encoded_io, format='PNG')
    encoded = encoded_io.getvalue()
    sha = lambda data: hashlib.sha256(data).hexdigest()
    return dict(encoded_source=encoded, source_rgba=rgba,
                expected_encoded_sha256=sha(encoded),
                expected_rgba_sha256=sha(rgba.tobytes()))


@pytest.fixture
def local_session(monkeypatch, tmp_path):
    model = tmp_path / atr.MODEL_FILENAME
    model.write_bytes(b'synthetic-atr-dual-head')
    pin = hashlib.sha256(model.read_bytes()).hexdigest()
    monkeypatch.setattr(atr, 'MODEL_SHA256', pin)
    monkeypatch.setattr(atr, 'MODEL_BYTES', model.stat().st_size)
    calls = []

    class FakeSession:
        def __init__(self, model_blob, sess_options, providers):
            calls.append(('init', model_blob))
            assert model_blob == b'synthetic-atr-dual-head'
            assert providers == ['CPUExecutionProvider']
            # Simulate path replacement after verified snapshot was opened.
            model.write_bytes(b'changed-after-snapshot')

        def get_inputs(self):
            return [types.SimpleNamespace(name='pixel_values')]

        def get_outputs(self):
            return [types.SimpleNamespace(name=x) for x in
                    ('logits', 'parsing_logits', 'edge_logits')]

        def get_providers(self):
            return ['CPUExecutionProvider']

        def run(self, names, feeds):
            calls.append(('run', names))
            assert feeds['pixel_values'].shape == (1, 3, 512, 512)
            raw = np.zeros((1, 18, 512, 512), np.float32)
            raw[0, 16] = 1
            refined = np.zeros_like(raw)
            refined[0, 4] = 1
            return [dict(logits=raw, parsing_logits=refined)[name]
                    for name in names]

    monkeypatch.setitem(sys.modules, 'onnxruntime', types.SimpleNamespace(
        SessionOptions=lambda: types.SimpleNamespace(),
        InferenceSession=FakeSession))
    return dict(**_signed(), onnx_path=model,
                expected_onnx_sha256=pin,
                expected_model_revision=atr.REVISION), calls


def test_one_authenticated_session_two_heads_and_private_receipts(local_session):
    kwargs, calls = local_session
    original = kwargs['source_rgba'].copy()
    raw, refined, receipt = atr.run_offline_atr_dual_head_observer(**kwargs)
    assert calls == [('init', b'synthetic-atr-dual-head'),
                     ('run', ['logits', 'parsing_logits'])]
    assert np.count_nonzero(raw == 16) == 3
    assert np.count_nonzero(refined == 4) == 3
    assert receipt['head_disagreement']['head_disagreement_px'] == 3
    assert receipt['raw_class_map_sha256_private'] == hashlib.sha256(raw.tobytes()).hexdigest()
    assert receipt['refined_class_map_sha256_private'] == hashlib.sha256(refined.tobytes()).hexdigest()
    assert receipt['head_selection_authorized'] is False
    assert receipt['owner_modified'] is False and receipt['Phase4'] == 'FAIL'
    assert np.array_equal(kwargs['source_rgba'], original)


def test_legacy_single_raw_head_contract_unchanged(local_session):
    kwargs, calls = local_session
    raw, receipt = atr.run_offline_atr_bag_observer(**kwargs)
    assert calls[-1] == ('run', ['logits'])
    assert receipt['schema'].endswith('bag-observer/v1')
    assert receipt['relevant_class_counts_opaque_only']['bag'] == 3
    assert np.count_nonzero(raw == 16) == 3


def test_wrong_model_pin_refused_before_loading(local_session):
    kwargs, calls = local_session
    kwargs['expected_onnx_sha256'] = '0' * 64
    with pytest.raises(SCHPResearchHold, match='CHECKPOINT_PIN'):
        atr.run_offline_atr_dual_head_observer(**kwargs)
    assert calls == []


def test_missing_refined_head_refused(local_session, monkeypatch):
    kwargs, _ = local_session
    original = sys.modules['onnxruntime'].InferenceSession

    class MissingHead(original):
        def get_outputs(self):
            return [types.SimpleNamespace(name='logits')]

    monkeypatch.setattr(sys.modules['onnxruntime'], 'InferenceSession', MissingHead)
    with pytest.raises(SCHPResearchHold, match='INTERFACE'):
        atr.run_offline_atr_dual_head_observer(**kwargs)


def test_invalid_refined_logits_refused(local_session, monkeypatch):
    kwargs, _ = local_session
    original = sys.modules['onnxruntime'].InferenceSession

    class InvalidRefined(original):
        def run(self, names, feeds):
            outputs = super().run(names, feeds)
            outputs[1] = np.zeros((1, 17, 512, 512), np.float32)
            return outputs

    monkeypatch.setattr(sys.modules['onnxruntime'], 'InferenceSession', InvalidRefined)
    with pytest.raises(SCHPResearchHold, match='ATR18_LOGITS'):
        atr.run_offline_atr_dual_head_observer(**kwargs)
