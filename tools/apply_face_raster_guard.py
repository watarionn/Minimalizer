from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from minimalizer_zerobase.semantic_abstraction.face_raster_guard import (
    apply_face_raster_guard,
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
        description="Apply the deterministic source-derived face raster guard."
    )
    parser.add_argument("--rendered", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--face-mask", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    result = apply_face_raster_guard(
        _rgb(args.rendered),
        _rgb(args.source),
        _mask(args.face_mask),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(
        str(args.output),
        cv2.cvtColor(result.rgb, cv2.COLOR_RGB2BGR),
    )
    payload = result.to_dict()
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
