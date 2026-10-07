"""Tiny subprocess boundary for the optional VTracer native extension.

The parent process must never import vtracer: a bad native wheel must only
kill this worker, not the Minimalizer process.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_png", type=Path)
    parser.add_argument("output_svg", type=Path)
    parser.add_argument("--settings", default="{}")
    args = parser.parse_args()
    # Deliberately import inside the isolated process.
    import vtracer  # type: ignore

    settings = json.loads(args.settings)
    args.output_svg.parent.mkdir(parents=True, exist_ok=True)
    vtracer.convert_image_to_svg_py(str(args.input_png), str(args.output_svg), **settings)
    if not args.output_svg.is_file() or args.output_svg.stat().st_size == 0:
        raise RuntimeError("vtracer produced no SVG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
