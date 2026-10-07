from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from minimalizer_zerobase.artifact_contract.bridge import bridge_stage_contracts
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.evaluation.actual_emission_support import (
    measure_actual_emission_support,
)
from minimalizer_zerobase.evaluation.source_authority_evidence import (
    build_source_authority_evidence,
)
from minimalizer_zerobase.evaluation.structural_hard_evidence import (
    evaluate_structural_hard_evidence,
)
from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.semantic_abstraction.macro_geometry_reauthoring import (
    reauthor_macro_geometry_with_budget,
)

ARTIFACT_VERSION = "sa10.10-v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_mask(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"cannot read mask: {path}")
    return image > 0


def _source_masks(case_dir: Path) -> dict[str, np.ndarray]:
    root = case_dir / "phase_04" / "part_masks"
    return {name: _read_mask(root / f"{name}.png") for name in PART_NAMES}


def _candidate_masks(case_dir: Path) -> dict[str, np.ndarray]:
    payload = _load(case_dir / "phase_12" / "12_simplification.json")
    selected_name = payload["selected_name"]
    selected = next(
        row for row in payload["candidates"]
        if row["name"] == selected_name
    )
    space = payload["coordinate_space"]
    width = int(space["pixel_width"])
    height = int(space["pixel_height"])
    masks = {
        name: np.zeros((height, width), dtype=bool)
        for name in PART_NAMES
    }
    for primitive in selected["primitives"]:
        part = primitive.get("composition_part") or primitive.get("semantic_part_id")
        if part not in masks:
            continue
        masks[part] |= rasterize_primitive_candidate(
            primitive,
            width=width,
            height=height,
        )
    return masks


def build_case_evidence(
    *,
    case_dir: Path,
    source: Path,
    output_dir: Path,
) -> dict:
    source_masks = _source_masks(case_dir)
    candidate_masks = _candidate_masks(case_dir)
    phase4_metrics = _load(case_dir / "phase_04" / "metrics.json")
    phase14_stage = _load(case_dir / "phase_14" / "stage.json")
    expected_source_sha = phase14_stage["source"]["sha256"]
    actual_source_sha = _sha256(source)

    bridge = bridge_stage_contracts(
        case_dir,
        source,
        output_dir=output_dir / "provenance_bridge",
        max_phase=14,
    )
    source_authority = build_source_authority_evidence(
        expected_source_sha256=expected_source_sha,
        actual_source_sha256=actual_source_sha,
        provenance_gate_passed=bridge.gate_result.passed,
        provenance_artifact_count=len(bridge.artifacts),
    )

    structural = evaluate_structural_hard_evidence(
        source_masks=source_masks,
        candidate_masks=candidate_masks,
        accessory_kind=str(phase4_metrics.get("accessory_kind", "none")),
        accessory_confidence=float(phase4_metrics.get("accessory_score", 0.0)),
    )

    macro_primitives, macro_budget = reauthor_macro_geometry_with_budget(
        hair_mask=source_masks["hair"],
        clothing_mask=source_masks["major_clothing"],
        global_primitive_budget=5,
    )
    actual_emission = measure_actual_emission_support(
        role_masks={
            "hair": source_masks["hair"],
            "major_clothing": source_masks["major_clothing"],
        },
        primitives=macro_primitives,
        budget=macro_budget,
    )

    production_candidate = case_dir / "phase_12" / "12_final.png"
    payload = {
        "artifact_version": ARTIFACT_VERSION,
        "case_id": case_dir.name,
        "source": {
            "path": source.name,
            "sha256": actual_source_sha,
        },
        "production_candidate": {
            "path": "phase_12/12_final.png",
            "sha256": _sha256(production_candidate),
        },
        "adopted_baseline": {
            "status": "UNAVAILABLE",
            "bound": False,
            "reason": (
                "No canonical adopted visual baseline is bound for this Phase14 "
                "case; candidate self-reference is forbidden."
            ),
        },
        "hard_evidence": {
            "feature_survival": {
                "status": "UNAVAILABLE",
                "passed": None,
                "reason": "Canonical hard gate requires a separately adopted visual baseline.",
            },
            "forbidden_face_detail": {
                "status": "UNAVAILABLE",
                "passed": None,
                "reason": "Canonical face hard gate is part of the adopted-baseline visual contract.",
            },
            "anatomy": {
                "status": "AVAILABLE",
                "passed": structural.anatomy_pass,
            },
            "topology": {
                "status": "AVAILABLE",
                "passed": structural.topology_pass,
            },
            "source_authority": {
                "status": "AVAILABLE",
                "passed": source_authority.passed,
            },
        },
        "source_authority_evidence": source_authority.to_dict(),
        "structural_hard_evidence": structural.to_dict(),
        "actual_emission_support": actual_emission.to_dict(),
        "boundary": {
            "phase14_metrics_reused_as_hard_evidence": False,
            "candidate_used_as_own_baseline": False,
            "actual_emission_maps_to_sa10_component_survival": False,
            "actual_emission_maps_to_sa10_primitive_economy": False,
            "aggregate_quality_score": False,
            "new_quality_thresholds": False,
        },
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_case_evidence(
        case_dir=args.case_dir,
        source=args.source,
        output_dir=args.output_dir,
    )
    output = args.output_dir / f"{args.case_dir.name}.sa10.10-hard-evidence.json"
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(_sha256(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
