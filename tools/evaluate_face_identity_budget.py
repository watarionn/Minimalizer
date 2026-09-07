from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean

from minimalize_engine import MinimalizeConfig, minimalize


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Evaluate Phase 10.5-b Adaptive Face Identity Budget.")
    p.add_argument("--max-side", type=int, default=220)
    return p


def main() -> None:
    args = build_parser().parse_args()
    root = Path(__file__).parents[1]
    corpus = root / "tests" / "assets" / "corpus"
    out = root / "examples" / "face_identity_budget_alpha10_dev5b"
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
            target_max_shapes=30,
            line_mode="none",
            enable_auto_retry=False,
            enable_character_auto_retry=False,
        )
        scene = minimalize(path, cfg)
        face_meta = (
            scene.metadata.get("character", {})
            .get("details", {})
            .get("face", {})
        )
        plan = face_meta.get("identity_plan")
        budget = face_meta.get("identity_budget")
        signals = face_meta.get("identity_signals")

        if plan is None or budget is None or signals is None:
            row = {
                "file": path.name,
                "available": False,
                "visibility_tier": "none",
                "legacy_face_shapes": face_meta.get("shape_count", 0),
            }
        else:
            reserved = budget["reserved_shapes"]
            row = {
                "file": path.name,
                "available": True,
                "visibility_tier": signals["visibility_tier"],
                "minimality_level": plan["minimality_level"],
                "available_face_budget": budget["available_shapes"],
                "planned_face_shapes": budget["total_reserved"],
                "released_face_slots": budget["released_shapes"],
                "legacy_face_shapes": face_meta.get("shape_count", 0),
                "face_base": reserved["face_base"],
                "primary_eye": reserved["primary_eye"],
                "secondary_eye": reserved["secondary_eye"],
                "mouth": reserved["mouth"],
                "helper": reserved["helper"],
                "eye_salience": signals["eye_salience_score"],
                "second_eye_salience": signals["second_eye_salience_score"],
                "mouth_salience": signals["mouth_salience_score"],
                "fringe_relation": signals["fringe_relation_score"],
                "feature_density": signals["feature_density_score"],
            }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))

    valid = [row for row in rows if row.get("available")]
    distribution = Counter(row["planned_face_shapes"] for row in valid)
    minimality = Counter(row["minimality_level"] for row in valid)
    summary = {
        "version": "0.3.0-alpha10-dev5b",
        "phase": "10.5-b Adaptive Face Identity Budget",
        "character_images": len(rows),
        "budget_available_images": len(valid),
        "planned_shape_distribution": {str(k): v for k, v in sorted(distribution.items())},
        "minimality_levels": dict(sorted(minimality.items())),
        "mean_available_face_budget": mean(row["available_face_budget"] for row in valid),
        "mean_planned_face_shapes": mean(row["planned_face_shapes"] for row in valid),
        "mean_legacy_face_shapes": mean(row["legacy_face_shapes"] for row in valid),
        "mean_released_face_slots": mean(row["released_face_slots"] for row in valid),
        "primary_eye_selected": sum(row["primary_eye"] for row in valid),
        "secondary_eye_selected": sum(row["secondary_eye"] for row in valid),
        "mouth_selected": sum(row["mouth"] for row in valid),
        "helper_selected": sum(row["helper"] for row in valid),
        "plans_using_only_face_base": sum(row["planned_face_shapes"] == 1 for row in valid),
        "plans_at_most_two_shapes": sum(row["planned_face_shapes"] <= 2 for row in valid),
        "rendering_changed_by_phase_10_5b": False,
    }

    with (out / "report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        writer = csv.DictWriter(f, fieldnames=fieldnames)
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
