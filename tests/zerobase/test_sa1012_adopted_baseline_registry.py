from __future__ import annotations

import pytest

from minimalizer_zerobase.evaluation.adopted_baseline_registry import (
    BaselineAdoptionRecord,
    bind_adopted_baseline,
)


def _record() -> BaselineAdoptionRecord:
    return BaselineAdoptionRecord.from_mapping({
        "version": "sa10.12-v1",
        "case_id": "case-a",
        "source_sha256": "a" * 64,
        "baseline_artifact_sha256": "b" * 64,
        "baseline_origin": "reviewed-phase12-output",
        "baseline_artifact_id": "drive-file-123",
        "review_status": "ADOPTED",
        "reviewer": "Rinka",
        "review_evidence": ["docs/review.md", "drive:drive-file-123"],
        "adoption_transaction_id": "adoption-tx-1",
        "immutable_record": True,
        "evaluation_baseline_allowed": True,
        "production_inference_allowed": False,
        "candidate_self_reference_forbidden": True,
    })


def test_separate_evaluation_transaction_may_bind_identical_fresh_bytes():
    record = _record()
    binding = bind_adopted_baseline(
        record,
        actual_source_sha256="a" * 64,
        actual_baseline_sha256="b" * 64,
        candidate_artifact_sha256="b" * 64,
        evaluation_transaction_id="evaluation-tx-2",
    )
    assert binding.binding_passed is True
    assert binding.candidate_bytes_equal_baseline is True
    assert binding.same_transaction is False
    assert binding.production_inference_allowed is False


def test_same_transaction_self_reference_fails_closed():
    record = _record()
    binding = bind_adopted_baseline(
        record,
        actual_source_sha256="a" * 64,
        actual_baseline_sha256="b" * 64,
        candidate_artifact_sha256="b" * 64,
        evaluation_transaction_id="adoption-tx-1",
    )
    assert binding.binding_passed is False
    assert binding.same_transaction is True


@pytest.mark.parametrize(
    "field,value",
    [
        ("review_status", "PASS"),
        ("immutable_record", False),
        ("evaluation_baseline_allowed", False),
        ("production_inference_allowed", True),
        ("candidate_self_reference_forbidden", False),
    ],
)
def test_invalid_adoption_boundary_is_rejected(field, value):
    payload = {
        "version": "sa10.12-v1",
        "case_id": "case-a",
        "source_sha256": "a" * 64,
        "baseline_artifact_sha256": "b" * 64,
        "baseline_origin": "reviewed-phase12-output",
        "baseline_artifact_id": "drive-file-123",
        "review_status": "ADOPTED",
        "reviewer": "Rinka",
        "review_evidence": ["docs/review.md"],
        "adoption_transaction_id": "adoption-tx-1",
        "immutable_record": True,
        "evaluation_baseline_allowed": True,
        "production_inference_allowed": False,
        "candidate_self_reference_forbidden": True,
    }
    payload[field] = value
    with pytest.raises(ValueError):
        BaselineAdoptionRecord.from_mapping(payload)


def test_hash_mismatch_fails_binding_without_rewriting_record():
    record = _record()
    binding = bind_adopted_baseline(
        record,
        actual_source_sha256="c" * 64,
        actual_baseline_sha256="b" * 64,
        candidate_artifact_sha256="d" * 64,
        evaluation_transaction_id="evaluation-tx-2",
    )
    assert binding.binding_passed is False
    assert record.source_sha256 == "a" * 64
