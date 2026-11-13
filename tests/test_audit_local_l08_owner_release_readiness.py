import json
from pathlib import Path

import pytest

from tools.research.audit_local_l08_owner_release_readiness import (
    L08Hold,
    audit_owner_release_readiness,
)


COMMIT = "c68dc17bdc2bd3b0ba0841b7108177553891913c"
SHA = "a" * 64


def _write(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _files(tmp_path: Path) -> tuple[Path, Path, Path]:
    a = _write(tmp_path / "a.json", {
        "schema": "minimalizer/local-l04/independent-visual-delta-review-receipt/v1",
        "receipt_created": True,
        "candidate_receipt_sha256": SHA,
        "review_readback": {
            "review_gate": "PASS", "L04_formal": "PASS", "Golden": "PASS",
            "production": "NO_GO", "release_authorized": False,
            "review_binding_receipt_sha256": SHA,
            "candidate_numerical_audit": "PASS", "b_delivery_audit": "PASS",
        },
        "L04_formal": "PASS", "Golden": "PASS", "production": "NO_GO",
        "release_authorized": False,
    })
    pc = _write(tmp_path / "pc.json", {
        "schema": "minimalizer/local-l05/owner-run-receipt/v1",
        "transport": "private_https", "production": True, "device": "pc",
        "owner_identity_verified": True, "origin_verified": True, "tailnet_verified": True,
        "health": {"status": 200, "worker": "local-compute-v1", "ready": True},
        "success": [{"route": "v2", "status": 200, "content_type": "image/png",
                     "input_sha256": SHA, "output_sha256": SHA,
                     "input_readback": True, "output_readback": True}],
        "failures": {"invalid_type": {"status": 415}, "busy": {"status": 429, "retry_after": "2"},
                     "unavailable": {"status": 503}},
        "readback": {"input_hashes": True, "output_hashes": True,
                      "failure_paths": True, "device_file_readback": True},
    })
    iphone = _write(tmp_path / "iphone.json", {
        "schema": "minimalizer/local-l05-l07/iphone-acceptance/v1",
        "production_commit": COMMIT, "transport": "private_https", "device": "iphone",
        "owner_attestation": True,
        "safari": {"png_result_visible": True, "zerobase2_success_visible": True, "evidence_sha256": SHA},
        "pwa": {"png_result_visible": True, "zerobase2_success_visible": True, "evidence_sha256": SHA},
        "offline_restore": {"airplane_mode_round_trip_passed": True},
        "fallback": {"zerobase2_503_visible": True, "local_v2_success_visible": True, "evidence_sha256": SHA},
        "private_drive_readback": True,
    })
    return a, pc, iphone


def test_owner_release_readiness_passes_without_authorizing_release(tmp_path: Path) -> None:
    a, pc, iphone = _files(tmp_path)
    result = audit_owner_release_readiness(a, pc, iphone, production_commit=COMMIT)
    assert result["ready_for_owner_release"] is True
    assert result["production"] == "NO_GO"
    assert result["release_authorized"] is False
    assert result["owner_action_required"] is True


def test_owner_release_readiness_rejects_wrong_current_production_commit(tmp_path: Path) -> None:
    a, pc, iphone = _files(tmp_path)
    with pytest.raises(L08Hold, match="IPHONE_PRODUCTION_COMMIT_MISMATCH"):
        audit_owner_release_readiness(a, pc, iphone, production_commit="b" * 40)


def test_owner_release_readiness_rejects_a_release_override(tmp_path: Path) -> None:
    a, pc, iphone = _files(tmp_path)
    value = json.loads(a.read_text(encoding="utf-8"))
    value["release_authorized"] = True
    _write(a, value)
    with pytest.raises(L08Hold, match="A_RELEASE_BOUNDARY_CHANGED"):
        audit_owner_release_readiness(a, pc, iphone, production_commit=COMMIT)
