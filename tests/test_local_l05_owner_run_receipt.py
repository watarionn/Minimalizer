import hashlib

import pytest

from tools.research.local_l05_owner_run_receipt import L05Hold, audit_receipt


def _sha(tag: str) -> str:
    return hashlib.sha256(tag.encode()).hexdigest()


def _receipt():
    return {
        "schema": "minimalizer/local-l05/owner-run-receipt/v1",
        "transport": "private_https",
        "production": False,
        "device": "pc",
        "owner_identity_verified": True,
        "origin_verified": True,
        "tailnet_verified": True,
        "health": {"status": 200, "worker": "local-compute-v1", "ready": True},
        "success": [
            {"route": "zerobase2", "status": 200, "content_type": "image/png",
             "input_sha256": _sha("in-best"), "output_sha256": _sha("out-best"),
             "input_readback": True, "output_readback": True},
            {"route": "v2", "status": 200, "content_type": "image/png",
             "input_sha256": _sha("in-v2"), "output_sha256": _sha("out-v2"),
             "input_readback": True, "output_readback": True},
        ],
        "failures": {
            "invalid_type": {"status": 415},
            "busy": {"status": 429, "retry_after": "2"},
            "unavailable": {"status": 503},
        },
        "readback": {"input_hashes": True, "output_hashes": True,
                      "failure_paths": True, "device_file_readback": True},
    }


def test_complete_pc_receipt_is_verified_but_not_released():
    result = audit_receipt(_receipt())
    assert result["owner_pc_e2e_verified"] is True
    assert result["png_routes_verified"] is True
    assert result["failure_paths_verified"] is True
    assert result["file_readback_verified"] is True
    assert result["L05_formal"] == "HOLD"
    assert result["production_release"] == "NO_GO"
    assert result["release_authorized"] is False


@pytest.mark.parametrize("field", ("origin_verified", "tailnet_verified"))
def test_network_identity_is_required(field):
    receipt = _receipt()
    receipt[field] = False
    with pytest.raises(L05Hold, match="OWNER_NETWORK_IDENTITY_NOT_VERIFIED"):
        audit_receipt(receipt)


def test_both_png_routes_are_required():
    receipt = _receipt()
    receipt["success"] = receipt["success"][:1]
    with pytest.raises(L05Hold, match="BOTH_PNG_ROUTES_REQUIRED"):
        audit_receipt(receipt)


def test_missing_readback_is_rejected():
    receipt = _receipt()
    receipt["readback"]["output_hashes"] = False
    with pytest.raises(L05Hold, match="READBACK_INCOMPLETE"):
        audit_receipt(receipt)


def test_busy_retry_after_is_required():
    receipt = _receipt()
    receipt["failures"]["busy"]["retry_after"] = "1"
    with pytest.raises(L05Hold, match="RETRY_AFTER_READBACK_REQUIRED"):
        audit_receipt(receipt)


def test_iphone_acceptance_cannot_be_preproduction():
    receipt = _receipt()
    receipt["device"] = "iphone"
    with pytest.raises(L05Hold, match="IPHONE_ACCEPTANCE_REQUIRES_PRODUCTION"):
        audit_receipt(receipt)
