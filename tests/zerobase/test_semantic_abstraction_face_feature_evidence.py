from __future__ import annotations

import numpy as np

from minimalizer_zerobase.semantic_abstraction.face_feature_evidence import (
    attach_facial_feature_evidence,
    detect_facial_feature_evidence,
)
from minimalizer_zerobase.semantic_abstraction.face_neutralization import (
    face_neutralization_gate,
)
from minimalizer_zerobase.semantic_abstraction.ir import (
    AbstractionPlan,
    AbstractionPolicy,
    SemanticPart,
)


def _synthetic_face() -> tuple[np.ndarray, np.ndarray]:
    rgb = np.full((80, 80, 3), 210, dtype=np.uint8)
    mask = np.zeros((80, 80), dtype=np.uint8)
    mask[10:70, 15:65] = 1
    rgb[28:34, 27:33] = 35
    rgb[29:35, 47:53] = 35
    rgb[50:54, 32:49] = 45
    return rgb, mask


def test_detects_paired_eye_like_regions_and_mouth() -> None:
    rgb, mask = _synthetic_face()
    evidence = detect_facial_feature_evidence(rgb, mask)
    assert evidence.paired_eye_like is True
    assert evidence.mouth_like is True
    assert {part.subcategory for part in evidence.parts} == {
        "eye_left",
        "eye_right",
        "mouth_like",
    }


def test_uniform_face_has_no_feature_parts() -> None:
    rgb = np.full((64, 64, 3), 180, dtype=np.uint8)
    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[8:56, 12:52] = 1
    evidence = detect_facial_feature_evidence(rgb, mask)
    assert evidence.paired_eye_like is False
    assert evidence.mouth_like is False
    assert evidence.parts == ()


def test_attached_features_are_forced_to_suppress() -> None:
    rgb, mask = _synthetic_face()
    evidence = detect_facial_feature_evidence(rgb, mask)
    plan = AbstractionPlan(
        parts=(
            SemanticPart(
                id="face",
                category="face",
                abstraction_policy=AbstractionPolicy.PRESERVE,
            ),
        )
    )
    result = attach_facial_feature_evidence(plan, evidence)
    features = [part for part in result.parts if part.category == "facial_feature"]
    assert len(features) == 3
    assert all(part.abstraction_policy is AbstractionPolicy.SUPPRESS for part in features)
    assert face_neutralization_gate(result)["pass"] is True


def test_detector_is_deterministic() -> None:
    rgb, mask = _synthetic_face()
    assert detect_facial_feature_evidence(rgb, mask).to_dict() == detect_facial_feature_evidence(
        rgb, mask
    ).to_dict()
