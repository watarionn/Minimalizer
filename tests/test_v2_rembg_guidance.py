from types import SimpleNamespace

import numpy as np
from PIL import Image
import pytest

from minimalize_engine.v2.rembg_guidance import (
    RembgGuidanceConfig,
    build_rembg_guidance,
    subject_confidence_from_probability,
)


def test_subject_confidence_is_weak_near_half_and_strong_at_extremes():
    probability = np.array([[0.0, 0.25, 0.5, 0.75, 1.0]], dtype=np.float32)
    confidence = subject_confidence_from_probability(probability)
    np.testing.assert_allclose(confidence, [[1.0, 0.25, 0.0, 0.25, 1.0]])


def test_rembg_config_requires_model_name():
    with pytest.raises(ValueError):
        RembgGuidanceConfig(model="")


def test_rembg_config_requires_conservative_confidence_power():
    with pytest.raises(ValueError):
        RembgGuidanceConfig(confidence_power=0.5)
    with pytest.raises(ValueError):
        subject_confidence_from_probability(
            np.array([[0.0, 1.0]], dtype=np.float32),
            power=float("nan"),
        )


def test_build_rembg_guidance_uses_mask_only_as_analysis_hint(monkeypatch):
    source = np.zeros((4, 5, 3), dtype=np.uint8)
    mask = Image.fromarray(np.array([
        [0, 0, 128, 255, 255],
        [0, 0, 128, 255, 255],
        [0, 0, 128, 255, 255],
        [0, 0, 128, 255, 255],
    ], dtype=np.uint8), mode="L")
    calls = {}

    def fake_new_session(model):
        calls["model"] = model
        return "session"

    def fake_remove(image, *, session, only_mask):
        calls["session"] = session
        calls["only_mask"] = only_mask
        calls["size"] = image.size
        return mask

    fake = SimpleNamespace(new_session=fake_new_session, remove=fake_remove)
    monkeypatch.setattr("minimalize_engine.v2.rembg_guidance._load_rembg", lambda: fake)

    guidance = build_rembg_guidance(
        source,
        config=RembgGuidanceConfig(model="isnet-anime"),
    )

    assert calls == {
        "model": "isnet-anime",
        "session": "session",
        "only_mask": True,
        "size": (5, 4),
    }
    assert guidance.subject_provider == "rembg"
    assert guidance.subject_model == "isnet-anime"
    assert guidance.subject_prob is not None
    assert guidance.subject_confidence is not None
    assert guidance.subject_prob.shape == (4, 5)
    assert float(guidance.subject_prob[0, 0]) == pytest.approx(0.0)
    assert float(guidance.subject_prob[0, 2]) == pytest.approx(128.0 / 255.0)
    assert float(guidance.subject_prob[0, 4]) == pytest.approx(1.0)
    assert float(guidance.subject_confidence[0, 2]) < 0.01


def test_build_rembg_guidance_accepts_reused_session(monkeypatch):
    source = np.zeros((3, 3, 3), dtype=np.uint8)
    mask = np.full((3, 3), 255, dtype=np.uint8)
    calls = {"new_session": 0}

    def fake_new_session(model):
        calls["new_session"] += 1
        return "unexpected"

    def fake_remove(image, *, session, only_mask):
        assert session == "reused-session"
        assert only_mask is True
        return mask

    fake = SimpleNamespace(new_session=fake_new_session, remove=fake_remove)
    monkeypatch.setattr("minimalize_engine.v2.rembg_guidance._load_rembg", lambda: fake)
    guidance = build_rembg_guidance(source, session="reused-session")
    assert calls["new_session"] == 0
    assert guidance.subject_prob is not None
    assert np.all(guidance.subject_prob == 1.0)
