from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean

from minimalize_engine import MinimalizeConfig, minimalize


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Evaluate alpha10-dev1 Face Geometry Quality."
    )
    p.add_argument("--max-side", type=int, default=240)
    p.add_argument("--threshold", type=float, default=0.72)
    return p


def main() -> None:
    args = parser().parse_args()
    root = Path(__file__).parents[1]
    corpus = root / "tests/assets/corpus"
    out = root / "examples/face_geometry_alpha10_dev1"
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for path in sorted(corpus.iterdir()):
        if "_pr-img_" not in path.name:
            continue
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue

        cfg = MinimalizeConfig.from_level(
            4,
            analysis_max_side=args.max_side,
            target_max_shapes=32,
            line_mode="none",
            enable_auto_retry=False,
            enable_character_auto_retry=False,
            character_quality_min_face_geometry=args.threshold,
        )
        scene = minimalize(path, cfg)
        cq = scene.metadata["character_quality"]
        fg = cq["diagnostics"]["face_geometry"]

        row = {
            "file": path.name,
            "score": cq["face_geometry_score"],
            "applicable": cq["face_geometry_applicable"],
            "flagged": "face_geometry_low" in cq["retry_reasons"],
            "area_ratio_score": fg.get("area_ratio_score"),
            "center_score": fg.get("center_score"),
            "aspect_score": fg.get("aspect_score"),
            "eye_span_score": fg.get("eye_span_score"),
            "mouth_position_score": fg.get("mouth_position_score"),
            "mask_iou_score": fg.get("mask_iou_score"),
            "head_area_ratio_score": fg.get("head_area_ratio_score"),
            "generated_to_source_area_ratio": (
                (fg.get("diagnostics") or {}).get("generated_to_source_area_ratio")
            ),
        }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))

    applicable = [r for r in rows if r["applicable"] and r["score"] is not None]
    scores = [float(r["score"]) for r in applicable]
    summary = {
        "images": len(rows),
        "applicable_faces": len(applicable),
        "threshold": args.threshold,
        "mean_score": mean(scores) if scores else None,
        "min_score": min(scores) if scores else None,
        "max_score": max(scores) if scores else None,
        "flagged_images": sum(bool(r["flagged"]) for r in rows),
        "flagged_files": [r["file"] for r in rows if r["flagged"]],
    }

    (out / "report.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (out / "report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
