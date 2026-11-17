"""Bind an independent Phase4 receipt to the adopted candidate receipt.

This source-free adapter does not infer a candidate binding from filenames,
review text, or private artifacts.  A separate manifest must explicitly map
the adopted receipt SHA to the three source/candidate array SHAs.  Missing or
inconsistent mapping fails closed and never authorizes release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.research.local_completion_release_gate import (  # noqa: E402
    EXPECTED_CANDIDATE_RECEIPT_SHA256,
)


SCHEMA = "minimalizer/local-l02/phase4-candidate-binding/v1"
PHASE4_SCHEMA = "minimalizer/l02/phase4-independent-review/v1"
CASES = ("H04", "H06", "H08")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class Phase4CandidateBindingHold(ValueError):
    """The Phase4 receipt cannot be bound to the adopted candidate."""


def _sha(value: object, field: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise Phase4CandidateBindingHold(f"INVALID_SHA:{field}")
    return value


def _object(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise Phase4CandidateBindingHold(f"INVALID_OBJECT:{field}")
    return value


def _load(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Phase4CandidateBindingHold(f"READ_FAILED:{label}:{type(exc).__name__}") from exc
    return _object(value, label)


def _audit_binding_manifest(binding: Mapping[str, Any]) -> dict[str, Mapping[str, str]]:
    if binding.get("schema") != SCHEMA:
        raise Phase4CandidateBindingHold("INVALID_BINDING_SCHEMA")
    if binding.get("candidate_receipt_sha256") != EXPECTED_CANDIDATE_RECEIPT_SHA256:
        raise Phase4CandidateBindingHold("CANDIDATE_RECEIPT_MISMATCH")
    if binding.get("source_only") is not True:
        raise Phase4CandidateBindingHold("NON_SOURCE_ONLY_BINDING")
    if binding.get("human_labels_used_for_inference") is not False:
        raise Phase4CandidateBindingHold("HUMAN_LABELS_IN_INFERENCE_INPUT")
    if binding.get("same_config_three_cases") != list(CASES):
        raise Phase4CandidateBindingHold("THREE_CASE_SAME_CONFIG_NOT_DECLARED")
    cases = _object(binding.get("cases"), "cases")
    if set(cases) != set(CASES):
        raise Phase4CandidateBindingHold("CASE_SET_MISMATCH")
    result: dict[str, Mapping[str, str]] = {}
    for case in CASES:
        entry = _object(cases[case], f"cases.{case}")
        result[case] = {
            "source_sha256": _sha(entry.get("source_sha256"), f"cases.{case}.source_sha256"),
            "candidate_sha256": _sha(entry.get("candidate_sha256"), f"cases.{case}.candidate_sha256"),
        }
    return result


def audit_phase4_candidate_binding(
    phase4: Mapping[str, Any], binding: Mapping[str, Any]
) -> dict[str, object]:
    """Return PASS only when the explicit three-case mapping matches Phase4."""
    mapped_cases = _audit_binding_manifest(binding)
    if phase4.get("schema") != PHASE4_SCHEMA:
        raise Phase4CandidateBindingHold("INVALID_PHASE4_SCHEMA")
    if phase4.get("phase4") != "PASS":
        raise Phase4CandidateBindingHold("PHASE4_NOT_PASS")
    for field in (
        "unseen_data",
        "labels_unavailable_before_inference",
        "evaluator_independent",
        "semantic_review_complete",
        "output_frozen_before_scoring",
    ):
        if phase4.get(field) is not True:
            raise Phase4CandidateBindingHold(f"PHASE4_{field.upper()}_REQUIRED")
    if phase4.get("review_json_used_in_inference") is not False:
        raise Phase4CandidateBindingHold("PHASE4_REVIEW_JSON_IN_INFERENCE")
    cases = _object(phase4.get("cases"), "phase4.cases")
    if set(cases) != set(CASES):
        raise Phase4CandidateBindingHold("PHASE4_CASE_SET_MISMATCH")
    for case in CASES:
        actual = _object(cases[case], f"phase4.cases.{case}")
        if _sha(actual.get("source_sha256"), f"phase4.cases.{case}.source_sha256") != mapped_cases[case]["source_sha256"]:
            raise Phase4CandidateBindingHold(f"SOURCE_SHA_MISMATCH:{case}")
        if _sha(actual.get("candidate_sha256"), f"phase4.cases.{case}.candidate_sha256") != mapped_cases[case]["candidate_sha256"]:
            raise Phase4CandidateBindingHold(f"CANDIDATE_ARRAY_SHA_MISMATCH:{case}")
        for field in (
            "correct_garment_preserved",
            "wrong_owner_removed_only_where_justified",
            "sleeve_recovery_owner_exclusive",
            "occlusion_and_critical_parts_preserved",
            "unknown_not_negative",
        ):
            if actual.get(field) is not True:
                raise Phase4CandidateBindingHold(f"PHASE4_{case}_{field.upper()}_REQUIRED")
    return {
        "schema": "minimalizer/local-l02/phase4-candidate-binding-audit/v1",
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "cases": mapped_cases,
        "phase4_verified": True,
        "independent_evaluator": True,
        "output_frozen_before_scoring": True,
        "source_only": True,
        "human_labels_used_for_inference": False,
        "private_artifacts_opened": False,
        "release_authorized": False,
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Bind independent Phase4 to the adopted candidate")
    parser.add_argument("--phase4", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        phase4 = _load(args.phase4, "phase4")
        binding = _load(args.binding, "binding")
        result = audit_phase4_candidate_binding(phase4, binding)
        exit_code = 0
    except Phase4CandidateBindingHold as exc:
        result = {
            "schema": "minimalizer/local-l02/phase4-candidate-binding-audit/v1",
            "status": "HOLD",
            "failures": (str(exc),),
            "private_artifacts_opened": False,
            "release_authorized": False,
        }
        exit_code = 2
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(_cli())
