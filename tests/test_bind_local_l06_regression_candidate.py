import hashlib
import json
from pathlib import Path

import pytest

from tools.research.bind_local_l06_regression_candidate import (
    BROWSER_SCHEMA,
    SCHEMA,
    SUMMARY_SCHEMA,
    L06RegressionHold,
    audit_l06_regression_candidate,
)
from tools.research.local_completion_release_gate import EXPECTED_CANDIDATE_RECEIPT_SHA256


def _write(path: Path, value: dict) -> str:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary() -> dict:
    return {
        "schema": SUMMARY_SCHEMA,
        "phase": 14,
        "pass": True,
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "gates": {
            "approved18_production_regression": {"pass": True},
            "approved78_formal_migration": {"pass": True, "migration_gate_pass": True},
            "diagnostic2_zero_base_visual": {"pass": True},
        },
        "inputs": {
            "approved18": {"sha256": "1" * 64},
            "approved78": {"sha256": "2" * 64},
            "diagnostic2": {"sha256": "3" * 64},
        },
    }


def _browser() -> dict:
    return {
        "schema": BROWSER_SCHEMA,
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "browser_render_pass": True,
        "performance_pass": True,
    }


def _case(tmp_path: Path):
    summary_path = tmp_path / "summary.json"
    browser_path = tmp_path / "browser.json"
    summary_sha = _write(summary_path, _summary())
    browser_sha = _write(browser_path, _browser())
    binding = {
        "schema": SCHEMA,
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "source_free": True,
        "summary_sha256": summary_sha,
        "browser_performance_sha256": browser_sha,
    }
    return summary_path, browser_path, binding


def test_current_candidate_bound_regression_passes(tmp_path: Path):
    summary_path, browser_path, binding = _case(tmp_path)
    result = audit_l06_regression_candidate(
        summary=json.loads(summary_path.read_text()),
        browser=json.loads(browser_path.read_text()),
        binding=binding,
        summary_path=summary_path,
        browser_path=browser_path,
    )
    assert result["status"] == "PASS"
    assert result["release_authorized"] is False


def test_historical_summary_without_candidate_binding_is_rejected(tmp_path: Path):
    summary_path, browser_path, binding = _case(tmp_path)
    summary = _summary()
    summary.pop("candidate_receipt_sha256")
    with pytest.raises(L06RegressionHold, match="SUMMARY_CANDIDATE_BINDING_MISSING"):
        audit_l06_regression_candidate(
            summary=summary,
            browser=json.loads(browser_path.read_text()),
            binding=binding,
            summary_path=summary_path,
            browser_path=browser_path,
        )


def test_browser_candidate_mismatch_is_rejected(tmp_path: Path):
    summary_path, browser_path, binding = _case(tmp_path)
    browser = _browser()
    browser["candidate_receipt_sha256"] = "f" * 64
    with pytest.raises(L06RegressionHold, match="BROWSER_CANDIDATE_BINDING_MISMATCH"):
        audit_l06_regression_candidate(
            summary=json.loads(summary_path.read_text()),
            browser=browser,
            binding=binding,
            summary_path=summary_path,
            browser_path=browser_path,
        )


def test_binding_sha_mismatch_is_rejected(tmp_path: Path):
    summary_path, browser_path, binding = _case(tmp_path)
    binding["summary_sha256"] = "0" * 64
    with pytest.raises(L06RegressionHold, match="SUMMARY_SHA_MISMATCH"):
        audit_l06_regression_candidate(
            summary=json.loads(summary_path.read_text()),
            browser=json.loads(browser_path.read_text()),
            binding=binding,
            summary_path=summary_path,
            browser_path=browser_path,
        )
