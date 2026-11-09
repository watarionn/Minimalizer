"""Audit the A-to-B L04 handoff without changing either lane's artifacts.

The handoff is eligible only when H04/H06/H08 each have a source, Stage8 JSON,
expanded SVG, and gate result with matching hashes and PASS conditions. This
tool never changes L04 policy, rewrites SVG, or promotes a HOLD artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping


SOURCE_SHA256 = {
    "H04": "7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3",
    "H06": "c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8",
    "H08": "759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> Mapping[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"JSON_ROOT_NOT_OBJECT:{path.name}")
    return value


def audit_l04_package(root: Path) -> dict[str, object]:
    receipt_path = root / "L04_SOURCE_PRESERVING_TRIPLE_RECEIPT.json"
    failures: list[str] = []
    if not receipt_path.is_file():
        return {
            "schema": "minimalizer/local-l02-to-l04-handoff-audit/v1",
            "handoff_eligible": False,
            "failures": ["TRIPLE_RECEIPT_MISSING"],
            "cases": {},
        }
    receipt = _json(receipt_path)
    if receipt.get("schema") != "minimalizer/local-l04/source-preserving-triple-receipt/v1":
        failures.append("TRIPLE_RECEIPT_SCHEMA_MISMATCH")
    cases: dict[str, dict[str, object]] = {}
    receipt_cases = {
        item.get("case"): item
        for item in receipt.get("cases", [])
        if isinstance(item, Mapping) and isinstance(item.get("case"), str)
    }
    for case, expected_source_sha in SOURCE_SHA256.items():
        case_dir = root / case
        source = case_dir / f"{case}.webp"
        stage8 = case_dir / "stage8_source_preserving.json"
        svg = case_dir / "expanded_stage8_source_preserving.svg"
        gate_path = case_dir / "L04_GATE_RESULT.json"
        manifest_path = case_dir / "TRIPLE_MANIFEST.json"
        missing = [p.name for p in (source, stage8, svg, gate_path, manifest_path) if not p.is_file()]
        case_failures: list[str] = []
        if missing:
            case_failures.append("MISSING:" + ",".join(missing))
            failures.extend(f"{case}:{item}" for item in case_failures)
            cases[case] = {"eligible": False, "failures": case_failures}
            continue
        stage = _json(stage8)
        gate = _json(gate_path)
        manifest = _json(manifest_path)
        actual_source_sha = sha256(source)
        actual_stage_sha = sha256(stage8)
        actual_svg_sha = sha256(svg)
        if actual_source_sha != expected_source_sha or stage.get("signed_source_sha256") != expected_source_sha:
            case_failures.append("SOURCE_SHA_MISMATCH")
        manifest_source = manifest.get("source", {})
        manifest_stage = manifest.get("stage8_json", {})
        manifest_svg = manifest.get("expanded_svg", {})
        if manifest_source.get("sha256") != actual_source_sha:
            case_failures.append("MANIFEST_SOURCE_SHA_MISMATCH")
        if manifest_stage.get("path") != stage8.name or manifest_stage.get("sha256") != actual_stage_sha:
            case_failures.append("MANIFEST_STAGE8_SHA_MISMATCH")
        if manifest_svg.get("path") != svg.name or manifest_svg.get("sha256") != actual_svg_sha:
            case_failures.append("MANIFEST_SVG_SHA_MISMATCH")
        if gate.get("stage8_json_sha256") != actual_stage_sha:
            case_failures.append("STAGE8_JSON_SHA_MISMATCH")
        if gate.get("expanded_svg_sha256") != actual_svg_sha or stage.get("expanded_svg_sha256") != actual_svg_sha:
            case_failures.append("EXPANDED_SVG_SHA_MISMATCH")
        if gate.get("three_artifact_hashes_verified") is not True:
            case_failures.append("THREE_ARTIFACT_BINDING_NOT_VERIFIED")
        if gate.get("source_owner_exact") is not True or gate.get("source_silhouette_exact") is not True:
            case_failures.append("SOURCE_GEOMETRY_NOT_EXACT")
        if stage.get("source_only_inference") is not True or stage.get("human_labels_used_for_inference") is not False:
            case_failures.append("SOURCE_ONLY_POLICY_FAIL")
        if stage.get("unknown_pixels_treated_as_negative") is not False:
            case_failures.append("UNKNOWN_POLICY_FAIL")
        if stage.get("chromium_alpha_replay", {}).get("pass") is not True:
            case_failures.append("CHROMIUM_REPLAY_FAIL")
        if gate.get("L04_formal") != "PASS" or gate.get("source_budget_pass") is not True or gate.get("expanded_svg_budget_pass") is not True:
            case_failures.append("L04_BUDGET_OR_FORMAL_HOLD")
        if receipt_cases.get(case, {}).get("three_artifact_hashes_verified") is not True:
            case_failures.append("RECEIPT_CASE_NOT_VERIFIED")
        failures.extend(f"{case}:{item}" for item in case_failures)
        cases[case] = {
            "eligible": not case_failures,
            "source_sha256": actual_source_sha,
            "stage8_json_sha256": actual_stage_sha,
            "expanded_svg_sha256": actual_svg_sha,
            "expanded_svg_vertices": stage.get("expanded_svg_vertices"),
            "expanded_svg_vertex_cap": stage.get("expanded_svg_vertex_cap"),
            "failures": case_failures,
        }
    return {
        "schema": "minimalizer/local-l02-to-l04-handoff-audit/v1",
        "handoff_eligible": not failures,
        "failures": failures,
        "cases": cases,
        "phase5": "REQUIRED_BEFORE_L04_HANDOFF",
        "golden": "HOLD",
        "production": "NO_GO",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_l04_package(args.package)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["handoff_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
