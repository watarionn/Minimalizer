"""Read-only Local L04 dual-budget and source-fidelity gate.

Never modifies SVG, source rings, owner labels, Golden or release state.
Numerical eligibility is not a human/production approval.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

class BudgetHold(ValueError):
    """Malformed, incomplete or untrusted geometry evidence."""

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_REQUIRED_NUMBERS = (
    "original_stage8_source_ring_vertices", "original_stage8_source_ring_cap",
    "expanded_svg_vertices", "expanded_svg_vertex_cap",
    "source_owner_mismatch_pixels", "protected_face_arm_owner_mismatch_pixels",
    "source_silhouette_xor_pixels",
)

def evaluate(record: dict) -> dict:
    if not isinstance(record, dict) or record.get("schema") != "minimalizer/local-l04/dual-budget-evidence/v1":
        raise BudgetHold("INVALID_EVIDENCE_SCHEMA")
    if not isinstance(record.get("case"), str) or not record["case"].strip():
        raise BudgetHold("MISSING_CASE")
    for key in ("signed_source_sha256", "stage8_source_rings_sha256", "expanded_svg_sha256"):
        value = record.get(key)
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise BudgetHold("MISSING_OR_INVALID_AUTHORITY_SHA:" + key)
    for key in _REQUIRED_NUMBERS:
        value = record.get(key)
        if type(value) is not int or value < 0:
            raise BudgetHold("INVALID_MEASUREMENT:" + key)
    if record["original_stage8_source_ring_cap"] == 0 or record["expanded_svg_vertex_cap"] == 0:
        raise BudgetHold("INVALID_ZERO_CAP")
    if record["original_stage8_source_ring_vertices"] == 0 or record["expanded_svg_vertices"] == 0:
        raise BudgetHold("INVALID_EMPTY_GEOMETRY")
    # No implicit discount for hidden rings, Stage9 paint or compressed SVG bytes.
    source_ok = record["original_stage8_source_ring_vertices"] <= record["original_stage8_source_ring_cap"]
    svg_ok = record["expanded_svg_vertices"] <= record["expanded_svg_vertex_cap"]
    owner_ok = record["source_owner_mismatch_pixels"] == 0
    protected_ok = record["protected_face_arm_owner_mismatch_pixels"] == 0
    silhouette_ok = record["source_silhouette_xor_pixels"] == 0
    eligible = source_ok and svg_ok and owner_ok and protected_ok and silhouette_ok
    # SHA fields are checked for format only; original file bytes are not present.
    return {
        "schema": "minimalizer/local-l04/dual-budget-gate/v1",
        "case": record["case"],
        "original_stage8_source_ring_vertices": record["original_stage8_source_ring_vertices"],
        "original_stage8_source_ring_cap": record["original_stage8_source_ring_cap"],
        "original_source_ring_overrun": max(0, record["original_stage8_source_ring_vertices"] - record["original_stage8_source_ring_cap"]),
        "expanded_svg_vertices": record["expanded_svg_vertices"],
        "expanded_svg_vertex_cap": record["expanded_svg_vertex_cap"],
        "source_budget_pass": source_ok,
        "expanded_svg_budget_pass": svg_ok,
        "source_owner_exact": owner_ok,
        "protected_face_arm_unchanged": protected_ok,
        "source_silhouette_exact": silhouette_ok,
        "numerical_candidate_eligible_for_independent_review": eligible,
        "source_authority_bytes_verified": False,
        "human_visual_golden": "HOLD",
        "L04_formal": "HOLD",
        "production_release": "NO_GO",
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_json", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(json.loads(args.evidence_json.read_text(encoding="utf-8"))), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
