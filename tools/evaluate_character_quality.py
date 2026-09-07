from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


def parser():
    p = argparse.ArgumentParser(
        description="Evaluate v0.3-alpha8 Character-specific Quality / Retry."
    )
    p.add_argument("--max-side", type=int, default=220)
    return p


def _scene(path: Path, max_side: int, **overrides):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=max_side,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        **overrides,
    )
    return minimalize(path, cfg)


def main():
    args = parser().parse_args()
    root = Path(__file__).parents[1]
    corpus = root / "tests/assets/corpus"
    out = root / "examples/character_quality_alpha8"
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for path in sorted(corpus.iterdir()):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        scene = _scene(path, args.max_side)
        if not scene.metadata.get("character", {}).get("enabled", False):
            continue

        cq = scene.metadata["character_quality"]
        row = {
            "file": path.name,
            "score": cq["score"],
            "face_applicable": cq["face_applicable"],
            "face_retention": cq["face_retention_score"],
            "face_safety": cq["face_safety_score"],
            "body_readability": cq["body_readability_score"],
            "limb_applicable": cq["limb_separation_applicable"],
            "limb_separation": cq["limb_separation_score"],
            "prop_applicable": cq["prop_applicable"],
            "prop_retention": cq["prop_retention_score"],
            "layout": cq["layout_score"],
            "retry_reasons": "|".join(cq["retry_reasons"]),
            "generic_quality": scene.metadata.get("quality", {}).get("score"),
            "selection_score": scene.metadata.get("retry_selection_score"),
        }
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))

    def mean(key):
        vals = [
            float(r[key])
            for r in rows
            if isinstance(r.get(key), (int, float))
            and not isinstance(r.get(key), bool)
        ]
        return sum(vals) / max(1, len(vals))

    summary = {
        "character_images": len(rows),
        "mean_score": mean("score"),
        "mean_face_retention": mean("face_retention"),
        "mean_face_safety": mean("face_safety"),
        "mean_body_readability": mean("body_readability"),
        "mean_limb_separation": mean("limb_separation"),
        "mean_prop_retention": mean("prop_retention"),
        "mean_layout": mean("layout"),
        "retry_needed_images": sum(bool(r["retry_reasons"]) for r in rows),
        "mean_generic_quality": mean("generic_quality"),
        "mean_selection_score": mean("selection_score"),
    }

    # Recovery benchmark: inject three distinct Character-quality failures
    # while keeping the relevant feature enabled. Retry is never allowed to
    # override an explicit user feature switch.
    recovery_cases = []
    scenarios = [
        (
            "low_analysis_limb_loss",
            corpus / "Isaki-Riona_pr-img_01_a.png",
            {
                "analysis_max_side": 110,
            },
        ),
        (
            "overwide_limbs",
            corpus / "Rindo-Chihaya_pr-img_01_a.png",
            {
                "character_limb_width_scale": 1.20,
                "character_quality_min_limb_separation": 0.99,
            },
        ),
        (
            "poor_layout_centering",
            corpus / "Isaki-Riona_pr-img_01_a.png",
            {
                "character_layout_visual_center_strength": 0.0,
                "character_quality_min_layout": 0.90,
            },
        ),
    ]
    for name, path, overrides in scenarios:
        broken_cfg = MinimalizeConfig.from_level(
            4,
            analysis_max_side=overrides.get("analysis_max_side", args.max_side),
            target_max_shapes=30,
            line_mode="none",
            enable_auto_retry=False,
            enable_character_auto_retry=False,
            **{k: v for k, v in overrides.items() if k != "analysis_max_side"},
        )
        broken = minimalize(path, broken_cfg)

        retry_cfg = broken_cfg.with_overrides(
            enable_character_auto_retry=True,
            character_max_retries=1,
        )
        recovered = minimalize(path, retry_cfg)
        recovery_cases.append({
            "scenario": name,
            "before_score": broken.metadata["character_quality"]["score"],
            "after_score": recovered.metadata["character_quality"]["score"],
            "before_reasons": broken.metadata["character_quality"]["retry_reasons"],
            "after_reasons": recovered.metadata["character_quality"]["retry_reasons"],
            "character_retry_attempts": recovered.metadata.get("character_retry_attempts", 0),
            "strategies": [
                s
                for item in recovered.metadata.get("retry_history", [])
                for s in item.get("strategy", [])
            ],
            "improved": (
                recovered.metadata["character_quality"]["score"]
                > broken.metadata["character_quality"]["score"]
            ),
        })

    summary["recovery_cases"] = recovery_cases
    summary["recovery_successes"] = sum(
        r["improved"] and r["character_retry_attempts"] >= 1
        for r in recovery_cases
    )

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
