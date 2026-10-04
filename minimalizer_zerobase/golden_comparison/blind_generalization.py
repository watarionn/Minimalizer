from __future__ import annotations

from typing import Any, Mapping


class BlindGeneralizationError(RuntimeError):
    pass


def evaluate_blind_generalization(
    cases: list[Mapping[str, Any]],
    *,
    rules_frozen: bool,
    production_integration_present: bool,
) -> dict[str, Any]:
    if not rules_frozen:
        raise BlindGeneralizationError("G2-G7 rules must be frozen before blind evaluation")
    if len(cases) < 3:
        raise BlindGeneralizationError("blind gate requires at least three unseen characters")

    ids: set[str] = set()
    rows: list[dict[str, Any]] = []
    failed: list[str] = []
    regressed: list[str] = []
    improved: list[str] = []

    for case in cases:
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise BlindGeneralizationError("every blind case requires a case_id")
        if case_id in ids:
            raise BlindGeneralizationError(f"duplicate blind case_id: {case_id}")
        ids.add(case_id)
        if case.get("has_golden"):
            raise BlindGeneralizationError(f"{case_id}: blind case must not contain a Golden image")
        hard_gate = case.get("hard_gate")
        if hard_gate not in {"PASS", "FAIL"}:
            raise BlindGeneralizationError(f"{case_id}: hard_gate must be PASS or FAIL")
        regressions = list(case.get("regressions", []))
        improvements = list(case.get("improvements", []))
        if hard_gate == "FAIL":
            failed.append(case_id)
        if regressions:
            regressed.append(case_id)
        if improvements:
            improved.append(case_id)
        rows.append({
            "case_id": case_id,
            "hard_gate": hard_gate,
            "improvements": improvements,
            "regressions": regressions,
        })

    all_hard_pass = not failed
    no_case_regressions = not regressed
    demonstrated_general_improvement = len(improved) == len(cases)
    adopt = (
        production_integration_present
        and all_hard_pass
        and no_case_regressions
        and demonstrated_general_improvement
    )
    if adopt:
        decision = "ADOPT"
        reason = "blind_generalization_pass"
    elif not production_integration_present:
        decision = "HOLD"
        reason = "production_integration_not_yet_present"
    else:
        decision = "REJECT"
        reason = "blind_generalization_failed"

    return {
        "schema_version": "1.0",
        "rules_frozen": True,
        "case_count": len(cases),
        "production_integration_present": production_integration_present,
        "cases": rows,
        "failed_cases": failed,
        "regressed_cases": regressed,
        "improved_cases": improved,
        "all_hard_pass": all_hard_pass,
        "no_case_regressions": no_case_regressions,
        "demonstrated_general_improvement": demonstrated_general_improvement,
        "decision": decision,
        "reason": reason,
        "aggregate_score_can_hide_case_failure": False,
    }
