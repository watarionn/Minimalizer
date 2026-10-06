from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from minimalizer_zerobase.evaluation.missing_signature_attribution import (
    attribute_missing_signatures,
)
from minimalizer_zerobase.production.feature_survival_gate import FeatureSignature


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
    parser = argparse.ArgumentParser(
        description="Attribute canonical missing feature signatures to source semantic parts."
    )
    parser.add_argument("--gate-report", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--subject-mask", type=Path, required=True)
    parser.add_argument("--semantic-mask-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    gate = json.loads(args.gate_report.read_text(encoding="utf-8"))
    missing = tuple(
        FeatureSignature(
            tuple(int(v) for v in row["rgb"]),
            float(row["area_ratio"]),
            float(row["cx"]),
            float(row["cy"]),
        )
        for row in gate.get("missing_signatures", [])
    )

    masks = {
        path.stem: _mask(path)
        for path in sorted(args.semantic_mask_dir.glob("*.png"))
    }
    rows = attribute_missing_signatures(
        missing_signatures=missing,
        source_rgb=_rgb(args.source),
        subject_mask=_mask(args.subject_mask),
        semantic_masks=masks,
    )
    payload = {
        "stage": "SA7.36",
        "gate_version": gate.get("version"),
        "missing_count": len(rows),
        "attributions": [row.to_dict() for row in rows],
    }
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
