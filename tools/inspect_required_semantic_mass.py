from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from minimalizer_zerobase.semantic_abstraction.required_semantic_mass import (
    reserve_required_semantic_masses,
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
        description="Inspect source-only required semantic mass reservations."
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--semantic-mask-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    masks = {
        path.stem: _mask(path)
        for path in sorted(args.semantic_mask_dir.glob("*.png"))
    }
    rows = reserve_required_semantic_masses(_rgb(args.source), masks)
    payload = {
        "stage": "SA7.37",
        "reservation_count": len(rows),
        "reservations": [row.to_dict() for row in rows],
    }
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
