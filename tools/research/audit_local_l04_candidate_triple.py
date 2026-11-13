"""Audit the current-candidate Local L04 triple without promoting it.

This is the candidate-triple counterpart of the older source-preserving
handoff audit.  It checks the exact source/Stage8/SVG lineage and numerical
eligibility, while keeping visual Golden and production authorization closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


CASES = ("H04", "H06", "H08")
SOURCE_SHA256 = {
    "H04": "7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3",
    "H06": "c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8",
    "H08": "759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e",
}


class CandidateTripleHold(ValueError):
    pass


def _json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise CandidateTripleHold(f"JSON_ROOT_NOT_OBJECT:{path.name}")
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_candidate_triple(root: Path) -> dict[str, Any]:
    root = root.resolve()
    failures: list[str] = []
    receipt_path = root / "L04_CANDIDATE_TRIPLE_RECEIPT.json"
    if not receipt_path.is_file():
        return {
            "schema": "minimalizer/local-l04/candidate-triple-audit/v1",
            "numerical_handoff_eligible": False,
            "L04_formal": "HOLD",
            "Golden": "HOLD",
            "production": "NO_GO",
            "failures": ["TRIPLE_RECEIPT_MISSING"],
            "cases": {},
        }
    receipt = _json(receipt_path)
    if receipt.get("schema") != "minimalizer/local-l04/candidate-triple-receipt/v1":
        failures.append("TRIPLE_RECEIPT_SCHEMA_MISMATCH")
    receipt_cases = {
        item.get("case"): item
        for item in receipt.get("cases", [])
        if isinstance(item, Mapping) and isinstance(item.get("case"), str)
    }
    if set(receipt_cases) != set(CASES):
        failures.append("CASE_SET_MISMATCH")
    cases: dict[str, dict[str, Any]] = {}
    for case in CASES:
        case_failures: list[str] = []
        case_root = root / case
        manifest_path = case_root / "TRIPLE_MANIFEST.json"
        gate_path = case_root / "L04_GATE_RESULT.json"
        stage_fallback = case_root / "stage8_source_ring.json"
        svg_fallback = case_root / "expanded_stage8.svg"
        if not manifest_path.is_file() or not gate_path.is_file():
            case_failures.append("MANIFEST_OR_GATE_MISSING")
            failures.extend(f"{case}:{item}" for item in case_failures)
            cases[case] = {"eligible": False, "failures": case_failures}
            continue
        manifest = _json(manifest_path)
        gate = _json(gate_path)
        item = receipt_cases.get(case, {})
        source_info = manifest.get("source", {})
        stage_info = manifest.get("stage8_json", {})
        svg_info = manifest.get("expanded_svg", {})
        source_path = root / "sources" / str(source_info.get("path", ""))
        stage_path = case_root / str(stage_info.get("path", stage_fallback.name))
        svg_path = case_root / str(svg_info.get("path", svg_fallback.name))
        for label, path in (("source", source_path), ("stage8", stage_path), ("svg", svg_path)):
            if not path.is_file():
                case_failures.append(f"MISSING_{label.upper()}")
        if not case_failures:
            source_sha = _sha(source_path)
            stage_sha = _sha(stage_path)
            svg_sha = _sha(svg_path)
            stage = _json(stage_path)
            checks = (
                (source_sha == SOURCE_SHA256[case], "SOURCE_SHA_MISMATCH"),
                (source_info.get("sha256") == source_sha, "MANIFEST_SOURCE_SHA_MISMATCH"),
                (stage_info.get("sha256") == stage_sha, "MANIFEST_STAGE8_SHA_MISMATCH"),
                (svg_info.get("sha256") == svg_sha, "MANIFEST_SVG_SHA_MISMATCH"),
                (item.get("source_sha256") == source_sha, "RECEIPT_SOURCE_SHA_MISMATCH"),
                (item.get("stage8_json_sha256") == stage_sha, "RECEIPT_STAGE8_SHA_MISMATCH"),
                (item.get("expanded_svg_sha256") == svg_sha, "RECEIPT_SVG_SHA_MISMATCH"),
                (gate.get("signed_source_sha256") == source_sha, "GATE_SOURCE_SHA_MISMATCH"),
                (gate.get("stage8_json_sha256") == stage_sha, "GATE_STAGE8_SHA_MISMATCH"),
                (gate.get("expanded_svg_sha256") == svg_sha, "GATE_SVG_SHA_MISMATCH"),
                (stage.get("signed_source_sha256") == source_sha, "STAGE_SOURCE_SHA_MISMATCH"),
                (stage.get("expanded_svg_sha256") == svg_sha, "STAGE_SVG_SHA_MISMATCH"),
                (stage.get("source_only_inference") is True, "SOURCE_ONLY_POLICY_FAIL"),
                (stage.get("human_labels_used_for_inference") is False, "HUMAN_LABEL_POLICY_FAIL"),
                (stage.get("unknown_pixels_treated_as_negative") is False, "UNKNOWN_POLICY_FAIL"),
                (gate.get("three_artifact_hashes_verified") is True, "THREE_ARTIFACT_BINDING_NOT_VERIFIED"),
                (gate.get("source_owner_exact") is True, "SOURCE_OWNER_NOT_EXACT"),
                (gate.get("protected_face_arm_unchanged") is True, "PROTECTED_OWNER_NOT_EXACT"),
                (gate.get("source_silhouette_exact") is True, "SOURCE_SILHOUETTE_NOT_EXACT"),
                (gate.get("numerical_candidate_eligible_for_independent_review") is True, "NUMERICAL_REVIEW_NOT_ELIGIBLE"),
                (gate.get("release_authorized") is False, "RELEASE_MUST_REMAIN_CLOSED"),
                (gate.get("production_release") == "NO_GO", "PRODUCTION_MUST_REMAIN_NO_GO"),
            )
            case_failures.extend(label for ok, label in checks if not ok)
            cases[case] = {
                "eligible": not case_failures,
                "source_sha256": source_sha,
                "stage8_json_sha256": stage_sha,
                "expanded_svg_sha256": svg_sha,
                "numerical_candidate_eligible_for_independent_review": gate.get("numerical_candidate_eligible_for_independent_review"),
                "failures": case_failures,
            }
        else:
            cases[case] = {"eligible": False, "failures": case_failures}
        failures.extend(f"{case}:{item}" for item in case_failures)
    return {
        "schema": "minimalizer/local-l04/candidate-triple-audit/v1",
        "numerical_handoff_eligible": not failures,
        "L04_formal": "HOLD",
        "Golden": "HOLD",
        "production": "NO_GO",
        "release_authorized": False,
        "failures": failures,
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="現行L04 candidate tripleを監査する")
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_candidate_triple(args.package)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["numerical_handoff_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
