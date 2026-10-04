from __future__ import annotations

from typing import Any, Mapping


DIMENSIONS = (
    "semantic_survival",
    "recognizability",
    "geometry_abstraction",
    "palette_role_preservation",
    "composition_negative_space",
    "primitive_economy",
    "orphan_contour_penalty",
    "feature_local_evidence",
)


class GoldenGapError(RuntimeError):
    pass


def _score(name: str, value: Any) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise GoldenGapError(f"{name}: score must be numeric")
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise GoldenGapError(f"{name}: score must be within [0, 1]")
    return value


def evaluate_golden_gap(
    *,
    case_id: str,
    feature_survival_report: Mapping[str, Any],
    dimension_scores: Mapping[str, Any],
    feature_local_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if feature_survival_report.get("case_id") != case_id:
        raise GoldenGapError("feature survival case_id mismatch")
    missing = set(DIMENSIONS) - set(dimension_scores)
    extra = set(dimension_scores) - set(DIMENSIONS)
    if missing:
        raise GoldenGapError("missing Golden Gap dimensions: " + ", ".join(sorted(missing)))
    if extra:
        raise GoldenGapError("unknown Golden Gap dimensions: " + ", ".join(sorted(extra)))

    scores = {name: _score(name, dimension_scores[name]) for name in DIMENSIONS}
    hard_gate = feature_survival_report.get("gate")
    if hard_gate not in {"PASS", "FAIL"}:
        raise GoldenGapError("feature survival gate must be PASS or FAIL")

    local_rows: list[dict[str, Any]] = []
    for feature_id, raw in sorted((feature_local_evidence or {}).items()):
        if not isinstance(raw, Mapping):
            raise GoldenGapError(f"{feature_id}: feature-local evidence must be an object")
        score = _score(f"{feature_id}.score", raw.get("score"))
        local_rows.append({
            "feature_id": feature_id,
            "score": score,
            "source": raw.get("source", "unknown"),
            "authoritative": False,
        })

    diagnostic_mean = sum(scores.values()) / len(scores)
    return {
        "schema_version": "1.0",
        "case_id": case_id,
        "gate": "FAIL" if hard_gate == "FAIL" else "PASS",
        "hard_gate": hard_gate,
        "hard_failures": list(feature_survival_report.get("hard_failures", [])),
        "dimensions": scores,
        "diagnostic_mean": diagnostic_mean,
        "diagnostic_mean_can_override_hard_fail": False,
        "feature_local_evidence": local_rows,
        "feature_local_evidence_is_authority": False,
    }


def compare_golden_gap(
    baseline: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    if baseline.get("case_id") != candidate.get("case_id"):
        raise GoldenGapError("cannot compare different Golden cases")
    baseline_dims = baseline.get("dimensions", {})
    candidate_dims = candidate.get("dimensions", {})
    if set(baseline_dims) != set(DIMENSIONS) or set(candidate_dims) != set(DIMENSIONS):
        raise GoldenGapError("comparison requires complete dimension reports")
    deltas = {
        name: float(candidate_dims[name]) - float(baseline_dims[name])
        for name in DIMENSIONS
    }
    regressions = [name for name, delta in deltas.items() if delta < 0.0]
    improvements = [name for name, delta in deltas.items() if delta > 0.0]
    return {
        "schema_version": "1.0",
        "case_id": baseline["case_id"],
        "baseline_gate": baseline.get("gate"),
        "candidate_gate": candidate.get("gate"),
        "candidate_admissible": candidate.get("gate") == "PASS",
        "dimension_deltas": deltas,
        "improvements": improvements,
        "regressions": regressions,
    }
