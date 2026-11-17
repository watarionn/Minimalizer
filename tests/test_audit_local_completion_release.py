import json
from pathlib import Path
import subprocess
import sys

from tools.research.audit_local_completion_release import audit_receipt_paths
from tools.research.local_completion_release_gate import (
    EXPECTED_CANDIDATE_RECEIPT_SHA256 as C,
    EXPECTED_PRODUCTION_WORKER_COMMIT as W,
)


def _payloads():
    return {
        "a": {
            "status": "PASS", "candidate_receipt_sha256": C,
            "observer_capabilities": [
                "arm", "instance_grouping", "occlusion_garment_body",
                "occlusion_outerwear_underlayer", "occlusion_sleeve_arm",
                "outerwear", "sleeve", "underlayer",
            ],
            "six_capabilities": True, "same_config_three_cases": True,
            "source_only_inference": True, "human_labels_used_for_inference": False,
            "unknown_preserved": True, "h04_pass": True, "h06_pass": True, "h08_pass": True,
        },
        "phase4": {
            "status": "PASS", "candidate_receipt_sha256": C,
            "independent_evaluator": True, "output_frozen_before_scoring": True,
            "semantic_review_complete": True, "unknown_not_negative": True,
            "source_alpha_bounds_pass": True, "owner_exclusivity_pass": True,
            "components4_pass": True, "components8_pass": True,
            "holes4_pass": True, "holes8_pass": True,
            "occlusion_and_critical_parts_pass": True,
        },
        "phase5": {
            "status": "PASS", "candidate_receipt_sha256": C,
            "exact_replay": True, "same_config_three_cases": True,
            "source_sha_match": True, "output_sha_match": True,
        },
        "l04": {
            "candidate_receipt_sha256": C, "L04_formal": "PASS", "Golden": "PASS",
            "production": "GO", "release_authorized": True,
            "triple_case_delivery_verified": True,
        },
        "l05": {"status": "PASS", "candidate_receipt_sha256": C, "production_worker_commit": W},
        "l07": {"status": "PASS", "candidate_receipt_sha256": C, "production_worker_commit": W},
        "acceptance": {
            "status": "PASS", "candidate_receipt_sha256": C, "production_worker_commit": W,
            "pc": True, "iphone_safari": True, "iphone_pwa": True, "png": True,
            "svg": True, "offline_recovery": True, "failure_paths": True,
            "fallback": True, "rollback": True,
        },
        "regression": {
            "status": "PASS", "candidate_receipt_sha256": C,
            "l06_golden_pass": True, "approved18_to_78_pass": True,
            "browser_render_pass": True, "performance_pass": True,
        },
        "preservation": {
            "status": "PASS", "candidate_receipt_sha256": C,
            "release_sha_bound": True, "artifact_sha_bound": True,
            "private_drive_saved": True, "private_drive_readback": True,
            "source_free_ledger": True,
        },
    }


def _write_receipts(tmp_path: Path, payloads):
    paths = {}
    for name, payload in payloads.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        paths[name] = path
    return paths


def test_all_receipts_are_audited_as_one_release(tmp_path):
    result = audit_receipt_paths(
        candidate_receipt_sha256=C,
        production_worker_commit=W,
        receipt_paths=_write_receipts(tmp_path, _payloads()),
        owner_action_required=False,
    )
    assert result["status"] == "PASS"
    assert result["release_authorized"] is True


def test_missing_receipt_is_fail_closed(tmp_path):
    paths = _write_receipts(tmp_path, _payloads())
    paths.pop("a")
    result = audit_receipt_paths(
        candidate_receipt_sha256=C,
        production_worker_commit=W,
        receipt_paths=paths,
        owner_action_required=False,
    )
    assert result["status"] == "HOLD"
    assert result["release_authorized"] is False
    assert "missing receipt path:a" in result["failures"]


def test_malformed_receipt_is_fail_closed(tmp_path):
    paths = _write_receipts(tmp_path, _payloads())
    paths["phase4"].write_text("not-json", encoding="utf-8")
    result = audit_receipt_paths(
        candidate_receipt_sha256=C,
        production_worker_commit=W,
        receipt_paths=paths,
        owner_action_required=False,
    )
    assert result["status"] == "HOLD"
    assert "phase4 receipt read failed:JSONDecodeError" in result["failures"]


def test_direct_cmd_entrypoint_is_importable():
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "tools" / "research" / "audit_local_completion_release.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Audit MinimalizerLocal completion" in result.stdout
    assert "ModuleNotFoundError" not in result.stderr
