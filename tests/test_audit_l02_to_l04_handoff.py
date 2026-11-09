import importlib.util
import json
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "tools/research/audit_l02_to_l04_handoff.py"
spec = importlib.util.spec_from_file_location("audit_l04_handoff", SRC)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def _write_package(tmp_path, *, budget_pass=False, include_h04=True):
    audit.SOURCE_SHA256 = {case: "a" * 64 for case in ("H04", "H06", "H08")}
    root = tmp_path / "package"
    root.mkdir()
    receipt_cases = []
    for case in ("H04", "H06", "H08"):
        if case == "H04" and not include_h04:
            continue
        folder = root / case
        folder.mkdir()
        source = folder / f"{case}.webp"
        source.write_bytes(f"{case}-source".encode())
        source_sha = audit.sha256(source)
        audit.SOURCE_SHA256[case] = source_sha
        stage = {
            "signed_source_sha256": source_sha,
            "phase8_stage_json_sha256": "pending",
            "expanded_svg_sha256": "pending",
            "expanded_svg_vertices": 100,
            "expanded_svg_vertex_cap": 100,
            "source_only_inference": True,
            "human_labels_used_for_inference": False,
            "unknown_pixels_treated_as_negative": False,
            "chromium_alpha_replay": {"pass": True},
        }
        stage_path = folder / "stage8_source_preserving.json"
        stage_path.write_text(json.dumps(stage), encoding="utf-8")
        stage_sha = audit.sha256(stage_path)
        svg = folder / "expanded_stage8_source_preserving.svg"
        svg.write_text("<svg/>", encoding="utf-8")
        svg_sha = audit.sha256(svg)
        stage["phase8_stage_json_sha256"] = stage_sha
        stage["expanded_svg_sha256"] = svg_sha
        stage_path.write_text(json.dumps(stage), encoding="utf-8")
        stage_sha = audit.sha256(stage_path)
        (folder / "TRIPLE_MANIFEST.json").write_text(json.dumps({
            "schema": "minimalizer/local-l04/private-triple-manifest/v1",
            "source": {"path": source.name, "sha256": source_sha},
            "stage8_json": {"path": stage_path.name, "sha256": stage_sha},
            "expanded_svg": {"path": svg.name, "sha256": svg_sha},
        }), encoding="utf-8")
        gate = {
            "case": case,
            "signed_source_sha256": source_sha,
            "stage8_json_sha256": stage_sha,
            "expanded_svg_sha256": svg_sha,
            "three_artifact_hashes_verified": True,
            "source_owner_exact": True,
            "source_silhouette_exact": True,
            "source_budget_pass": budget_pass,
            "expanded_svg_budget_pass": budget_pass,
            "L04_formal": "PASS" if budget_pass else "HOLD",
        }
        (folder / "L04_GATE_RESULT.json").write_text(json.dumps(gate), encoding="utf-8")
        receipt_cases.append({"case": case, "three_artifact_hashes_verified": True})
    (root / "L04_SOURCE_PRESERVING_TRIPLE_RECEIPT.json").write_text(
        json.dumps({
            "schema": "minimalizer/local-l04/source-preserving-triple-receipt/v1",
            "cases": receipt_cases,
        }), encoding="utf-8")
    return root


def test_missing_h04_cannot_enter_l04(tmp_path):
    result = audit.audit_l04_package(_write_package(tmp_path, include_h04=False))
    assert result["handoff_eligible"] is False
    assert any(item.startswith("H04:MISSING:") for item in result["failures"])


def test_vertex_hold_cannot_enter_l04(tmp_path):
    result = audit.audit_l04_package(_write_package(tmp_path, budget_pass=False))
    assert result["handoff_eligible"] is False
    assert "H06:L04_BUDGET_OR_FORMAL_HOLD" in result["failures"]


def test_complete_three_case_contract_is_eligible(tmp_path):
    result = audit.audit_l04_package(_write_package(tmp_path, budget_pass=True))
    assert result["handoff_eligible"] is True
    assert result["phase5"] == "REQUIRED_BEFORE_L04_HANDOFF"
