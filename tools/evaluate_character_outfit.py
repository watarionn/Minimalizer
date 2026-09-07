from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


def parser():
    p = argparse.ArgumentParser(description="Evaluate v0.3-alpha3 outfit reconstruction.")
    p.add_argument("--max-side", type=int, default=220)
    return p


def main():
    args = parser().parse_args()
    root = Path(__file__).parents[1]
    corpus = root / "tests/assets/corpus"
    out = root / "examples/character_outfit_alpha3"
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for p in sorted(corpus.iterdir()):
        if p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        cfg = MinimalizeConfig.from_level(
            4,
            analysis_max_side=args.max_side,
            target_max_shapes=30,
            line_mode="none",
            enable_auto_retry=False,
        )
        scene = minimalize(p, cfg)
        ch = scene.metadata.get("character", {})
        outfit = ch.get("details", {}).get("outfit", {})
        st = outfit.get("structure") or {}
        row = {
            "file": p.name,
            "character_enabled": ch.get("enabled", False),
            "outfit_shapes": outfit.get("shape_count", 0),
            "torso": st.get("torso") is not None,
            "left_sleeve": st.get("left_sleeve") is not None,
            "right_sleeve": st.get("right_sleeve") is not None,
            "lower": st.get("lower") is not None,
            "lower_type": st.get("lower_type"),
            "left_shoe": st.get("left_shoe") is not None,
            "right_shoe": st.get("right_shoe") is not None,
            "accessories": len(st.get("accessory_region_ids", [])),
            "outfit_confidence": st.get("confidence"),
            "quality": scene.metadata.get("quality", {}).get("score"),
            "shape_count": scene.metadata.get("shape_count"),
        }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))

    subject = [r for r in rows if r["character_enabled"]]
    summary = {
        "images": len(rows),
        "character_images": len(subject),
        "outfit_shape_rate": sum(r["outfit_shapes"] > 0 for r in subject) / max(1, len(subject)),
        "torso_rate": sum(r["torso"] for r in subject) / max(1, len(subject)),
        "any_sleeve_rate": sum(r["left_sleeve"] or r["right_sleeve"] for r in subject) / max(1, len(subject)),
        "both_sleeves_rate": sum(r["left_sleeve"] and r["right_sleeve"] for r in subject) / max(1, len(subject)),
        "lower_rate": sum(r["lower"] for r in subject) / max(1, len(subject)),
        "both_shoes_rate": sum(r["left_shoe"] and r["right_shoe"] for r in subject) / max(1, len(subject)),
        "accessory_rate": sum(r["accessories"] > 0 for r in subject) / max(1, len(subject)),
        "mean_outfit_shapes": sum(r["outfit_shapes"] for r in subject) / max(1, len(subject)),
        "mean_quality": sum((r["quality"] or 0.0) for r in subject) / max(1, len(subject)),
        "mean_shape_count": sum((r["shape_count"] or 0) for r in subject) / max(1, len(subject)),
    }

    (out / "report.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("SUMMARY", json.dumps(summary))


if __name__ == "__main__":
    main()
