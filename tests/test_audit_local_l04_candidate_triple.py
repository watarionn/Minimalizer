import json
from pathlib import Path

import tools.research.audit_local_l04_candidate_triple as audit_module


def _package(tmp_path: Path, *, release_authorized: bool = False) -> Path:
    root = tmp_path / "package"
    (root / "sources").mkdir(parents=True)
    cases = []
    source_shas = {}
    for case in ("H04", "H06", "H08"):
        source = root / "sources" / f"{case}.png"
        source.write_bytes((case + "-source").encode())
        from tools.research.audit_local_l04_candidate_triple import _sha

        source_shas[case] = _sha(source)
        folder = root / case
        folder.mkdir()
        stage = folder / "stage8_source_ring.json"
        stage.write_text(json.dumps({
            "signed_source_sha256": source_shas[case],
            "expanded_svg_sha256": "pending",
            "source_only_inference": True,
            "human_labels_used_for_inference": False,
            "unknown_pixels_treated_as_negative": False,
        }), encoding="utf-8")
        svg = folder / "expanded_stage8.svg"
        svg.write_text("<svg/>", encoding="utf-8")
        svg_sha = _sha(svg)
        stage.write_text(json.dumps({
            "signed_source_sha256": source_shas[case],
            "expanded_svg_sha256": svg_sha,
            "source_only_inference": True,
            "human_labels_used_for_inference": False,
            "unknown_pixels_treated_as_negative": False,
        }), encoding="utf-8")
        stage_sha = _sha(stage)
        (folder / "TRIPLE_MANIFEST.json").write_text(json.dumps({
            "source": {"path": f"{case}.png", "sha256": source_shas[case]},
            "stage8_json": {"path": stage.name, "sha256": stage_sha},
            "expanded_svg": {"path": svg.name, "sha256": svg_sha},
        }), encoding="utf-8")
        (folder / "L04_GATE_RESULT.json").write_text(json.dumps({
            "signed_source_sha256": source_shas[case],
            "stage8_json_sha256": stage_sha,
            "expanded_svg_sha256": svg_sha,
            "three_artifact_hashes_verified": True,
            "source_owner_exact": True,
            "protected_face_arm_unchanged": True,
            "source_silhouette_exact": True,
            "numerical_candidate_eligible_for_independent_review": True,
            "release_authorized": release_authorized,
            "production_release": "NO_GO",
        }), encoding="utf-8")
        cases.append({
            "case": case,
            "source_sha256": source_shas[case],
            "stage8_json_sha256": stage_sha,
            "expanded_svg_sha256": svg_sha,
        })
    (root / "L04_CANDIDATE_TRIPLE_RECEIPT.json").write_text(json.dumps({
        "schema": "minimalizer/local-l04/candidate-triple-receipt/v1",
        "cases": cases,
    }), encoding="utf-8")
    return root


def test_candidate_triple_audit_passes_numerical_gate(tmp_path: Path, monkeypatch):
    root = _package(tmp_path)
    monkeypatch.setattr(
        audit_module,
        "SOURCE_SHA256",
        {
            case: audit_module._sha(root / "sources" / f"{case}.png")
            for case in ("H04", "H06", "H08")
        },
    )
    result = audit_module.audit_candidate_triple(root)
    assert result["numerical_handoff_eligible"] is True
    assert result["L04_formal"] == "HOLD"
    assert result["release_authorized"] is False


def test_candidate_triple_audit_rejects_release_authorization(tmp_path: Path, monkeypatch):
    root = _package(tmp_path, release_authorized=True)
    monkeypatch.setattr(
        audit_module,
        "SOURCE_SHA256",
        {
            case: audit_module._sha(root / "sources" / f"{case}.png")
            for case in ("H04", "H06", "H08")
        },
    )
    result = audit_module.audit_candidate_triple(root)
    assert result["numerical_handoff_eligible"] is False
    assert "H04:RELEASE_MUST_REMAIN_CLOSED" in result["failures"]
