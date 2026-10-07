from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.evaluation.source_shape_evidence import evaluate_source_shape_evidence
from minimalizer_zerobase.evaluation.source_silhouette_anatomy_gate import evaluate_source_silhouette_anatomy
from minimalizer_zerobase.evaluation.structural_hard_evidence import evaluate_structural_hard_evidence
from minimalizer_zerobase.evaluation.saliency_perceptual import evaluate_saliency_perceptual
from minimalizer_zerobase.refine.backend import backend_available


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_mask(path: Path) -> np.ndarray:
    mask = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise FileNotFoundError(path)
    return mask > 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    phase3 = args.case_dir / "phase_03"
    phase4 = args.case_dir / "phase_04"
    phase12 = args.case_dir / "phase_12"
    source_mask = load_mask(phase3 / "03_subject_mask.png")
    candidate_rgb = cv2.cvtColor(cv2.imread(str(phase12 / "12_final.png"), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    background = np.median(np.concatenate((candidate_rgb[:4, :4].reshape(-1, 3), candidate_rgb[-4:, -4:].reshape(-1, 3))), axis=0)
    candidate_mask = np.any(np.abs(candidate_rgb.astype(np.int16) - background.astype(np.int16)) > 3, axis=2)
    parts = {}
    for path in sorted((phase4 / "part_masks").glob("*.png")):
        parts[path.stem] = load_mask(path)
    required = ["head", "torso", "left_arm", "right_arm", "face"]
    retained = [name for name, mask in parts.items() if np.any(mask)]
    hard = evaluate_structural_hard_evidence(source_masks=parts, candidate_masks={name: candidate_mask & mask for name, mask in parts.items()})
    shape = evaluate_source_shape_evidence(source_mask, candidate_mask)
    anatomy = evaluate_source_silhouette_anatomy(
        source_mask, candidate_mask, fragmentation_penalty=0.0,
        anatomy_evidence={"required_parts": required, "retained_parts": retained,
                          "shape_matching": shape.get("match_shapes_i1"),
                          "perceptual": "observer-only"},
    )
    perceptual = evaluate_saliency_perceptual(
        cv2.cvtColor(cv2.imread(str(args.source), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB),
        candidate_rgb, parts,
    )
    report = {
        "schema_version": "sa10.23-real-gc001-transaction-v1",
        "case": "GC001_IMG_1205",
        "source": {"path": args.source.name, "sha256": sha256(args.source), "drive_id": "1LxHHizN1nC9JVpbHegqMtO38O6xWwjpj"},
        "phase12": {"selected_profile": json.loads((phase12 / "12_simplification.json").read_text(encoding="utf-8")).get("selected_name"), "final_sha256": sha256(phase12 / "12_final.png")},
        "backend": {"pydiffvg_available": backend_available("diffvg"), "policy": "optional; no generative pixels"},
        "hard_gates": {"sa10_18_source_silhouette_anatomy": anatomy, "sa10_20_structural": hard.to_dict() if hasattr(hard, "to_dict") else hard},
        "observers": {"sa10_19_source_shape": shape, "sa10_21_saliency_perceptual": perceptual},
        "decision": {"candidate_authorized": bool(anatomy["gate"] == "PASS" and hard.anatomy_pass and hard.topology_pass), "malformed_candidate_promoted": False, "production_promotion": False},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "source_sha256": report["source"]["sha256"], "sa10_18": anatomy["gate"], "structural": report["decision"]["candidate_authorized"], "diffvg": report["backend"]["pydiffvg_available"]}, ensure_ascii=False))
    return 0 if report["decision"]["candidate_authorized"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
