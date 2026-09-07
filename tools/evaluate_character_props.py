from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


def parser():
    p = argparse.ArgumentParser(description="Evaluate v0.3-alpha4 prop separation.")
    p.add_argument("--max-side", type=int, default=220)
    return p


def main():
    args = parser().parse_args()
    root = Path(__file__).parents[1]
    corpus = root / "tests/assets/corpus"
    out = root / "examples/character_props_alpha4"
    out.mkdir(parents=True, exist_ok=True)

    gt_path=root / "tests/assets/prop_ground_truth.json"
    ground_truth=json.loads(gt_path.read_text(encoding="utf-8")) if gt_path.exists() else {}

    rows = []
    for path in sorted(corpus.iterdir()):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue

        cfg = MinimalizeConfig.from_level(
            4,
            analysis_max_side=args.max_side,
            target_max_shapes=30,
            line_mode="none",
            enable_auto_retry=False,
        )
        scene = minimalize(path, cfg)
        character = scene.metadata.get("character", {})
        props = character.get("details", {}).get("props", {})
        descriptors = props.get("descriptors", [])
        types = [d.get("prop_type", "unknown") for d in descriptors]
        confidences = [float(d.get("confidence", 0)) for d in descriptors]

        expected=ground_truth.get(path.name)
        exact_match=(sorted(types)==sorted(expected)) if expected is not None else None
        row = {
            "file": path.name,
            "character_enabled": bool(character.get("enabled", False)),
            "prop_count": len(descriptors),
            "prop_shape_count": int(props.get("shape_count", 0)),
            "types": ",".join(types),
            "expected_types": ",".join(expected) if expected is not None else "",
            "ground_truth_exact": exact_match,
            "mean_prop_confidence": sum(confidences) / len(confidences) if confidences else None,
            "staff": "staff_like" in types,
            "sword": "sword_like" in types,
            "microphone": "microphone_like" in types,
            "headphones": "headphone_like" in types,
            "hat": "hat_like" in types,
            "bag": "bag_like" in types,
            "quality": scene.metadata.get("quality", {}).get("score"),
            "shape_count": scene.metadata.get("shape_count"),
        }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))

    subject = [r for r in rows if r["character_enabled"]]
    prop_rows = [r for r in subject if r["prop_count"] > 0]
    gt_rows=[r for r in rows if r["ground_truth_exact"] is not None]
    summary = {
        "images": len(rows),
        "character_images": len(subject),
        "images_with_props": len(prop_rows),
        "prop_image_rate": len(prop_rows) / max(1, len(subject)),
        "mean_prop_count_when_detected": sum(r["prop_count"] for r in prop_rows) / max(1, len(prop_rows)),
        "mean_prop_shapes_when_detected": sum(r["prop_shape_count"] for r in prop_rows) / max(1, len(prop_rows)),
        "mean_prop_confidence": (
            sum(r["mean_prop_confidence"] for r in prop_rows if r["mean_prop_confidence"] is not None)
            / max(1, sum(r["mean_prop_confidence"] is not None for r in prop_rows))
        ),
        "staff_images": sum(r["staff"] for r in subject),
        "sword_images": sum(r["sword"] for r in subject),
        "microphone_images": sum(r["microphone"] for r in subject),
        "headphone_images": sum(r["headphones"] for r in subject),
        "hat_images": sum(r["hat"] for r in subject),
        "bag_images": sum(r["bag"] for r in subject),
        "ground_truth_cases": len(gt_rows),
        "ground_truth_exact_matches": sum(bool(r["ground_truth_exact"]) for r in gt_rows),
        "ground_truth_exact_match_rate": (
            sum(bool(r["ground_truth_exact"]) for r in gt_rows) / max(1, len(gt_rows))
        ),
    }

    (out / "report.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("SUMMARY", json.dumps(summary))


if __name__ == "__main__":
    main()
