from __future__ import annotations

import hashlib
import json

import pytest

from tools.research.audit_local_l05_current_worker_binding import CurrentWorkerBindingHold
from tools.research.local_completion_release_gate import EXPECTED_PRODUCTION_WORKER_COMMIT as WORKER
from tools.research.prepare_local_l05_iphone_binding import prepare_iphone_binding


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _iphone_receipt(production_commit: str = WORKER) -> dict[str, object]:
    return {
        "schema": "minimalizer/local-l05-l07/iphone-acceptance/v1",
        "production_commit": production_commit,
        "transport": "private_https",
        "device": "iphone",
        "owner_attestation": True,
        "safari": {
            "png_result_visible": True,
            "zerobase2_success_visible": True,
            "evidence_sha256": _sha("safari"),
        },
        "pwa": {
            "png_result_visible": True,
            "zerobase2_success_visible": True,
            "evidence_sha256": _sha("pwa"),
        },
        "offline_restore": {"airplane_mode_round_trip_passed": True},
        "fallback": {
            "zerobase2_503_visible": True,
            "local_v2_success_visible": True,
            "evidence_sha256": _sha("fallback"),
        },
        "private_drive_readback": True,
    }


def test_prepare_binds_current_worker_without_private_artifacts():
    receipt = _iphone_receipt()
    raw = json.dumps(receipt, sort_keys=True).encode()

    binding = prepare_iphone_binding(receipt, raw)

    assert binding["production_worker_commit"] == WORKER
    assert binding["source_receipt_sha256"] == hashlib.sha256(raw).hexdigest()


def test_prepare_rejects_stale_worker_before_binding():
    receipt = _iphone_receipt("c68dc17bdc2bd3b0ba0841b7108177553891913c")
    raw = json.dumps(receipt, sort_keys=True).encode()

    with pytest.raises(CurrentWorkerBindingHold, match="IPHONE_WORKER_COMMIT_MISMATCH"):
        prepare_iphone_binding(receipt, raw)


def test_prepare_binds_the_exact_raw_bytes():
    receipt = _iphone_receipt()
    raw = json.dumps(receipt, sort_keys=True).encode()

    binding = prepare_iphone_binding(receipt, raw)

    assert binding["source_receipt_sha256"] == hashlib.sha256(raw).hexdigest()
    assert binding["source_receipt_sha256"] != hashlib.sha256(raw + b"\n").hexdigest()
