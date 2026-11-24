from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.research import local_l04_production_bundle as bundle_module


RECEIPT = "381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a"
CASES = ("H04", "H06", "H08")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _png_header(width: int, height: int) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
        + bytes((8, 6, 0, 0, 0))
        + struct.pack(">I", zlib.crc32(b"IHDR" + struct.pack(">II", width, height) + bytes((8, 6, 0, 0, 0))))
    )


def _fixture(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    cases: dict[str, object] = {}
    for case in CASES:
        directory = tmp_path / case
        directory.mkdir()
        source = f"signed-source-{case}".encode()
        stage8 = f'{{"case":"{case}","stage":8}}'.encode()
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="32"><path d="M0 0"/></svg>'.encode()
        png = _png_header(24, 32)
        paths = {
            "source": directory / "source.bin",
            "stage8_json": directory / "stage8.json",
            "expanded_svg": directory / "expanded.svg",
            "expanded_png": directory / "expanded.png",
        }
        for key, data in (("source", source), ("stage8_json", stage8), ("expanded_svg", svg), ("expanded_png", png)):
            paths[key].write_bytes(data)
        cases[case] = {
            key: {"path": str(path.relative_to(tmp_path)), "sha256": _sha(path.read_bytes())}
            for key, path in paths.items()
        }
        cases[case]["expanded_png"]["derived_from_expanded_svg_sha256"] = _sha(svg)

    manifest = {
        "schema": "minimalizer/local-l04/production-bundle/v2",
        "candidate_receipt_sha256": RECEIPT,
        "L04_formal": "PASS",
        "Golden": "PASS",
        "production": "GO",
        "release_authorized": True,
        "source_free_repository_record": True,
        "rasterization": {
            "renderer": "@resvg/resvg-wasm",
            "version": "2.6.2",
            "wasm_sha256": bundle_module._RASTERIZER_WASM_SHA256,
            "fit": "original",
            "preserve_alpha": True,
        },
        "cases": cases,
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, manifest


def _install_triple_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    def evaluate_paths(**kwargs):
        for path_key, sha_key in (
            ("source_path", "expected_source_sha256"),
            ("stage8_json_path", "expected_stage8_json_sha256"),
            ("expanded_svg_path", "expected_expanded_svg_sha256"),
        ):
            if _sha(Path(kwargs[path_key]).read_bytes()) != kwargs[sha_key]:
                return {"numerical_candidate_eligible_for_independent_review": False}
        return {
            "case": Path(kwargs["source_path"]).parent.name,
            "numerical_candidate_eligible_for_independent_review": True,
        }

    monkeypatch.setattr(
        bundle_module,
        "_load_triple_gate",
        lambda: SimpleNamespace(L04Hold=ValueError, evaluate_paths=evaluate_paths),
    )


def test_loads_exact_formal_candidate_and_reads_only_sha_pinned_assets(tmp_path, monkeypatch):
    manifest_path, _ = _fixture(tmp_path)
    _install_triple_gate(monkeypatch)

    loaded = bundle_module.load_release_bundle(
        manifest_path, expected_candidate_receipt_sha256=RECEIPT
    )

    assert loaded["candidate_receipt_sha256"] == RECEIPT
    assert set(loaded["cases"]) == set(CASES)
    h06 = loaded["cases"]["H06"]
    assert bundle_module.find_case_for_source(loaded, Path(h06["source_path"]).read_bytes()) == "H06"
    assert bundle_module.read_case_svg(loaded, "H06").startswith(b"<svg")
    assert bundle_module.read_case_png(loaded, "H06").startswith(b"\x89PNG")


def test_rejects_wrong_receipt_and_bundle_path_escape(tmp_path, monkeypatch):
    manifest_path, manifest = _fixture(tmp_path)
    _install_triple_gate(monkeypatch)
    with pytest.raises(bundle_module.L04ProductionBundleHold, match="CANDIDATE_RECEIPT_SHA_MISMATCH"):
        bundle_module.load_release_bundle(manifest_path, expected_candidate_receipt_sha256="0" * 64)

    manifest["cases"]["H06"]["source"]["path"] = "../../outside.png"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(bundle_module.L04ProductionBundleHold, match="ARTIFACT_PATH_ESCAPES_BUNDLE"):
        bundle_module.load_release_bundle(manifest_path, expected_candidate_receipt_sha256=RECEIPT)


def test_rejects_png_not_derived_from_the_exact_expanded_svg(tmp_path, monkeypatch):
    manifest_path, manifest = _fixture(tmp_path)
    _install_triple_gate(monkeypatch)
    manifest["cases"]["H04"]["expanded_png"]["derived_from_expanded_svg_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(bundle_module.L04ProductionBundleHold, match="PNG_SOURCE_SVG_SHA_MISMATCH"):
        bundle_module.load_release_bundle(manifest_path, expected_candidate_receipt_sha256=RECEIPT)
