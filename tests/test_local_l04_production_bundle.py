import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SRC = (Path(__file__).resolve().parents[1] /
       "tools/research/local_l04_production_bundle.py")
spec = importlib.util.spec_from_file_location("local_l04_production_bundle", SRC)
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _case(root: Path, case: str) -> dict:
    source = f"signed-{case}".encode()
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0h1v1z"/></svg>'
    source_path = root / f"{case}.source"
    svg_path = root / f"{case}.svg"
    source_path.write_bytes(source)
    svg_path.write_bytes(svg)
    record = {
        "schema": "minimalizer/local-l04/stage8-source-triple/v1",
        "case": case,
        "signed_source_sha256": _sha(source),
        "expanded_svg_sha256": _sha(svg),
        "original_stage8_source_ring_vertices": 4,
        "expanded_svg_vertices": 4,
        "source_owner_mismatch_pixels": 0,
        "protected_face_arm_owner_mismatch_pixels": 0,
        "source_silhouette_xor_pixels": 0,
    }
    stage8_path = root / f"{case}.stage8.json"
    stage8_path.write_text(json.dumps(record, separators=(",", ":")), encoding="utf-8")
    return {
        "source": {"path": source_path.name, "sha256": _sha(source)},
        "stage8_json": {"path": stage8_path.name, "sha256": _sha(stage8_path.read_bytes())},
        "expanded_svg": {"path": svg_path.name, "sha256": _sha(svg)},
    }


def _manifest(root: Path, *, status="PASS") -> Path:
    cases = {case: _case(root, case) for case in ("H04", "H06", "H08")}
    data = {
        "schema": "minimalizer/local-l04/production-bundle/v1",
        "candidate_receipt_sha256": "1" * 64,
        "L04_formal": status,
        "Golden": status,
        "production": "GO" if status == "PASS" else "NO_GO",
        "release_authorized": status == "PASS",
        "source_free_repository_record": True,
        "cases": cases,
    }
    path = root / "PRODUCTION_BUNDLE.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def test_hold_bundle_is_rejected(tmp_path):
    path = _manifest(tmp_path, status="HOLD")
    with pytest.raises(bundle.L04ProductionBundleHold, match="RELEASE_STATUS_NOT_PASS:L04_formal"):
        bundle.load_release_bundle(path)


def test_candidate_receipt_pin_is_required(tmp_path):
    path = _manifest(tmp_path)
    with pytest.raises(bundle.L04ProductionBundleHold, match="CANDIDATE_RECEIPT_SHA_MISMATCH"):
        bundle.load_release_bundle(path, expected_candidate_receipt_sha256="2" * 64)


def test_pass_bundle_returns_exact_triple_paths(tmp_path):
    path = _manifest(tmp_path)
    result = bundle.load_release_bundle(path, expected_candidate_receipt_sha256="1" * 64)
    assert result["release_authorized"] is True
    assert set(result["cases"]) == {"H04", "H06", "H08"}
    for case in result["cases"].values():
        assert Path(case["expanded_svg_path"]).is_file()


def test_path_escape_is_rejected(tmp_path):
    path = _manifest(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["cases"]["H04"]["source"]["path"] = "../outside.source"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(bundle.L04ProductionBundleHold, match="ARTIFACT_PATH_ESCAPES_BUNDLE:H04:source"):
        bundle.load_release_bundle(path)


def test_svg_tamper_is_rejected_by_triple_gate(tmp_path):
    path = _manifest(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    svg_path = tmp_path / data["cases"]["H06"]["expanded_svg"]["path"]
    svg_path.write_bytes(svg_path.read_bytes().replace(b"h1", b"h2"))
    with pytest.raises(bundle.L04ProductionBundleHold, match="EXPANDED_SVG_SHA_MISMATCH"):
        bundle.load_release_bundle(path)
