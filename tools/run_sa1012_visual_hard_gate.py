from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalizer_zerobase.evaluation.adopted_baseline_registry import (
    BaselineAdoptionRecord,
    bind_adopted_baseline,
)
from minimalizer_zerobase.evaluation.canonical_hard_gate import (
    evaluate_canonical_hard_gate,
)

ARTIFACT_VERSION = "sa10.12-v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rgb(path: Path):
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(path)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def _mask(path: Path):
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(path)
    return image > 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adoption-record", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--subject-mask", type=Path, required=True)
    parser.add_argument("--face-mask", type=Path, required=True)
    parser.add_argument("--evaluation-transaction-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    record = BaselineAdoptionRecord.from_mapping(
        json.loads(args.adoption_record.read_text(encoding="utf-8"))
    )
    binding = bind_adopted_baseline(
        record,
        actual_source_sha256=_sha256(args.source),
        actual_baseline_sha256=_sha256(args.baseline),
        candidate_artifact_sha256=_sha256(args.current),
        evaluation_transaction_id=args.evaluation_transaction_id,
    )
    if not binding.binding_passed:
        raise ValueError("adopted baseline binding failed")

    report = evaluate_canonical_hard_gate(
        adopted_baseline_rgb=_rgb(args.baseline),
        current_rgb=_rgb(args.current),
        source_rgb=_rgb(args.source),
        subject_mask=_mask(args.subject_mask),
        face_mask=_mask(args.face_mask),
    )
    payload = {
        "artifact_version": ARTIFACT_VERSION,
        "case_id": record.case_id,
        "binding": binding.to_dict(),
        "canonical_hard_gate": report.to_dict(),
        "feature_survival": {
            "status": "AVAILABLE",
            "passed": report.survival_pass,
            "required_signature_count": report.required_signature_count,
            "missing_count": report.missing_count,
            "missing_signatures": [
                signature.to_dict()
                if hasattr(signature, "to_dict")
                else {
                    "position": list(signature.position),
                    "color": list(signature.color),
                }
                for signature in report.missing_signatures
            ],
        },
        "forbidden_face_detail": {
            "status": "AVAILABLE",
            "passed": report.forbidden_face_pass,
            "ratio": report.forbidden_face_detail_ratio,
        },
        "boundary": {
            "candidate_self_reference_forbidden": True,
            "same_transaction": binding.same_transaction,
            "production_inference_allowed": False,
            "golden_used_for_inference": False,
            "browser_v12_used_for_inference": False,
            "aggregate_quality_score": False,
            "new_quality_thresholds": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(_sha256(args.output))
    return 0 if report.pass_gate else 2


if __name__ == "__main__":
    raise SystemExit(main())
