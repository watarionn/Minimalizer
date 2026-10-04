from __future__ import annotations

import pytest

from minimalizer_zerobase.golden_comparison.blind_generalization import (
    BlindGeneralizationError,
    evaluate_blind_generalization,
)


def _cases() -> list[dict]:
    return [
        {"case_id": "blind_a", "has_golden": False, "hard_gate": "PASS", "improvements": ["geometry_abstraction"], "regressions": []},
        {"case_id": "blind_b", "has_golden": False, "hard_gate": "PASS", "improvements": ["primitive_economy"], "regressions": []},
        {"case_id": "blind_c", "has_golden": False, "hard_gate": "PASS", "improvements": ["recognizability"], "regressions": []},
    ]


def test_adopt_requires_every_blind_case_to_improve_without_regression() -> None:
    report = evaluate_blind_generalization(_cases(), rules_frozen=True, production_integration_present=True)
    assert report["decision"] == "ADOPT"


def test_missing_production_integration_is_hold_not_false_pass() -> None:
    report = evaluate_blind_generalization(_cases(), rules_frozen=True, production_integration_present=False)
    assert report["decision"] == "HOLD"
    assert report["reason"] == "production_integration_not_yet_present"


def test_one_hard_fail_rejects_whole_adoption() -> None:
    cases = _cases()
    cases[1]["hard_gate"] = "FAIL"
    report = evaluate_blind_generalization(cases, rules_frozen=True, production_integration_present=True)
    assert report["decision"] == "REJECT"
    assert report["failed_cases"] == ["blind_b"]


def test_one_regressed_character_cannot_be_hidden_by_other_improvements() -> None:
    cases = _cases()
    cases[2]["regressions"] = ["palette_role_preservation"]
    report = evaluate_blind_generalization(cases, rules_frozen=True, production_integration_present=True)
    assert report["decision"] == "REJECT"
    assert report["aggregate_score_can_hide_case_failure"] is False


def test_every_case_must_demonstrate_improvement() -> None:
    cases = _cases()
    cases[0]["improvements"] = []
    report = evaluate_blind_generalization(cases, rules_frozen=True, production_integration_present=True)
    assert report["decision"] == "REJECT"


def test_rules_must_be_frozen_before_looking_at_blind_results() -> None:
    with pytest.raises(BlindGeneralizationError, match="rules must be frozen"):
        evaluate_blind_generalization(_cases(), rules_frozen=False, production_integration_present=True)


def test_blind_case_cannot_have_golden() -> None:
    cases = _cases()
    cases[0]["has_golden"] = True
    with pytest.raises(BlindGeneralizationError, match="must not contain a Golden"):
        evaluate_blind_generalization(cases, rules_frozen=True, production_integration_present=True)


def test_requires_multiple_unseen_characters() -> None:
    with pytest.raises(BlindGeneralizationError, match="at least three"):
        evaluate_blind_generalization(_cases()[:2], rules_frozen=True, production_integration_present=True)


def test_duplicate_case_id_fails_closed() -> None:
    cases = _cases()
    cases[2]["case_id"] = "blind_a"
    with pytest.raises(BlindGeneralizationError, match="duplicate"):
        evaluate_blind_generalization(cases, rules_frozen=True, production_integration_present=True)
