import hashlib
import json
from pathlib import Path

import pytest

import tools.research.audit_local_l04_candidate_triple as audit_module
import tools.research.bind_local_l02_phase4_l04_triple as bind_module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return _sha(path)


def _fixture(tmp_path: Path, monkeypatch):
    triple = tmp_path / "triple"
    phase5 = tmp_path / "phase5"
    cases = {}
    receipt_cases = []
    for case in bind_module.CASES:
        source_sha = hashlib.sha256((case + "-source").encode()).hexdigest()
        candidate_sha = hashlib.sha256((case + "-candidate").encode()).hexdigest()
        source = triple / "sources" / f"{case}.png"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes((case + "-source").encode())
        p4_path = phase5 / case / "phase_04" / "stage.json"
        p4_sha = _json(p4_path, {
            "source": {"sha256": source_sha},
            "l02_candidate": {"candidate_sha256": candidate_sha},
        })
        graph_path = phase5 / case / "phase_05" / "05_structure_graph.json"
        graph_path.parent.mkdir(parents=True, exist_ok=True)
        graph_path.write_text(case + "-graph", encoding="utf-8")
        graph_sha = _sha(graph_path)
        p5_path = phase5 / case / "phase_05" / "stage.json"
        p5_sha = _json(p5_path, {
            "source": {"sha256": source_sha},
            "inputs": {"phase4": {"stage.json": p4_sha}},
            "outputs": {"05_structure_graph.json": graph_sha},
            "metrics": {"pass": True},
        })
        svg_path = triple / case / "expanded_stage8.svg"
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(f"<svg>{case}</svg>", encoding="utf-8")
        svg_sha = _sha(svg_path)
        stage8_path = triple / case / "stage8_source_ring.json"
        stage8_sha = _json(stage8_path, {
            "signed_source_sha256": source_sha,
            "candidate_sha256": candidate_sha,
            "phase4_stage_json_sha256": p4_sha,
            "phase5_stage_json_sha256": p5_sha,
            "expanded_svg_sha256": svg_sha,
            "source_only_inference": True,
            "human_labels_used_for_inference": False,
            "unknown_pixels_treated_as_negative": False,
        })
        _json(triple / case / "TRIPLE_MANIFEST.json", {
            "source": {"path": f"{case}.png", "sha256": source_sha},
            "candidate_sha256": candidate_sha,
            "stage8_json": {"path": "stage8_source_ring.json", "sha256": stage8_sha},
            "expanded_svg": {"path": svg_path.name, "sha256": svg_sha},
            "phase5_stage_json_sha256": p5_sha,
        })
        _json(triple / case / "L04_GATE_RESULT.json", {
            "signed_source_sha256": source_sha,
            "stage8_json_sha256": stage8_sha,
            "expanded_svg_sha256": svg_sha,
            "three_artifact_hashes_verified": True,
            "source_owner_exact": True,
            "protected_face_arm_unchanged": True,
            "source_silhouette_exact": True,
            "numerical_candidate_eligible_for_independent_review": True,
            "release_authorized": False,
            "production_release": "NO_GO",
        })
        cases[case] = {"source_sha256": source_sha, "candidate_sha256": candidate_sha}
        receipt_cases.append({
            "case": case,
            "source_sha256": source_sha,
            "candidate_sha256": candidate_sha,
            "stage8_json_sha256": stage8_sha,
            "expanded_svg_sha256": svg_sha,
        })
    _json(triple / "L04_CANDIDATE_TRIPLE_RECEIPT.json", {"schema": "minimalizer/local-l04/candidate-triple-receipt/v1", "cases": receipt_cases})
    authority = tmp_path / "authority.json"
    authority_fields = {
        "schema": "minimalizer/local-l02/h08-owner-authority/v1",
        "case": "H08",
        "frozen_owner_sha256": bind_module.FROZEN_H08_OWNER_SHA256,
        "source_sha256": cases["H08"]["source_sha256"],
        "prediction_sha256": cases["H08"]["candidate_sha256"],
        "golden": "HOLD",
        "production": "NO_GO",
    }
    authority_fields.update({field: True for field in bind_module.AUTHORITY_TRUE_FIELDS})
    _json(authority, authority_fields)
    monkeypatch.setattr(audit_module, "SOURCE_SHA256", {case: values["source_sha256"] for case, values in cases.items()})
    monkeypatch.setattr(bind_module, "verify_phase4_receipt", lambda review, freeze: {"cases": cases, "phase4": "PASS"})
    return triple, phase5, authority, cases


def test_binder_requires_one_candidate_across_phase4_phase5_and_l04(tmp_path, monkeypatch):
    triple, phase5, authority, cases = _fixture(tmp_path, monkeypatch)
    review = tmp_path / "review.json"
    freeze = tmp_path / "freeze.json"
    _json(review, {"review": "signed"})
    _json(freeze, {"freeze": "pinned"})

    result = bind_module.bind_candidate_triple(
        phase4_receipt=review,
        freeze_receipt=freeze,
        triple_root=triple,
        phase5_root=phase5,
        h08_authority_receipt=authority,
    )

    assert result["phase4"] == "PASS"
    assert result["phase5_replay"] == "PASS"
    assert result["candidate_status"] == "READY_FOR_OWNER_REVIEW"
    assert result["production"] == "NO_GO"
    assert result["cases"]["H06"]["candidate_sha256"] == cases["H06"]["candidate_sha256"]


def test_binder_rejects_phase5_source_candidate_mismatch(tmp_path, monkeypatch):
    triple, phase5, authority, _ = _fixture(tmp_path, monkeypatch)
    review = tmp_path / "review.json"
    freeze = tmp_path / "freeze.json"
    _json(review, {"review": "signed"})
    _json(freeze, {"freeze": "pinned"})
    stage8_path = triple / "H06" / "stage8_source_ring.json"
    stage8 = json.loads(stage8_path.read_text(encoding="utf-8"))
    stage8["candidate_sha256"] = "0" * 64
    stage8_path.write_text(json.dumps(stage8), encoding="utf-8")

    with pytest.raises(bind_module.CandidateBindingHold, match="L04_TRIPLE_AUDIT_HOLD"):
        bind_module.bind_candidate_triple(
            phase4_receipt=review,
            freeze_receipt=freeze,
            triple_root=triple,
            phase5_root=phase5,
            h08_authority_receipt=authority,
        )
