from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.run_zerobase_phase14_closure import build_closure


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _evidence(tmp_path: Path, *, diagnostic_pass: bool = True):
    diagnostic = _write(
        tmp_path / "diagnostic.json",
        {
            "pass": diagnostic_pass,
            "case_count": 2,
            "pass_count": 2 if diagnostic_pass else 1,
            "fail_count": 0 if diagnostic_pass else 1,
            "human_visual_pass_count": 2 if diagnostic_pass else 1,
            "determinism_pass_count": 2 if diagnostic_pass else 1,
            "minimum_scores": {},
            "maximum_penalties": {},
        },
    )
    approved18 = _write(
        tmp_path / "approved18.json",
        {
            "pass": True,
            "case_count": 18,
            "input_sha_pass_count": 18,
            "approved_sha_pass_count": 18,
            "structural_gate_pass_count": 18,
            "diagnostics": {},
        },
    )
    approved78 = _write(
        tmp_path / "approved78.json",
        {
            "pass": True,
            "replay_complete": True,
            "binding": {"reference_count": 78},
            "migration_gate_pass": True,
            "migration_gate": {"reasons": []},
            "calibration_diagnostic": {"gating": False},
        },
    )
    return diagnostic, approved18, approved78


def test_phase14_closure_authorizes_phase15_only_when_all_gates_pass(
    tmp_path: Path,
) -> None:
    diagnostic, approved18, approved78 = _evidence(tmp_path)

    result = build_closure(
        diagnostic2_path=diagnostic,
        approved18_path=approved18,
        approved78_path=approved78,
    )

    assert result["pass"] is True
    assert result["next_phase_authorized"] == 15
    assert all(item["pass"] for item in result["gates"].values())


def test_phase14_closure_fails_closed_on_any_failed_corpus_gate(
    tmp_path: Path,
) -> None:
    diagnostic, approved18, approved78 = _evidence(
        tmp_path,
        diagnostic_pass=False,
    )

    result = build_closure(
        diagnostic2_path=diagnostic,
        approved18_path=approved18,
        approved78_path=approved78,
    )

    assert result["pass"] is False
    assert result["next_phase_authorized"] is None
    assert result["gates"]["diagnostic2_zero_base_visual"]["pass"] is False


def test_phase14_closure_rejects_missing_evidence(tmp_path: Path) -> None:
    diagnostic, approved18, approved78 = _evidence(tmp_path)
    approved18.unlink()

    with pytest.raises(FileNotFoundError):
        build_closure(
            diagnostic2_path=diagnostic,
            approved18_path=approved18,
            approved78_path=approved78,
        )
