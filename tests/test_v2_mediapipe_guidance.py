from types import SimpleNamespace

import numpy as np
import pytest

from minimalize_engine.v2 import AnalysisGuidance
from minimalize_engine.v2.mediapipe_guidance import (
    MEDIAPIPE_MULTICLASS_LABELS,
    MediaPipeSemanticConfig,
    attach_mediapipe_semantics,
    build_mediapipe_semantic_guide,
    create_mediapipe_segmenter,
)


class _Mask:
    def __init__(self, value):
        self._value = np.asarray(value, dtype=np.float32)

    def numpy_view(self):
        return self._value[..., None]


class _Segmenter:
    def __init__(self, maps):
        self.maps = maps
        self.calls = 0

    def segment(self, image):
        self.calls += 1
        return SimpleNamespace(confidence_masks=[_Mask(value) for value in self.maps])


def _fake_mp():
    class ImageFormat:
        SRGB = "srgb"

    class Image:
        def __init__(self, *, image_format, data):
            self.image_format = image_format
            self.data = data

    return SimpleNamespace(Image=Image, ImageFormat=ImageFormat)


def _maps(shape=(2, 3)):
    return [np.full(shape, index / 10.0, dtype=np.float32) for index in range(6)]


def test_mediapipe_config_requires_model_path():
    with pytest.raises(ValueError):
        MediaPipeSemanticConfig(model_path="")


def test_create_segmenter_rejects_missing_model_before_import(tmp_path):
    config = MediaPipeSemanticConfig(model_path=str(tmp_path / "missing.tflite"))
    with pytest.raises(ValueError, match="does not exist"):
        create_mediapipe_segmenter(config)


def test_build_semantic_guide_masks_foreground_by_rembg(monkeypatch):
    source = np.zeros((2, 3, 3), dtype=np.uint8)
    subject = np.array([[1.0, 0.5, 0.0], [1.0, 0.5, 0.0]], dtype=np.float32)
    segmenter = _Segmenter(_maps())
    monkeypatch.setattr("minimalize_engine.v2.mediapipe_guidance._load_mediapipe", _fake_mp)
    guide = build_mediapipe_semantic_guide(
        source,
        config=MediaPipeSemanticConfig(model_path="unused.tflite"),
        segmenter=segmenter,
        subject_prob=subject,
    )
    assert guide.labels == MEDIAPIPE_MULTICLASS_LABELS[1:]
    assert guide.provider == "mediapipe"
    assert guide.model == "selfie_multiclass_256x256"
    assert guide.confidence_maps.shape == (5, 2, 3)
    np.testing.assert_allclose(guide.confidence_maps[0], 0.1 * subject)
    np.testing.assert_allclose(guide.confidence_maps[-1], 0.5 * subject)
    assert segmenter.calls == 1


def test_attach_semantics_preserves_rembg_guidance(monkeypatch):
    source = np.zeros((2, 3, 3), dtype=np.uint8)
    subject = np.full((2, 3), 0.9, dtype=np.float32)
    confidence = np.full((2, 3), 0.64, dtype=np.float32)
    base = AnalysisGuidance(
        subject_prob=subject,
        subject_confidence=confidence,
        subject_provider="rembg",
        subject_model="isnet-anime",
    )
    segmenter = _Segmenter(_maps())
    monkeypatch.setattr("minimalize_engine.v2.mediapipe_guidance._load_mediapipe", _fake_mp)
    combined = attach_mediapipe_semantics(
        source,
        config=MediaPipeSemanticConfig(model_path="unused.tflite"),
        base_guidance=base,
        segmenter=segmenter,
    )
    np.testing.assert_array_equal(combined.subject_prob, subject)
    np.testing.assert_array_equal(combined.subject_confidence, confidence)
    assert combined.subject_provider == "rembg"
    assert combined.subject_model == "isnet-anime"
    assert combined.semantic is not None
    assert combined.semantic.provider == "mediapipe"
