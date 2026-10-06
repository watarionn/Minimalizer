import numpy as np

from minimalizer_zerobase.evaluation.canonical_hard_gate import (
    CANONICAL_HARD_GATE_VERSION,
    evaluate_canonical_hard_gate,
)
from minimalizer_zerobase.production.feature_survival_gate import (
    feature_survival_report,
    source_supported_feature_survival_report,
)


def _images():
    source = np.full((32, 32, 3), [240, 220, 200], dtype=np.uint8)
    source[8:24, 8:24] = [160, 80, 40]
    baseline = source.copy()
    # Baseline-only artifact absent from the original source.
    baseline[2:6, 2:6] = [80, 144, 208]
    current = source.copy()
    subject = np.ones((32, 32), dtype=bool)
    face = np.zeros((32, 32), dtype=bool)
    face[10:22, 10:22] = True
    return source, baseline, current, subject, face


def test_source_supported_gate_does_not_canonize_baseline_artifact():
    source, baseline, current, subject, _ = _images()
    legacy = feature_survival_report(baseline, current, subject, subject)
    canonical = source_supported_feature_survival_report(
        baseline,
        current,
        source,
        subject,
        subject,
        subject,
    )
    assert not legacy.pass_gate
    assert canonical.pass_gate


def test_canonical_gate_measures_current_face_fresh():
    source, baseline, current, subject, face = _images()
    clean = evaluate_canonical_hard_gate(
        adopted_baseline_rgb=baseline,
        current_rgb=current,
        source_rgb=source,
        subject_mask=subject,
        face_mask=face,
    )
    assert clean.version == CANONICAL_HARD_GATE_VERSION
    assert clean.pass_gate
    dirty = current.copy()
    dirty[13:16, 13:16] = [0, 0, 0]
    dirty[13:16, 17:20] = [0, 0, 0]
    report = evaluate_canonical_hard_gate(
        adopted_baseline_rgb=baseline,
        current_rgb=dirty,
        source_rgb=source,
        subject_mask=subject,
        face_mask=face,
    )
    assert report.forbidden_face_detail_ratio > 0
    assert not report.forbidden_face_pass
    assert not report.pass_gate


def test_canonical_gate_rejects_empty_face_mask():
    import pytest
    source, baseline, current, subject, face = _images()
    face[:] = False
    with pytest.raises(ValueError):
        evaluate_canonical_hard_gate(
            adopted_baseline_rgb=baseline,
            current_rgb=current,
            source_rgb=source,
            subject_mask=subject,
            face_mask=face,
        )


def test_canonical_gate_report_serializes_missing_signatures():
    import json
    source, baseline, current, subject, face = _images()
    current[8:24, 8:24] = [240, 220, 200]
    report = evaluate_canonical_hard_gate(
        adopted_baseline_rgb=baseline,
        current_rgb=current,
        source_rgb=source,
        subject_mask=subject,
        face_mask=face,
    )
    payload = report.to_dict()
    assert report.missing_count == len(report.missing_signatures)
    assert isinstance(json.dumps(payload), str)
