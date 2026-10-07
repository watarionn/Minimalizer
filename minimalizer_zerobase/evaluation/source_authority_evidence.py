from __future__ import annotations

from dataclasses import dataclass

SA10_SOURCE_AUTHORITY_VERSION = "sa10.10-v1"


@dataclass(frozen=True)
class SourceAuthorityEvidence:
    expected_source_sha256: str
    actual_source_sha256: str
    provenance_gate_passed: bool
    provenance_artifact_count: int
    passed: bool
    version: str = SA10_SOURCE_AUTHORITY_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "status": "AVAILABLE",
            "passed": self.passed,
            "expected_source_sha256": self.expected_source_sha256,
            "actual_source_sha256": self.actual_source_sha256,
            "source_hash_match": self.expected_source_sha256 == self.actual_source_sha256,
            "provenance_gate_passed": self.provenance_gate_passed,
            "provenance_artifact_count": self.provenance_artifact_count,
        }


def build_source_authority_evidence(
    *,
    expected_source_sha256: str,
    actual_source_sha256: str,
    provenance_gate_passed: bool,
    provenance_artifact_count: int,
) -> SourceAuthorityEvidence:
    for name, value in (
        ("expected_source_sha256", expected_source_sha256),
        ("actual_source_sha256", actual_source_sha256),
    ):
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"{name} must be a SHA-256 hex string")
        try:
            int(value, 16)
        except ValueError as exc:
            raise ValueError(f"{name} must be hexadecimal") from exc
    if not isinstance(provenance_gate_passed, bool):
        raise ValueError("provenance_gate_passed must be bool")
    if isinstance(provenance_artifact_count, bool) or provenance_artifact_count < 1:
        raise ValueError("provenance_artifact_count must be positive")

    passed = bool(
        expected_source_sha256 == actual_source_sha256
        and provenance_gate_passed
    )
    return SourceAuthorityEvidence(
        expected_source_sha256=expected_source_sha256,
        actual_source_sha256=actual_source_sha256,
        provenance_gate_passed=provenance_gate_passed,
        provenance_artifact_count=int(provenance_artifact_count),
        passed=passed,
    )
