"""Fail-closed lineage gate for the private Local L04 three-artifact set.

This module only reads the signed source image, Stage8 JSON and expanded SVG.
It never rewrites geometry, changes Golden/Public assets, or authorizes release.
The expected file hashes are supplied by an independently preserved receipt;
the Stage8 JSON cross-links the source and expanded SVG hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree


class L04Hold(ValueError):
    """Untrusted, incomplete, or numerically ineligible L04 evidence."""


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SCHEMA = "minimalizer/local-l04/stage8-source-triple/v1"
_REQUIRED_NUMBERS = (
    "original_stage8_source_ring_vertices",
    "original_stage8_source_ring_cap",
    "expanded_svg_vertices",
    "expanded_svg_vertex_cap",
    "source_owner_mismatch_pixels",
    "protected_face_arm_owner_mismatch_pixels",
    "source_silhouette_xor_pixels",
)
_FORBIDDEN_SVG_TAGS = frozenset({
    "script", "foreignobject", "iframe", "object", "embed", "image",
    "audio", "video", "canvas",
})


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _required_sha(value: object, field: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise L04Hold("MISSING_OR_INVALID_SHA:" + field)
    return value


def _read_regular(path: Path, label: str) -> bytes:
    if not isinstance(path, Path) or not path.is_file():
        raise L04Hold("MISSING_ARTIFACT:" + label)
    data = path.read_bytes()
    if not data:
        raise L04Hold("EMPTY_ARTIFACT:" + label)
    return data


def _validate_svg(svg_bytes: bytes) -> None:
    # External entities and DTDs are not part of the signed expanded artifact.
    upper = svg_bytes.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise L04Hold("UNSAFE_EXPANDED_SVG_MARKUP")
    try:
        root = ElementTree.fromstring(svg_bytes)
    except ElementTree.ParseError as exc:
        raise L04Hold("INVALID_EXPANDED_SVG_XML") from exc
    tag = root.tag.rsplit("}", 1)[-1] if isinstance(root.tag, str) else ""
    if tag != "svg":
        raise L04Hold("EXPANDED_SVG_ROOT_NOT_SVG")
    for node in root.iter():
        local_tag = node.tag.rsplit("}", 1)[-1] if isinstance(node.tag, str) else ""
        if local_tag.lower() in _FORBIDDEN_SVG_TAGS:
            raise L04Hold("UNSAFE_EXPANDED_SVG_CONTENT:" + local_tag)
        for attr, value in node.attrib.items():
            local_attr = attr.rsplit("}", 1)[-1].lower()
            if local_attr.startswith("on"):
                raise L04Hold("UNSAFE_EXPANDED_SVG_EVENT_ATTRIBUTE")
            if local_attr in {"href", "src"}:
                reference = value.strip()
                if reference and not reference.startswith("#"):
                    raise L04Hold("UNSAFE_EXPANDED_SVG_EXTERNAL_REFERENCE")
    geometry_tags = {"path", "polygon", "polyline", "rect", "circle",
                     "ellipse", "line"}
    if not any(
            isinstance(node.tag, str) and
            node.tag.rsplit("}", 1)[-1] in geometry_tags
            for node in root.iter()):
        raise L04Hold("EMPTY_EXPANDED_SVG_GEOMETRY")


def evaluate_paths(*, source_path: Path, stage8_json_path: Path,
                   expanded_svg_path: Path, expected_source_sha256: str,
                   expected_stage8_json_sha256: str,
                   expected_expanded_svg_sha256: str) -> dict:
    """Verify the exact private triple and return a non-promoting receipt."""
    expected_source = _required_sha(expected_source_sha256, "expected_source_sha256")
    expected_stage8 = _required_sha(expected_stage8_json_sha256,
                                    "expected_stage8_json_sha256")
    expected_svg = _required_sha(expected_expanded_svg_sha256,
                                 "expected_expanded_svg_sha256")
    source = _read_regular(source_path, "signed_source")
    stage8_bytes = _read_regular(stage8_json_path, "stage8_json")
    svg = _read_regular(expanded_svg_path, "expanded_svg")
    source_sha = _sha256(source)
    stage8_sha = _sha256(stage8_bytes)
    svg_sha = _sha256(svg)
    if source_sha != expected_source:
        raise L04Hold("SIGNED_SOURCE_SHA_MISMATCH")
    if stage8_sha != expected_stage8:
        raise L04Hold("STAGE8_JSON_SHA_MISMATCH")
    if svg_sha != expected_svg:
        raise L04Hold("EXPANDED_SVG_SHA_MISMATCH")
    _validate_svg(svg)
    try:
        record = json.loads(stage8_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise L04Hold("INVALID_STAGE8_JSON") from exc
    if not isinstance(record, dict) or record.get("schema") != _SCHEMA:
        raise L04Hold("INVALID_STAGE8_SCHEMA")
    case = record.get("case")
    if not isinstance(case, str) or not case.strip():
        raise L04Hold("MISSING_CASE")
    if _required_sha(record.get("signed_source_sha256"),
                     "signed_source_sha256") != source_sha:
        raise L04Hold("MANIFEST_SOURCE_SHA_MISMATCH")
    if _required_sha(record.get("expanded_svg_sha256"),
                     "expanded_svg_sha256") != svg_sha:
        raise L04Hold("MANIFEST_EXPANDED_SVG_SHA_MISMATCH")
    for key in _REQUIRED_NUMBERS:
        value = record.get(key)
        if type(value) is not int or value < 0:
            raise L04Hold("INVALID_MEASUREMENT:" + key)
    if (record["original_stage8_source_ring_vertices"] == 0 or
            record["original_stage8_source_ring_cap"] == 0 or
            record["expanded_svg_vertices"] == 0 or
            record["expanded_svg_vertex_cap"] == 0):
        raise L04Hold("INVALID_EMPTY_GEOMETRY_OR_ZERO_CAP")

    source_budget_ok = (record["original_stage8_source_ring_vertices"] <=
                        record["original_stage8_source_ring_cap"])
    svg_budget_ok = (record["expanded_svg_vertices"] <=
                     record["expanded_svg_vertex_cap"])
    owner_ok = record["source_owner_mismatch_pixels"] == 0
    protected_ok = record["protected_face_arm_owner_mismatch_pixels"] == 0
    silhouette_ok = record["source_silhouette_xor_pixels"] == 0
    numerical = source_budget_ok and svg_budget_ok and owner_ok and protected_ok and silhouette_ok
    return {
        "schema": "minimalizer/local-l04/source-stage8-svg-triple-gate/v1",
        "case": case,
        "signed_source_sha256": source_sha,
        "stage8_json_sha256": stage8_sha,
        "expanded_svg_sha256": svg_sha,
        "three_artifact_hashes_verified": True,
        "source_budget_pass": source_budget_ok,
        "expanded_svg_budget_pass": svg_budget_ok,
        "source_owner_exact": owner_ok,
        "protected_face_arm_unchanged": protected_ok,
        "source_silhouette_exact": silhouette_ok,
        "numerical_candidate_eligible_for_independent_review": numerical,
        "human_visual_golden": "HOLD",
        "L04_formal": "HOLD",
        "production_release": "NO_GO",
        "release_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("stage8_json", type=Path)
    parser.add_argument("expanded_svg", type=Path)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--stage8-json-sha256", required=True)
    parser.add_argument("--expanded-svg-sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(evaluate_paths(
        source_path=args.source, stage8_json_path=args.stage8_json,
        expanded_svg_path=args.expanded_svg,
        expected_source_sha256=args.source_sha256,
        expected_stage8_json_sha256=args.stage8_json_sha256,
        expected_expanded_svg_sha256=args.expanded_svg_sha256,
    ), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
