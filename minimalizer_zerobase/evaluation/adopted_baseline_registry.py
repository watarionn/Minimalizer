from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

SA10_ADOPTED_BASELINE_VERSION = "sa10.12-v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _require_sha256(name: str, value: str) -> str:
    text = str(value)
    if not _SHA256_RE.fullmatch(text):
        raise ValueError(f"{name} must be lowercase SHA-256 hex")
    return text


@dataclass(frozen=True)
class BaselineAdoptionRecord:
    case_id: str
    source_sha256: str
    baseline_artifact_sha256: str
    baseline_origin: str
    baseline_artifact_id: str
    review_status: str
    reviewer: str
    review_evidence: tuple[str, ...]
    adoption_transaction_id: str
    immutable_record: bool
    evaluation_baseline_allowed: bool
    production_inference_allowed: bool
    candidate_self_reference_forbidden: bool
    version: str = SA10_ADOPTED_BASELINE_VERSION

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "BaselineAdoptionRecord":
        review_evidence = payload.get("review_evidence")
        if not isinstance(review_evidence, list) or not review_evidence:
            raise ValueError("review_evidence must be a non-empty list")
        record = cls(
            case_id=str(payload.get("case_id") or ""),
            source_sha256=_require_sha256(
                "source_sha256", str(payload.get("source_sha256") or "")
            ),
            baseline_artifact_sha256=_require_sha256(
                "baseline_artifact_sha256",
                str(payload.get("baseline_artifact_sha256") or ""),
            ),
            baseline_origin=str(payload.get("baseline_origin") or ""),
            baseline_artifact_id=str(payload.get("baseline_artifact_id") or ""),
            review_status=str(payload.get("review_status") or ""),
            reviewer=str(payload.get("reviewer") or ""),
            review_evidence=tuple(str(value) for value in review_evidence),
            adoption_transaction_id=str(
                payload.get("adoption_transaction_id") or ""
            ),
            immutable_record=bool(payload.get("immutable_record")),
            evaluation_baseline_allowed=bool(
                payload.get("evaluation_baseline_allowed")
            ),
            production_inference_allowed=bool(
                payload.get("production_inference_allowed")
            ),
            candidate_self_reference_forbidden=bool(
                payload.get("candidate_self_reference_forbidden")
            ),
            version=str(payload.get("version") or SA10_ADOPTED_BASELINE_VERSION),
        )
        record.validate()
        return record

    def validate(self) -> None:
        if self.version != SA10_ADOPTED_BASELINE_VERSION:
            raise ValueError("unsupported adopted-baseline record version")
        for name, value in (
            ("case_id", self.case_id),
            ("baseline_origin", self.baseline_origin),
            ("baseline_artifact_id", self.baseline_artifact_id),
            ("reviewer", self.reviewer),
            ("adoption_transaction_id", self.adoption_transaction_id),
        ):
            if not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if self.review_status != "ADOPTED":
            raise ValueError("review_status must be ADOPTED")
        if not all(value.strip() for value in self.review_evidence):
            raise ValueError("review_evidence entries must be non-empty")
        if not self.immutable_record:
            raise ValueError("adoption record must be immutable")
        if not self.evaluation_baseline_allowed:
            raise ValueError("adopted baseline must allow evaluation use")
        if self.production_inference_allowed:
            raise ValueError("adopted baseline cannot be a production inference input")
        if not self.candidate_self_reference_forbidden:
            raise ValueError("candidate self-reference prohibition is required")


@dataclass(frozen=True)
class AdoptedBaselineBinding:
    case_id: str
    adoption_transaction_id: str
    evaluation_transaction_id: str
    source_sha256: str
    baseline_artifact_sha256: str
    candidate_artifact_sha256: str
    baseline_origin: str
    baseline_artifact_id: str
    reviewer: str
    review_evidence: tuple[str, ...]
    candidate_bytes_equal_baseline: bool
    same_transaction: bool
    binding_passed: bool
    production_inference_allowed: bool = False
    version: str = SA10_ADOPTED_BASELINE_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "case_id": self.case_id,
            "adoption_transaction_id": self.adoption_transaction_id,
            "evaluation_transaction_id": self.evaluation_transaction_id,
            "source_sha256": self.source_sha256,
            "baseline_artifact_sha256": self.baseline_artifact_sha256,
            "candidate_artifact_sha256": self.candidate_artifact_sha256,
            "baseline_origin": self.baseline_origin,
            "baseline_artifact_id": self.baseline_artifact_id,
            "reviewer": self.reviewer,
            "review_evidence": list(self.review_evidence),
            "candidate_bytes_equal_baseline": self.candidate_bytes_equal_baseline,
            "same_transaction": self.same_transaction,
            "binding_passed": self.binding_passed,
            "production_inference_allowed": False,
            "candidate_self_reference_forbidden": True,
        }


def bind_adopted_baseline(
    record: BaselineAdoptionRecord,
    *,
    actual_source_sha256: str,
    actual_baseline_sha256: str,
    candidate_artifact_sha256: str,
    evaluation_transaction_id: str,
) -> AdoptedBaselineBinding:
    record.validate()
    actual_source = _require_sha256("actual_source_sha256", actual_source_sha256)
    actual_baseline = _require_sha256(
        "actual_baseline_sha256", actual_baseline_sha256
    )
    candidate = _require_sha256(
        "candidate_artifact_sha256", candidate_artifact_sha256
    )
    evaluation_transaction = str(evaluation_transaction_id).strip()
    if not evaluation_transaction:
        raise ValueError("evaluation_transaction_id must be non-empty")

    same_transaction = (
        evaluation_transaction == record.adoption_transaction_id
    )
    passed = bool(
        actual_source == record.source_sha256
        and actual_baseline == record.baseline_artifact_sha256
        and not same_transaction
    )
    return AdoptedBaselineBinding(
        case_id=record.case_id,
        adoption_transaction_id=record.adoption_transaction_id,
        evaluation_transaction_id=evaluation_transaction,
        source_sha256=actual_source,
        baseline_artifact_sha256=actual_baseline,
        candidate_artifact_sha256=candidate,
        baseline_origin=record.baseline_origin,
        baseline_artifact_id=record.baseline_artifact_id,
        reviewer=record.reviewer,
        review_evidence=record.review_evidence,
        candidate_bytes_equal_baseline=(candidate == actual_baseline),
        same_transaction=same_transaction,
        binding_passed=passed,
    )
