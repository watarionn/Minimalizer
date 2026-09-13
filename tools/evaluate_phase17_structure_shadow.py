from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minimalize_engine import minimalize_rinka_reference

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate Phase 17 structure-first shadow metadata on an image directory."
    )
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--analysis-max-side", type=int, default=320)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def _images(path: Path) -> list[Path]:
    return sorted(
        item for item in path.iterdir()
        if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES
    )


def evaluate(input_dir: Path, analysis_max_side: int) -> dict:
    rows: list[dict] = []
    fail_reasons: dict[str, int] = {}
    for image_path in _images(input_dir):
        scene = minimalize_rinka_reference(
            image_path,
            4,
            analysis_max_side=analysis_max_side,
            preset="approved_reference",
        )
        shadow = dict(scene.metadata.get("rinka_structure_first_shadow") or {})
        alpha = dict(scene.metadata.get("rinka_alpha_structure_shadow") or {})
        gate = dict(scene.metadata.get("rinka_structure_candidate_gate") or {})
        for reason in gate.get("reasons") or []:
            fail_reasons[reason] = fail_reasons.get(reason, 0) + 1
        rows.append({
            "file": image_path.name,
            "enabled": bool(shadow.get("enabled")),
            "mask_source": shadow.get("mask_source"),
            "gate_passed": bool(gate.get("passed")),
            "gate_reasons": gate.get("reasons") or [],
            "hair_count": int(gate.get("hair_count") or 0),
            "face_count": int(gate.get("face_count") or 0),

            "body_zone_count": int(gate.get("body_zone_count") or 0),
            "shape_count": int(gate.get("shape_count") or 0),
            "carrier_exposure_ratio": float(gate.get("carrier_exposure_ratio") or 0.0),
            "carrier_patch_count": int(gate.get("carrier_patch_count") or 0),
            "alpha_enabled": bool(alpha.get("enabled")),
        })

    passed = [row for row in rows if row["gate_passed"]]
    exposures = [row["carrier_exposure_ratio"] for row in rows]
    hair_counts: dict[str, int] = {}
    for row in rows:
        key = str(row["hair_count"])
        hair_counts[key] = hair_counts.get(key, 0) + 1

    return {
        "count": len(rows),
        "gate_passed": len(passed),
        "gate_failed": len(rows) - len(passed),
        "gate_pass_rate": round(len(passed) / max(len(rows), 1), 6),
        "fail_reasons": dict(sorted(fail_reasons.items())),
        "hair_count_distribution": hair_counts,
        "max_carrier_exposure_ratio": round(max(exposures, default=0.0), 6),
        "rows": rows,
    }


def main() -> int:
    args = _parse_args()
    result = evaluate(args.input_dir, args.analysis_max_side)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
