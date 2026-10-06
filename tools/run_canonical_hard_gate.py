from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from minimalizer_zerobase.evaluation.canonical_hard_gate import (
    evaluate_canonical_hard_gate,
)


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
        description="Run the canonical source-supported Minimalizer hard gate."
    )
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--subject-mask", type=Path, required=True)
    parser.add_argument("--face-mask", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = evaluate_canonical_hard_gate(
        adopted_baseline_rgb=_rgb(args.baseline),
        current_rgb=_rgb(args.current),
        source_rgb=_rgb(args.source),
        subject_mask=_mask(args.subject_mask),
        face_mask=_mask(args.face_mask),
    )
    payload = report.to_dict()
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report.pass_gate else 2


if __name__ == "__main__":
    raise SystemExit(main())
