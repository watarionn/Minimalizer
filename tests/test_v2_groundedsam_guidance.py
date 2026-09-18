from __future__ import annotations

import numpy as np
import pytest

from minimalize_engine.v2 import AnalysisGuidance, SemanticGuide
from minimalize_engine.v2.groundedsam_guidance import (
    GROUNDED_SAM_LABELS,
    GroundedSamConfig,
    attach_groundedsam_semantics,
    fuse_semantic_guides,
    semantic_maps_from_detections,
)


def _subject() -> np.ndarray:
    return np.array(
        [
            [1.0, 1.0, 0.0, 0.0],
            [1.0, 0.8, 0.2, 0.0],
            [1.0, 1.0, 0.0, 0.0],
            [0.9, 1.0, 0.0, 0.0],
        ],
        dtype=np.float32,
    )


def test_groundedsam_config_rejects_invalid_threshold_order():
    with pytest.raises(ValueError, match="detection_full_confidence"):
        GroundedSamConfig(
            detection_threshold=0.40,
            detection_full_confidence=0.40,
        )


def test_groundedsam_config_rejects_unknown_device():
    with pytest.raises(ValueError, match="device"):
        GroundedSamConfig(device="metal")


def test_semantic_maps_use_subject_authority_and_canonical_labels():
    subject = _subject()
    masks = np.zeros((4, 4, 4), dtype=bool)
    masks[0, 0:2, 0:2] = True
    masks[1, 0:2, 0:2] = True
    masks[2, 2:4, 0:2] = True
    masks[3, 0:2, 0:2] = True

    maps = semantic_maps_from_detections(
        subject_prob=subject,
        raw_labels=("hair", "face", "left hand", "ribbon"),
        scores=(0.40, 0.40, 0.40, 0.40),
        masks=masks,
        sam_ious=(1.0, 1.0, 1.0, 1.0),
        config=GroundedSamConfig(
            hair_max_subject_ratio=1.0,
            face_max_subject_ratio=1.0,
            limb_max_subject_ratio=1.0,
            accessory_max_subject_ratio=1.0,
        ),
    )

    assert maps.shape == (4, 4, 4)
    assert GROUNDED_SAM_LABELS == ("hair", "face-skin", "limb", "accessory")
    np.testing.assert_allclose(maps[0, 0:2, 0:2], subject[0:2, 0:2])
    np.testing.assert_allclose(maps[1, 0:2, 0:2], subject[0:2, 0:2])
    np.testing.assert_allclose(maps[2, 2:4, 0:2], subject[2:4, 0:2])
    np.testing.assert_allclose(maps[3, 0:2, 0:2], subject[0:2, 0:2])
    assert np.all(maps[:, :, 2:] <= subject[None, :, 2:])


def test_semantic_maps_reject_oversize_part_masks():
    subject = np.ones((4, 4), dtype=np.float32)
    masks = np.ones((2, 4, 4), dtype=bool)

    maps = semantic_maps_from_detections(
        subject_prob=subject,
        raw_labels=("hair", "face"),
        scores=(0.40, 0.40),
        masks=masks,
        sam_ious=(1.0, 1.0),
        config=GroundedSamConfig(
            hair_max_subject_ratio=0.50,
            face_max_subject_ratio=0.15,
        ),
    )

    assert np.count_nonzero(maps) == 0


def test_semantic_maps_keep_low_confidence_evidence_below_high_confidence():
    subject = np.ones((2, 2), dtype=np.float32)
    masks = np.ones((1, 2, 2), dtype=bool)

    maps = semantic_maps_from_detections(
        subject_prob=subject,
        raw_labels=("hair",),
        scores=(0.30,),
        masks=masks,
        sam_ious=(0.80,),
        config=GroundedSamConfig(hair_max_subject_ratio=1.0),
    )

    np.testing.assert_allclose(maps[0], 0.4, atol=1e-6)
    assert float(maps[0].max()) < 0.80


def test_fuse_semantic_guides_uses_max_confidence_per_shared_label():
    primary = SemanticGuide(
        labels=("hair", "clothes"),
        confidence_maps=np.array(
            [
                [[0.2, 0.7], [0.0, 0.1]],
                [[0.8, 0.1], [0.2, 0.0]],
            ],
            dtype=np.float32,
        ),
        provider="mediapipe",
        model="selfie_multiclass_256x256",
    )
    supplemental = SemanticGuide(
        labels=("hair", "accessory"),
        confidence_maps=np.array(
            [
                [[0.9, 0.3], [0.1, 0.0]],
                [[0.0, 0.6], [0.4, 0.0]],
            ],
            dtype=np.float32,
        ),
        provider="grounded-sam",
        model="grounding-dino-tiny+sam-vit-base",
    )

    fused = fuse_semantic_guides(primary, supplemental)

    assert fused.labels == ("hair", "clothes", "accessory")
    np.testing.assert_allclose(
        fused.confidence_maps[0],
        np.array([[0.9, 0.7], [0.1, 0.1]], dtype=np.float32),
    )
    np.testing.assert_allclose(fused.confidence_maps[1], primary.confidence_maps[1])
    np.testing.assert_allclose(
        fused.confidence_maps[2], supplemental.confidence_maps[1]
    )
    assert fused.provider == "mediapipe+grounded-sam"


def test_attach_groundedsam_preserves_rembg_foreground_authority(monkeypatch):
    source = np.zeros((2, 2, 3), dtype=np.uint8)
    subject = np.array([[1.0, 0.7], [0.2, 0.0]], dtype=np.float32)
    subject_confidence = subject**2
    base_semantic = SemanticGuide(
        labels=("clothes",),
        confidence_maps=np.full((1, 2, 2), 0.6, dtype=np.float32),
        provider="mediapipe",
        model="selfie_multiclass_256x256",
    )
    base = AnalysisGuidance(
        subject_prob=subject,
        subject_confidence=subject_confidence,
        semantic=base_semantic,
        subject_provider="rembg",
        subject_model="isnet-anime",
    )
    supplemental = SemanticGuide(
        labels=("hair",),
        confidence_maps=np.full((1, 2, 2), 0.8, dtype=np.float32),
        provider="grounded-sam",
        model="grounding-dino-tiny+sam-vit-base",
    )

    monkeypatch.setattr(
        "minimalize_engine.v2.groundedsam_guidance.build_groundedsam_semantic_guide",
        lambda *args, **kwargs: supplemental,
    )

    combined = attach_groundedsam_semantics(source, base_guidance=base)

    np.testing.assert_array_equal(combined.subject_prob, subject)
    np.testing.assert_array_equal(combined.subject_confidence, subject_confidence)
    assert combined.subject_provider == "rembg"
    assert combined.subject_model == "isnet-anime"
    assert combined.semantic is not None
    assert combined.semantic.labels == ("clothes", "hair")


def test_attach_groundedsam_requires_foreground_authority():
    base = AnalysisGuidance()

    with pytest.raises(ValueError, match="subject_prob"):
        attach_groundedsam_semantics(
            np.zeros((2, 2, 3), dtype=np.uint8),
            base_guidance=base,
        )
