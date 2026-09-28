from __future__ import annotations

import json

import numpy as np
from PIL import Image

from minimalizer_zerobase.analyzers.contracts import Provenance
from minimalizer_zerobase.subject.artifacts import write_phase3_artifacts
from minimalizer_zerobase.subject.extraction import (
    alpha_is_informative,
    extract_canonical_subject,
)


def test_informative_source_alpha_is_used_without_fallback():
    rgba = np.zeros((20, 20, 4), dtype=np.uint8)
    rgba[4:16, 6:14, :3] = (120, 40, 200)
    rgba[4:16, 6:14, 3] = 255
    image = Image.fromarray(rgba, mode="RGBA")

    def forbidden(_rgb):
        raise AssertionError("fallback must not be used")

    result = extract_canonical_subject(image, probability_provider=forbidden)

    assert result.metadata.evidence_source == "source-alpha"
    assert result.metadata.alpha_informative is True
    assert result.metadata.bbox_xywh == (6, 4, 8, 12)
    assert result.metadata.foreground_ratio == 96 / 400


def test_nearly_opaque_alpha_is_rejected_and_fallback_is_used():
    rgba = np.full((20, 20, 4), 255, dtype=np.uint8)
    rgba[:, :, :3] = (40, 80, 120)
    rgba[0, 0, 3] = 0
    image = Image.fromarray(rgba, mode="RGBA")

    probability = np.zeros((20, 20), dtype=np.float32)
    probability[3:17, 5:15] = 0.9

    def fallback(_rgb):
        return probability, Provenance(
            producer="test-segmenter",
            producer_version="1",
            model_id="test-model",
        )

    result = extract_canonical_subject(image, probability_provider=fallback)

    assert result.metadata.alpha_informative is False
    assert result.metadata.evidence_source == "test-segmenter"
    assert result.metadata.bbox_xywh == (5, 3, 10, 14)
    assert result.metadata.foreground_ratio == 140 / 400


def test_alpha_informative_guard_rejects_full_frame_alpha():
    alpha = np.full((10, 10), 255, dtype=np.uint8)
    informative, ratio = alpha_is_informative(alpha)
    assert informative is False
    assert ratio == 1.0


def test_phase3_artifacts_include_visuals_metrics_and_binding(tmp_path):
    rgba = np.zeros((16, 16, 4), dtype=np.uint8)
    rgba[3:13, 4:12] = (200, 80, 30, 255)
    source = tmp_path / "case.png"
    Image.fromarray(rgba, mode="RGBA").save(source)

    result = extract_canonical_subject(Image.open(source))
    output = tmp_path / "artifacts"
    stage = write_phase3_artifacts(
        source,
        result,
        output,
        config={"mask_threshold": 0.5},
    )

    assert (output / "03_subject_mask.png").exists()
    assert (output / "03_subject_overlay.png").exists()
    assert (output / "preview.png").exists()
    assert (output / "metrics.json").exists()
    assert (output / "stage.json").exists()

    persisted = json.loads((output / "stage.json").read_text(encoding="utf-8"))
    assert persisted["phase"] == 3
    assert persisted["source"]["sha256"] == stage["source"]["sha256"]
    assert persisted["metadata"]["evidence_source"] == "source-alpha"
    assert persisted["outputs"]["03_subject_mask.png"]
    assert persisted["outputs"]["03_subject_overlay.png"]
