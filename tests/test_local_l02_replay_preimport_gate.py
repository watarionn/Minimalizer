"""Source-free regression: no executable L02 stage import before provenance gates."""
from __future__ import annotations

import ast
import builtins
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "tools" / "research"
sys.path.insert(0, str(RESEARCH))

import local_l02_canonical_strict_signed_replay as runner  # noqa: E402

EXECUTABLE_STAGES = {
    "local_l02_no_merge_signed_replay",
    "local_l02_composed_dual_contact_shadow",
    "local_l02_enclosed_class32_shadow",
}


def test_replay_stages_are_not_top_level_imports():
    tree = ast.parse((RESEARCH / "local_l02_canonical_strict_signed_replay.py").read_text())
    top_level = [
        node.module for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module in EXECUTABLE_STAGES
    ]
    assert top_level == []
    replay = next(node for node in tree.body
                  if isinstance(node, ast.FunctionDef) and node.name == "replay")
    verify_line = next(node.lineno for node in ast.walk(replay)
                       if isinstance(node, ast.Call)
                       and isinstance(node.func, ast.Name)
                       and node.func.id == "verify_pr_replay_lineage")
    wrapper_line = next(node.lineno for node in replay.body
                        if isinstance(node, ast.If)
                        and any(isinstance(x, ast.Name) and x.id == "PINNED_GUARDED_WRAPPER_SHA256"
                                for x in ast.walk(node.test)))
    stage_lines = [node.lineno for node in ast.walk(replay)
                   if isinstance(node, ast.ImportFrom) and node.module in EXECUTABLE_STAGES]
    assert len(stage_lines) == len(EXECUTABLE_STAGES)
    assert verify_line < wrapper_line < min(stage_lines)


@pytest.mark.parametrize("failure", ["lineage", "wrapper"])
def test_failure_before_stage_import_or_private_archive_read(monkeypatch, tmp_path, failure):
    original_import = builtins.__import__
    attempted = []

    def trace_import(name, *args, **kwargs):
        if name in EXECUTABLE_STAGES:
            attempted.append(name)
        return original_import(name, *args, **kwargs)

    if failure == "lineage":
        def reject_lineage():
            raise ValueError("SYNTHETIC_LINEAGE_HOLD")
        monkeypatch.setattr(runner, "verify_pr_replay_lineage", reject_lineage)
        expected = "SYNTHETIC_LINEAGE_HOLD"
    else:
        monkeypatch.setattr(runner, "verify_pr_replay_lineage",
                            lambda: {"verified_dependency_blobs": 23})
        monkeypatch.setattr(runner, "PINNED_GUARDED_WRAPPER_SHA256", "0" * 64)
        expected = "GUARDED_STAGING_WRAPPER_SHA_MISMATCH"

    monkeypatch.setattr(builtins, "__import__", trace_import)
    with pytest.raises(ValueError, match=expected):
        runner.replay(tmp_path, "H06")
    assert attempted == []
    assert list(tmp_path.iterdir()) == []
