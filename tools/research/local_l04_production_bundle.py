"""Fail-closed loader for a formally released Local L04 artifact bundle.

The bundle is private runtime input.  This module does not create or promote
an L04 candidate.  It only permits an already approved source/Stage8/SVG
triple to be read by a later delivery route.  A delivery route must not use a
PNG produced by another pipeline as a substitute for the expanded SVG.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


class L04ProductionBundleHold(ValueError):
    """The private bundle is incomplete, inconsistent, or not releasable."""


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SCHEMA_V1 = "minimalizer/local-l04/production-bundle/v1"
_SCHEMA_V2 = "minimalizer/local-l04/production-bundle/v2"
_SCHEMAS = {_SCHEMA_V1, _SCHEMA_V2}
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_RASTERIZER = "@resvg/resvg-wasm"
_RASTERIZER_VERSION = "2.6.2"
_RASTERIZER_WASM_SHA256 = "22bf6e9f9a100d972da0411a69c5ba504367fc1fa87b3b64e3f35e53926d2d70"
_CASES = ("H04", "H06", "H08")
_STATUS_FIELDS = ("L04_formal", "Golden", "production")


def _load_triple_gate():
    path = Path(__file__).with_name("local_l04_source_stage8_svg_triple_gate.py")
    spec = importlib.util.spec_from_file_location("local_l04_triple_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("L04_TRIPLE_GATE_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise L04ProductionBundleHold("MISSING_OR_INVALID_SHA:" + label)
    return value


def _status(value: Any, label: str, expected: str) -> None:
    if value != expected:
        raise L04ProductionBundleHold(
            f"RELEASE_STATUS_NOT_{expected.upper()}:{label}:{value!r}"
        )


def _artifact_path(root: Path, entry: Any, label: str) -> Path:
    if not isinstance(entry, dict):
        raise L04ProductionBundleHold("MISSING_ARTIFACT_ENTRY:" + label)
    relative = entry.get("path")
    if not isinstance(relative, str) or not relative.strip():
        raise L04ProductionBundleHold("MISSING_ARTIFACT_PATH:" + label)
    candidate = Path(relative)
    if candidate.is_absolute():
        raise L04ProductionBundleHold("ABSOLUTE_ARTIFACT_PATH:" + label)
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise L04ProductionBundleHold("ARTIFACT_PATH_ESCAPES_BUNDLE:" + label)
    if not resolved.is_file():
        raise L04ProductionBundleHold("MISSING_ARTIFACT:" + label)
    return resolved


def _artifact_sha(entry: Any, label: str) -> str:
    if not isinstance(entry, dict):
        raise L04ProductionBundleHold("MISSING_ARTIFACT_ENTRY:" + label)
    return _sha(entry.get("sha256"), label + ":sha256")


def _load_manifest(path: Path) -> tuple[Path, dict[str, Any]]:
    if not isinstance(path, Path) or not path.is_file():
        raise L04ProductionBundleHold("MISSING_BUNDLE_MANIFEST")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise L04ProductionBundleHold("INVALID_BUNDLE_MANIFEST") from exc
    if not isinstance(value, dict) or value.get("schema") not in _SCHEMAS:
        raise L04ProductionBundleHold("INVALID_BUNDLE_SCHEMA")
    return path.parent.resolve(), value


def load_release_bundle(
    manifest_path: Path,
    *,
    expected_candidate_receipt_sha256: str | None = None,
) -> dict[str, Any]:
    """Verify and load a formally approved private L04 bundle.

    The returned paths are exact files from the checked bundle.  The loader
    intentionally rejects the currently known HOLD/NO_GO candidate packages.
    """
    root, manifest = _load_manifest(manifest_path)
    schema = manifest["schema"]
    receipt_sha = _sha(
        manifest.get("candidate_receipt_sha256"),
        "candidate_receipt_sha256",
    )
    if expected_candidate_receipt_sha256 is not None:
        expected = _sha(
            expected_candidate_receipt_sha256,
            "expected_candidate_receipt_sha256",
        )
        if receipt_sha != expected:
            raise L04ProductionBundleHold("CANDIDATE_RECEIPT_SHA_MISMATCH")
    for field in _STATUS_FIELDS:
        _status(manifest.get(field), field, "PASS" if field != "production" else "GO")
    if manifest.get("release_authorized") is not True:
        raise L04ProductionBundleHold("RELEASE_NOT_AUTHORIZED")
    if manifest.get("source_free_repository_record") is not True:
        raise L04ProductionBundleHold("SOURCE_FREE_RECORD_MISSING")

    cases = manifest.get("cases")
    if not isinstance(cases, dict) or set(cases) != set(_CASES):
        raise L04ProductionBundleHold("REQUIRED_CASE_SET_MISMATCH")

    rasterization: dict[str, str] | None = None
    if schema == _SCHEMA_V2:
        raster = manifest.get("rasterization")
        if not isinstance(raster, dict):
            raise L04ProductionBundleHold("MISSING_RASTERIZATION_RECORD")
        renderer = raster.get("renderer")
        version = raster.get("version")
        wasm_sha = _sha(raster.get("wasm_sha256"), "rasterization:wasm_sha256")
        if renderer != _RASTERIZER:
            raise L04ProductionBundleHold("UNSUPPORTED_RASTERIZER")
        if version != _RASTERIZER_VERSION or wasm_sha != _RASTERIZER_WASM_SHA256:
            raise L04ProductionBundleHold("RASTERIZER_BUILD_MISMATCH")
        if raster.get("fit") != "original" or raster.get("preserve_alpha") is not True:
            raise L04ProductionBundleHold("UNSUPPORTED_RASTERIZATION_PROFILE")
        rasterization = {
            "renderer": renderer,
            "version": version,
            "wasm_sha256": wasm_sha,
        }

    triple_gate = _load_triple_gate()
    result_cases: dict[str, dict[str, Any]] = {}
    for case in _CASES:
        entry = cases[case]
        if not isinstance(entry, dict):
            raise L04ProductionBundleHold("INVALID_CASE_ENTRY:" + case)
        source = _artifact_path(root, entry.get("source"), case + ":source")
        stage8 = _artifact_path(root, entry.get("stage8_json"), case + ":stage8_json")
        expanded_svg = _artifact_path(root, entry.get("expanded_svg"), case + ":expanded_svg")
        expected_source = _artifact_sha(
            entry.get("source"), case + ":source"
        )
        expected_stage8 = _artifact_sha(
            entry.get("stage8_json"), case + ":stage8_json"
        )
        expected_svg = _artifact_sha(
            entry.get("expanded_svg"), case + ":expanded_svg"
        )
        try:
            result = triple_gate.evaluate_paths(
                source_path=source,
                stage8_json_path=stage8,
                expanded_svg_path=expanded_svg,
                expected_source_sha256=expected_source,
                expected_stage8_json_sha256=expected_stage8,
                expected_expanded_svg_sha256=expected_svg,
            )
        except triple_gate.L04Hold as exc:
            raise L04ProductionBundleHold(str(exc)) from exc
        if result.get("case") != case:
            raise L04ProductionBundleHold("CASE_ID_MISMATCH:" + case)
        if result.get("numerical_candidate_eligible_for_independent_review") is not True:
            raise L04ProductionBundleHold("NUMERICAL_L04_GATE_NOT_PASS:" + case)
        loaded_case = {
            "source_path": str(source),
            "stage8_json_path": str(stage8),
            "expanded_svg_path": str(expanded_svg),
            "source_sha256": expected_source,
            "stage8_json_sha256": expected_stage8,
            "expanded_svg_sha256": expected_svg,
        }
        if schema == _SCHEMA_V2:
            png_entry = entry.get("expanded_png")
            png_path = _artifact_path(root, png_entry, case + ":expanded_png")
            png_sha = _artifact_sha(png_entry, case + ":expanded_png")
            derived_svg_sha = _sha(
                png_entry.get("derived_from_expanded_svg_sha256"),
                case + ":expanded_png:derived_from_expanded_svg_sha256",
            )
            if derived_svg_sha != expected_svg:
                raise L04ProductionBundleHold("PNG_SOURCE_SVG_SHA_MISMATCH:" + case)
            png_data = png_path.read_bytes()
            if _sha256(png_data) != png_sha:
                raise L04ProductionBundleHold("EXPANDED_PNG_SHA_MISMATCH:" + case)
            png_width, png_height = _png_dimensions(png_data, case)
            try:
                svg_root = ET.fromstring(expanded_svg.read_bytes())
                svg_width = _svg_dimension(svg_root.attrib.get("width"), case + ":svg_width")
                svg_height = _svg_dimension(svg_root.attrib.get("height"), case + ":svg_height")
            except (ET.ParseError, OSError) as exc:
                raise L04ProductionBundleHold("INVALID_EXPANDED_SVG:" + case) from exc
            if (png_width, png_height) != (svg_width, svg_height):
                raise L04ProductionBundleHold("EXPANDED_PNG_DIMENSION_MISMATCH:" + case)
            loaded_case.update({
                "expanded_png_path": str(png_path),
                "expanded_png_sha256": png_sha,
                "expanded_png_width": png_width,
                "expanded_png_height": png_height,
            })
        result_cases[case] = loaded_case
    return {
        "schema": schema,
        "candidate_receipt_sha256": receipt_sha,
        "bundle_root": str(root),
        "cases": result_cases,
        "rasterization": rasterization,
        "release_authorized": True,
    }


__all__ = ["L04ProductionBundleHold", "load_release_bundle"]


def find_case_for_source(bundle: dict[str, Any], source_bytes: bytes) -> str | None:
    """Return the formal case whose signed source bytes match exactly."""
    source_sha = _sha256(source_bytes)
    cases = bundle.get("cases")
    if not isinstance(cases, dict):
        raise L04ProductionBundleHold("LOADED_BUNDLE_CASES_MISSING")
    for case, entry in cases.items():
        if isinstance(entry, dict) and entry.get("source_sha256") == source_sha:
            return case
    return None


def read_case_svg(bundle: dict[str, Any], case: str) -> bytes:
    """Read the exact expanded SVG selected by a previously verified bundle."""
    cases = bundle.get("cases")
    if not isinstance(cases, dict) or case not in cases:
        raise L04ProductionBundleHold("CASE_NOT_IN_LOADED_BUNDLE:" + case)
    path = Path(cases[case]["expanded_svg_path"])
    data = path.read_bytes()
    if _sha256(data) != cases[case]["expanded_svg_sha256"]:
        raise L04ProductionBundleHold("LOADED_SVG_SHA_MISMATCH:" + case)
    return data


def _png_dimensions(data: bytes, label: str) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != _PNG_SIGNATURE or data[12:16] != b"IHDR":
        raise L04ProductionBundleHold("INVALID_EXPANDED_PNG:" + label)
    width, height = struct.unpack(">II", data[16:24])
    if width <= 0 or height <= 0:
        raise L04ProductionBundleHold("INVALID_EXPANDED_PNG_DIMENSIONS:" + label)
    return width, height


def _svg_dimension(value: Any, label: str) -> int:
    if not isinstance(value, str) or re.fullmatch(r"[1-9][0-9]*", value) is None:
        raise L04ProductionBundleHold("INVALID_SVG_DIMENSION:" + label)
    return int(value)


def read_case_png(bundle: dict[str, Any], case: str) -> bytes:
    """Read the SHA-pinned transparent PNG derivative of a formal SVG."""
    cases = bundle.get("cases")
    if not isinstance(cases, dict) or case not in cases:
        raise L04ProductionBundleHold("CASE_NOT_IN_LOADED_BUNDLE:" + case)
    entry = cases[case]
    path_value = entry.get("expanded_png_path")
    expected_sha = entry.get("expanded_png_sha256")
    if not isinstance(path_value, str) or not isinstance(expected_sha, str):
        raise L04ProductionBundleHold("FORMAL_PNG_NOT_CONFIGURED:" + case)
    path = Path(path_value)
    data = path.read_bytes()
    if _sha256(data) != expected_sha:
        raise L04ProductionBundleHold("LOADED_PNG_SHA_MISMATCH:" + case)
    width, height = _png_dimensions(data, case)
    if (width, height) != (
        entry.get("expanded_png_width"), entry.get("expanded_png_height")
    ):
        raise L04ProductionBundleHold("LOADED_PNG_DIMENSION_MISMATCH:" + case)
    return data


def load_configured_release_bundle() -> dict[str, Any] | None:
    """Load the private bundle configured for a worker, or return None.

    A configured but invalid bundle is not silently treated as a release.  The
    caller can choose whether to surface the hold or leave the ordinary PNG
    route available while the formal SVG route remains unavailable.
    """
    manifest = os.getenv("MINIMALIZER_LOCAL_L04_BUNDLE_MANIFEST", "").strip()
    if not manifest:
        return None
    expected = os.getenv(
        "MINIMALIZER_LOCAL_L04_RECEIPT_SHA256",
        "381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a",
    ).strip()
    return load_release_bundle(
        Path(manifest), expected_candidate_receipt_sha256=expected
    )


__all__ += [
    "find_case_for_source",
    "read_case_svg",
    "read_case_png",
    "load_configured_release_bundle",
]
