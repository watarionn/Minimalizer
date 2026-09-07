from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean

from minimalize_engine import MinimalizeConfig, minimalize


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Evaluate alpha10-dev2 Face Contour Fit ON/OFF on the character corpus."
    )
    p.add_argument("--max-side", type=int, default=240)
    p.add_argument("--max-shapes", type=int, default=32)
    return p


def _scene(path: Path, *, enabled: bool, max_side: int, max_shapes: int):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=max_side,
        target_max_shapes=max_shapes,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_contour_fit=enabled,
    )
    return minimalize(path, cfg)


def main() -> None:
    args = parser().parse_args()
    root = Path(__file__).parents[1]
    corpus = root / "tests/assets/corpus"
    out = root / "examples/face_contour_alpha10_dev2"
    out.mkdir(parents=True, exist_ok=True)

    images = sorted(
        p
        for p in corpus.iterdir()
        if "_pr-img_" in p.name
        and p.suffix.lower() in {".png", ".webp", ".jpg", ".jpeg"}
    )

    rows = []
    for path in images:
        before = _scene(
            path,
            enabled=False,
            max_side=args.max_side,
            max_shapes=args.max_shapes,
        )
        after = _scene(
            path,
            enabled=True,
            max_side=args.max_side,
            max_shapes=args.max_shapes,
        )
        bq = before.metadata["character_quality"]
        aq = after.metadata["character_quality"]
        b = float(bq["face_geometry_score"])
        a = float(aq["face_geometry_score"])
        rows.append({
            "file": path.name,
            "face_geometry_before": b,
            "face_geometry_after": a,
            "delta": a - b,
            "improved": a > b,
            "before_flagged": "face_geometry_low" in bq["retry_reasons"],
            "after_flagged": "face_geometry_low" in aq["retry_reasons"],
            "character_quality_after": aq["score"],
        })
        print(json.dumps(rows[-1], ensure_ascii=False))

    summary = {
        "character_images": len(rows),
        "mean_face_geometry_before": mean(r["face_geometry_before"] for r in rows),
        "mean_face_geometry_after": mean(r["face_geometry_after"] for r in rows),
        "mean_delta": mean(r["delta"] for r in rows),
        "improved_images": sum(bool(r["improved"]) for r in rows),
        "before_flagged_images": sum(bool(r["before_flagged"]) for r in rows),
        "after_flagged_images": sum(bool(r["after_flagged"]) for r in rows),
        "largest_gains": sorted(rows, key=lambda r: r["delta"], reverse=True)[:4],
    }

    with (out / "report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    (out / "report.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
