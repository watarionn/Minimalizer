from __future__ import annotations

import hashlib
import json

import pytest

from tools.research.audit_local_l05_current_worker_binding import (
    BINDING_SCHEMA,
    CurrentWorkerBindingHold,
    audit_current_worker_binding,
)
from tools.research.local_completion_release_gate import (
    EXPECTED_CANDIDATE_RECEIPT_SHA256 as CANDIDATE,
    EXPECTED_PRODUCTION_WORKER_COMMIT as WORKER,
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _pc_receipt():
    return {
        "schema": "minimalizer/local-l05/owner-run-receipt/v1",
        "transport": "private_https",
        "production": True,
        "device": "pc",
        "owner_identity_verified": True,
        "origin_verified": True,
        "tailnet_verified": True,
        "health": {"status": 200, "worker": "local-compute-v1", "ready": True},
        "success": [
            {
                "route": "zerobase2", "status": 200, "content_type": "image/png",
                "input_sha256": _sha("input"), "output_sha256": _sha("best"),
                "input_readback": True, "output_readback": True,
            },
            {
                "route": "v2", "status": 200, "content_type": "image/png",
                "input_sha256": _sha("input"), "output_sha256": _sha("v2"),
                "input_readback": True, "output_readback": True,
            },
        ],
        "failures": {
            "invalid_type": {"status": 415},
            "busy": {"status": 429, "retry_after": "2"},
            "unavailable": {"status": 503},
        },
        "readback": {
            "input_hashes": True, "output_hashes": True,
            "failure_paths": True, "device_file_readback": True,
        },
    }


def _binding(raw_bytes: bytes, worker: str = WORKER):
    return {
        "schema": BINDING_SCHEMA,
        "candidate_receipt_sha256": CANDIDATE,
        "production_worker_commit": worker,
        "source_receipt_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    }


def test_current_pc_receipt_can_be_bound_without_opening_private_artifacts():
    receipt = _pc_receipt()
    raw = json.dumps(receipt, sort_keys=True).encode()

    result = audit_current_worker_binding(receipt, _binding(raw), hashlib.sha256(raw).hexdigest())

    assert result["status"] == "PASS"
    assert result["device"] == "pc"
    assert result["release_authorized"] is False
    assert result["private_artifacts_opened"] is False


def test_stale_iphone_receipt_is_not_rebound_to_current_worker():
    receipt = {
        "schema": "minimalizer/local-l05-l07/iphone-acceptance/v1",
        "production_commit": "c68dc17bdc2bd3b0ba0841b7108177553891913c",
        "transport": "private_https",
        "device": "iphone",
        "owner_attestation": True,
        "safari": {"png_result_visible": True, "zerobase2_success_visible": True, "evidence_sha256": _sha("safari")},
        "pwa": {"png_result_visible": True, "zerobase2_success_visible": True, "evidence_sha256": _sha("pwa")},
        "offline_restore": {"airplane_mode_round_trip_passed": True},
        "fallback": {"zerobase2_503_visible": True, "local_v2_success_visible": True, "evidence_sha256": _sha("fallback")},
        "private_drive_readback": True,
    }
    raw = json.dumps(receipt, sort_keys=True).encode()

    with pytest.raises(CurrentWorkerBindingHold, match="IPHONE_WORKER_COMMIT_MISMATCH"):
        audit_current_worker_binding(receipt, _binding(raw), hashlib.sha256(raw).hexdigest())


def test_binding_cannot_claim_a_different_raw_receipt():
    receipt = _pc_receipt()
    raw = json.dumps(receipt, sort_keys=True).encode()
    binding = _binding(b"different-receipt")

    with pytest.raises(CurrentWorkerBindingHold, match="SOURCE_RECEIPT_SHA_MISMATCH"):
        audit_current_worker_binding(receipt, binding, hashlib.sha256(raw).hexdigest())
