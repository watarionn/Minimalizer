from pathlib import Path

import pytest

from tools.research.prepare_local_l02_h08_owner_authority_receipt import (
    CANDIDATE_SHA256,
    H08AuthorityHold,
    materialize_authority_receipt,
    render_authority_form,
)


def complete_form() -> str:
    text = render_authority_form()
    text = text.replace("owner_id:", "owner_id: watar", 1)
    text = text.replace("approved_at_utc:", "approved_at_utc: 2026-11-11T00:00:00Z", 1)
    text = text.replace("approval_record:", "approval_record: explicit-owner-approval-record", 1)
    for field in (
        "authority_receipt_verified",
        "bound_to_case",
        "bound_to_source_sha",
        "bound_to_prediction_sha",
        "bound_to_observer_sha",
        "owner_promotion_explicitly_approved",
        "unknown_not_promoted",
        "human_labels_not_used_for_inference",
        "production_not_authorized",
    ):
        text = text.replace(f"{field}: UNANSWERED", f"{field}: YES")
    return text


def test_form_pins_current_h08_candidate():
    form = render_authority_form()
    assert f"candidate_sha256: {CANDIDATE_SHA256}" in form
    assert "frozen_owner_sha256:" in form
    assert "observer_sha256:" in form


def test_complete_form_materializes_non_promoting_authority_receipt():
    receipt = materialize_authority_receipt(complete_form())
    assert receipt["case"] == "H08"
    assert receipt["owner_promotion_authorized"] is True
    assert receipt["golden"] == "HOLD"
    assert receipt["production"] == "NO_GO"


def test_stale_candidate_is_rejected():
    form = complete_form().replace(CANDIDATE_SHA256, "f" * 64, 1)
    with pytest.raises(H08AuthorityHold, match="CANDIDATE_SHA_MISMATCH"):
        materialize_authority_receipt(form)


def test_unanswered_authority_does_not_materialize():
    form = complete_form().replace(
        "owner_promotion_explicitly_approved: YES",
        "owner_promotion_explicitly_approved: UNANSWERED",
    )
    with pytest.raises(H08AuthorityHold, match="UNANSWERED_OR_INVALID:owner_promotion_explicitly_approved"):
        materialize_authority_receipt(form)
