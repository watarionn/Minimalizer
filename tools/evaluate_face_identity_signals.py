from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean

from minimalize_engine import MinimalizeConfig, minimalize


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Evaluate Phase 10.5-a Face Identity Signals.")
    p.add_argument("--max-side", type=int, default=220)
    return p


def main() -> None:
    args = build_parser().parse_args()
    root = Path(__file__).parents[1]
    corpus = root / "tests" / "assets" / "corpus"
    out = root / "examples" / "face_identity_alpha10_dev5a"
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
        signals = (
            scene.metadata.get("character", {})
            .get("details", {})
            .get("face", {})
            .get("identity_signals")
        )
        if signals is None:
            row = {
                "file": path.name,
                "available": False,
                "visibility_tier": "none",
            }
        else:
            row = {
                "file": path.name,
                "available": True,
                "visibility_tier": signals["visibility_tier"],
                "face_render_scale": signals["face_render_scale"],
                "face_size_score": signals["face_size_score"],
                "primary_eye_side": signals["primary_eye_side"],
                "eye_salience": signals["eye_salience_score"],
                "second_eye_salience": signals["second_eye_salience_score"],
                "mouth_salience": signals["mouth_salience_score"],
                "fringe_relation": signals["fringe_relation_score"],
                "contour_salience": signals["contour_salience_score"],
                "expression_salience": signals["expression_salience_score"],
                "feature_density": signals["feature_density_score"],
                "useful_signal_count": signals["diagnostics"]["useful_signal_count"],
                "face_shapes": scene.metadata.get("character", {})
                .get("details", {}).get("face", {}).get("shape_count", 0),
            }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))

    valid = [row for row in rows if row.get("available")]
    tiers = Counter(row["visibility_tier"] for row in valid)
    primary_sides = Counter(row["primary_eye_side"] for row in valid)
    summary = {
        "version": "0.3.0-alpha10-dev5a",
        "phase": "10.5-a Face Identity Signal analysis",
        "character_images": len(rows),
        "signal_available_images": len(valid),
        "visibility_tiers": dict(sorted(tiers.items())),
        "primary_eye_sides": dict(sorted(primary_sides.items())),
        "mean_face_render_scale": mean(row["face_render_scale"] for row in valid),
        "mean_face_size_score": mean(row["face_size_score"] for row in valid),
        "mean_eye_salience": mean(row["eye_salience"] for row in valid),
        "mean_second_eye_salience": mean(row["second_eye_salience"] for row in valid),
        "mean_mouth_salience": mean(row["mouth_salience"] for row in valid),
        "mean_fringe_relation": mean(row["fringe_relation"] for row in valid),
        "mean_contour_salience": mean(row["contour_salience"] for row in valid),
        "mean_expression_salience": mean(row["expression_salience"] for row in valid),
        "mean_feature_density": mean(row["feature_density"] for row in valid),
        "second_eye_salience_ge_0_45": sum(row["second_eye_salience"] >= 0.45 for row in valid),
        "mouth_salience_ge_0_50": sum(row["mouth_salience"] >= 0.50 for row in valid),
        "fringe_relation_ge_0_50": sum(row["fringe_relation"] >= 0.50 for row in valid),
        "expression_salience_ge_0_60": sum(row["expression_salience"] >= 0.60 for row in valid),
        "rendering_changed_by_phase_10_5a": False,
    }

    (out / "report.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if rows:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        with (out / "report.csv").open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
