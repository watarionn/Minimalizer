import json
from pathlib import Path

from tools.research.audit_local_l04_candidate_b_delivery import audit_candidate_b_delivery


def test_candidate_b_delivery_fails_closed_when_case_is_missing(tmp_path: Path):
    package = tmp_path / "package"
    package.mkdir()
    result = audit_candidate_b_delivery(package)
    assert result["B_L04_delivery"] == "FAIL"
    assert set(result["cases"]) == {"H04", "H06", "H08"}
    assert result["release_authorized"] is False
