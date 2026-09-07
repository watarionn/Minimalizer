from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


def parser():
    p = argparse.ArgumentParser(description="Evaluate v0.3-alpha5 integrated Character primitives.")
    p.add_argument("--max-side", type=int, default=220)
    return p


def run_one(path: Path, max_side: int, enabled: bool):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=max_side,
        target_max_shapes=32,
        line_mode="none",
        enable_auto_retry=False,
        enable_body_primitives=enabled,
    )
    return minimalize(path, cfg)


def main():
    args = parser().parse_args()
    root = Path(__file__).parents[1]
    corpus = root / "tests/assets/corpus"
    out = root / "examples/character_primitives_alpha5"
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for path in sorted(corpus.iterdir()):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue

        on = run_one(path, args.max_side, True)
        if not on.metadata.get("character", {}).get("enabled", False):
            continue
        off = run_one(path, args.max_side, False)

        ch = on.metadata["character"]
        details = ch["details"]
        body = details["body"]
        analysis = body.get("analysis") or {}
        limbs = analysis.get("limbs") or []
        limb_types = {l["part_type"] for l in limbs}

        q_on = on.metadata.get("quality", {})
        q_off = off.metadata.get("quality", {})

        row = {
            "file": path.name,
            "preset": ch["structure"]["preset"],
            "reserved_body": ch["budget"]["reserved_body"],
            "body_shapes": body.get("shape_count", 0),
            "torso": bool(analysis.get("torso_points")),
            "left_arm": "left_arm" in limb_types,
            "right_arm": "right_arm" in limb_types,
            "left_leg": "left_leg" in limb_types,
            "right_leg": "right_leg" in limb_types,
            "integrated_shapes": ch["shape_result"]["shape_count"],
            "final_shapes_on": on.metadata.get("shape_count"),
            "final_shapes_off": off.metadata.get("shape_count"),
            "quality_on": q_on.get("score"),
            "quality_off": q_off.get("score"),
            "silhouette_on": q_on.get("silhouette_similarity"),
            "silhouette_off": q_off.get("silhouette_similarity"),
            "complexity_on": q_on.get("complexity_score"),
            "complexity_off": q_off.get("complexity_score"),
            "tiny_on": q_on.get("tiny_shape_ratio"),
            "tiny_off": q_off.get("tiny_shape_ratio"),
        }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))

    def mean(key):
        vals = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
        return sum(vals) / max(1, len(vals))

    summary = {
        "character_images": len(rows),
        "torso_rate": sum(r["torso"] for r in rows) / max(1, len(rows)),
        "left_arm_rate": sum(r["left_arm"] for r in rows) / max(1, len(rows)),
        "right_arm_rate": sum(r["right_arm"] for r in rows) / max(1, len(rows)),
        "both_arms_rate": sum(r["left_arm"] and r["right_arm"] for r in rows) / max(1, len(rows)),
        "both_legs_rate": sum(r["left_leg"] and r["right_leg"] for r in rows) / max(1, len(rows)),
        "mean_body_shapes": mean("body_shapes"),
        "mean_integrated_shapes": mean("integrated_shapes"),
        "mean_final_shapes_on": mean("final_shapes_on"),
        "mean_final_shapes_off": mean("final_shapes_off"),
        "mean_quality_on": mean("quality_on"),
        "mean_quality_off": mean("quality_off"),
        "mean_silhouette_on": mean("silhouette_on"),
        "mean_silhouette_off": mean("silhouette_off"),
        "mean_complexity_on": mean("complexity_on"),
        "mean_complexity_off": mean("complexity_off"),
        "mean_tiny_on": mean("tiny_on"),
        "mean_tiny_off": mean("tiny_off"),
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
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print("SUMMARY", json.dumps(summary))


if __name__ == "__main__":
    main()
