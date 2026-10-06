from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from minimalizer_zerobase.evaluation.forbidden_face_detail_gate import (
    forbidden_face_detail_ratio,
)
from minimalizer_zerobase.production.feature_survival_gate import (
    FeatureSignature,
    source_supported_feature_survival_report,
)

CANONICAL_HARD_GATE_VERSION = "sa7.35-v2"


@dataclass(frozen=True)
class CanonicalHardGateReport:
    version: str
    survival_pass: bool
    required_signature_count: int
    missing_count: int
    missing_signatures: tuple[FeatureSignature, ...]
    forbidden_face_detail_ratio: float
    forbidden_face_pass: bool
    pass_gate: bool

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_canonical_hard_gate(
    *,
    adopted_baseline_rgb: np.ndarray,
    current_rgb: np.ndarray,
    source_rgb: np.ndarray,
    subject_mask: np.ndarray,
    face_mask: np.ndarray,
    match_threshold: float = .20,
    max_forbidden_face_ratio: float = 0.0,
) -> CanonicalHardGateReport:
    """Evaluate the one canonical visual-adoption survival/face hard gate.

    The candidate image is always measured fresh. No previous JSON/report is
    accepted as input. Golden is deliberately absent from this interface.
    """
    baseline = np.asarray(adopted_baseline_rgb, dtype=np.uint8)
    current = np.asarray(current_rgb, dtype=np.uint8)
    source = np.asarray(source_rgb, dtype=np.uint8)
    subject = np.asarray(subject_mask, dtype=bool)
    face = np.asarray(face_mask, dtype=bool)

    if baseline.shape != current.shape or baseline.shape != source.shape:
        raise ValueError("baseline/current/source image shape mismatch")
    if baseline.ndim != 3 or baseline.shape[2] != 3:
        raise ValueError("RGB images required")
    if subject.shape != baseline.shape[:2]:
        raise ValueError("subject mask shape mismatch")
    if face.shape != baseline.shape[:2]:
        raise ValueError("face mask shape mismatch")
    if not np.any(subject):
        raise ValueError("subject mask is empty")
    if not np.any(face):
        raise ValueError("face mask is empty")
    if max_forbidden_face_ratio < 0:
        raise ValueError("max_forbidden_face_ratio must be non-negative")

    survival = source_supported_feature_survival_report(
        baseline,
        current,
        source,
        subject,
        subject,
        subject,
        match_threshold=match_threshold,
    )
    face_ratio = forbidden_face_detail_ratio(current, face)
    face_pass = face_ratio <= max_forbidden_face_ratio
    passed = survival.pass_gate and face_pass

    return CanonicalHardGateReport(
        version=CANONICAL_HARD_GATE_VERSION,
        survival_pass=survival.pass_gate,
        required_signature_count=len(survival.baseline),
        missing_count=len(survival.missing),
        missing_signatures=survival.missing,
        forbidden_face_detail_ratio=face_ratio,
        forbidden_face_pass=face_pass,
        pass_gate=passed,
    )
