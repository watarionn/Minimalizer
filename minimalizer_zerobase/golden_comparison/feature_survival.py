from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .semantic_manifest import validate_semantic_manifest


VALID_STATES = {"present", "absent", "unknown"}


class FeatureSurvivalError(RuntimeError):
    pass


@dataclass(frozen=True)
class FeatureEvidence:
    state: str
    source: str
    confidence: float | None = None

    def __post_init__(self) -> None:
        if self.state not in VALID_STATES:
            raise FeatureSurvivalError(f"invalid feature evidence state: {self.state}")
        if not self.source:
            raise FeatureSurvivalError("feature evidence source is required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise FeatureSurvivalError("feature evidence confidence must be within [0, 1]")


def _coerce_evidence(feature_id: str, raw: Any) -> FeatureEvidence:
    if isinstance(raw, FeatureEvidence):
        return raw
    if not isinstance(raw, Mapping):
        raise FeatureSurvivalError(f"{feature_id}: evidence must be an object")
    return FeatureEvidence(
        state=raw.get("state", "unknown"),
        source=raw.get("source", ""),
        confidence=raw.get("confidence"),
    )


def evaluate_feature_survival(
    manifest: dict[str, Any],
    evidence: Mapping[str, Any],
    *,
    perceptual_score: float | None = None,
) -> dict[str, Any]:
    validate_semantic_manifest(manifest)
    feature_ids = {feature["id"] for feature in manifest["features"]}
    unknown_evidence = set(evidence) - feature_ids
    if unknown_evidence:
        raise FeatureSurvivalError(
            "evidence references unknown feature: " + ", ".join(sorted(unknown_evidence))
        )

    rows: list[dict[str, Any]] = []
    hard_failures: list[dict[str, str]] = []
    for feature in manifest["features"]:
        feature_id = feature["id"]
        observed = _coerce_evidence(
            feature_id,
            evidence.get(feature_id, {"state": "unknown", "source": "missing"}),
        )
        disposition = feature["disposition"]

        if disposition == "required" and observed.state != "present":
            hard_failures.append(
                {"feature_id": feature_id, "reason": f"required_feature_{observed.state}"}
            )
        elif disposition == "forbidden" and observed.state != "absent":
            hard_failures.append(
                {"feature_id": feature_id, "reason": f"forbidden_feature_{observed.state}"}
            )

        rows.append(
            {
                "feature_id": feature_id,
                "disposition": disposition,
                "state": observed.state,
                "source": observed.source,
                "confidence": observed.confidence,
            }
        )

    return {
        "schema_version": "1.0",
        "case_id": manifest["case_id"],
        "gate": "FAIL" if hard_failures else "PASS",
        "hard_failures": hard_failures,
        "feature_evidence": rows,
        "perceptual_score": perceptual_score,
        "perceptual_score_can_override_hard_fail": False,
    }
