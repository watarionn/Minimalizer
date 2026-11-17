"""Bind L06 regression evidence to the adopted Minimalizer candidate.

This adapter consumes JSON receipts only.  It does not open images, SVGs,
NPZs, screenshots, or private Drive content.  A historical Phase14 summary
without an explicit candidate SHA is rejected rather than being promoted to
the current release.
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


SCHEMA = "minimalizer/local-l06/regression-binding/v1"
SUMMARY_SCHEMA = "minimalizer/local-l06/phase14-summary/v1"
BROWSER_SCHEMA = "minimalizer/local-l06/browser-performance/v1"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class L06RegressionHold(ValueError):
    """The L06 evidence cannot be bound to the adopted candidate."""


def _object(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise L06RegressionHold(f"INVALID_OBJECT:{field}")
    return value


def _sha(value: object, field: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise L06RegressionHold(f"INVALID_SHA:{field}")
    return value


def _load(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise L06RegressionHold(f"READ_FAILED:{label}:{type(exc).__name__}") from exc
    return _object(value, label)


def _file_sha(path: Path, label: str) -> str:
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, UnicodeError) as exc:
        raise L06RegressionHold(f"READ_FAILED:{label}:{type(exc).__name__}") from exc
    return digest


def _require_pass(value: object, field: str) -> None:
    if value is not True:
        raise L06RegressionHold(f"{field}_REQUIRED")


def _audit_summary(summary: Mapping[str, Any]) -> None:
    is_current_schema = summary.get("schema") == SUMMARY_SCHEMA
    is_legacy_phase14 = summary.get("schema_version") == "1.0" and summary.get("phase") == 14
    if not (is_current_schema or is_legacy_phase14):
        raise L06RegressionHold("INVALID_SUMMARY_SCHEMA")
    if summary.get("phase") != 14 or summary.get("pass") is not True:
        raise L06RegressionHold("PHASE14_NOT_PASS")
    if summary.get("candidate_receipt_sha256") != EXPECTED_CANDIDATE_RECEIPT_SHA256:
        raise L06RegressionHold("SUMMARY_CANDIDATE_BINDING_MISSING_OR_MISMATCH")
    gates = _object(summary.get("gates"), "summary.gates")
    approved18 = _object(gates.get("approved18_production_regression"), "approved18")
    approved78 = _object(gates.get("approved78_formal_migration"), "approved78")
    diagnostic2 = _object(gates.get("diagnostic2_zero_base_visual"), "diagnostic2")
    _require_pass(approved18.get("pass"), "APPROVED18")
    _require_pass(approved78.get("pass"), "APPROVED78")
    _require_pass(approved78.get("migration_gate_pass"), "APPROVED78_MIGRATION")
    _require_pass(diagnostic2.get("pass"), "DIAGNOSTIC2")
    inputs = _object(summary.get("inputs"), "summary.inputs")
    for name in ("approved18", "approved78", "diagnostic2"):
        entry = _object(inputs.get(name), f"summary.inputs.{name}")
        _sha(entry.get("sha256"), f"summary.inputs.{name}.sha256")


def _audit_browser(browser: Mapping[str, Any]) -> None:
    if browser.get("schema") != BROWSER_SCHEMA:
        raise L06RegressionHold("INVALID_BROWSER_PERFORMANCE_SCHEMA")
    if browser.get("candidate_receipt_sha256") != EXPECTED_CANDIDATE_RECEIPT_SHA256:
        raise L06RegressionHold("BROWSER_CANDIDATE_BINDING_MISMATCH")
    _require_pass(browser.get("browser_render_pass"), "BROWSER_RENDER")
    _require_pass(browser.get("performance_pass"), "PERFORMANCE")


def audit_l06_regression_candidate(
    *, summary: Mapping[str, Any], browser: Mapping[str, Any], binding: Mapping[str, Any],
    summary_path: Path, browser_path: Path,
) -> dict[str, object]:
    """Return a candidate-bound L06 receipt, or raise a fail-closed hold."""
    if binding.get("schema") != SCHEMA:
        raise L06RegressionHold("INVALID_BINDING_SCHEMA")
    if binding.get("candidate_receipt_sha256") != EXPECTED_CANDIDATE_RECEIPT_SHA256:
        raise L06RegressionHold("CANDIDATE_RECEIPT_MISMATCH")
    if binding.get("source_free") is not True:
        raise L06RegressionHold("NON_SOURCE_FREE_BINDING")
    _audit_summary(summary)
    _audit_browser(browser)
    if _file_sha(summary_path, "summary") != _sha(binding.get("summary_sha256"), "summary_sha256"):
        raise L06RegressionHold("SUMMARY_SHA_MISMATCH")
    if _file_sha(browser_path, "browser_performance") != _sha(
        binding.get("browser_performance_sha256"), "browser_performance_sha256"
    ):
        raise L06RegressionHold("BROWSER_PERFORMANCE_SHA_MISMATCH")
    return {
        "schema": "minimalizer/local-l06/regression/v1",
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "l06_golden_pass": True,
        "approved18_to_78_pass": True,
        "browser_render_pass": True,
        "performance_pass": True,
        "phase14_summary_sha256": binding["summary_sha256"],
        "browser_performance_sha256": binding["browser_performance_sha256"],
        "source_free": True,
        "private_artifacts_opened": False,
        "release_authorized": False,
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Bind L06 regression to the adopted candidate")
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--browser-performance", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        summary = _load(args.summary, "summary")
        browser = _load(args.browser_performance, "browser_performance")
        binding = _load(args.binding, "binding")
        result = audit_l06_regression_candidate(
            summary=summary,
            browser=browser,
            binding=binding,
            summary_path=args.summary,
            browser_path=args.browser_performance,
        )
        exit_code = 0
    except L06RegressionHold as exc:
        result = {
            "schema": "minimalizer/local-l06/regression/v1",
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
