from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

from minimalize_engine.v2.regression import (
    RegressionConfig,
    VISUAL_REGRESSION_CORPUS_V1,
    load_rgb_file,
    resolve_code_revision,
    run_visual_regression_corpus,
)


def canonical_corpus_paths(
    input_dir: str | Path,
    reference_dir: str | Path | None = None,
) -> tuple[dict[str, Path], dict[str, Path]]:
    inputs = Path(input_dir)
    references = None if reference_dir is None else Path(reference_dir)
    cases: dict[str, Path] = {}
    refs: dict[str, Path] = {}
    for index, name in enumerate(VISUAL_REGRESSION_CORPUS_V1, start=1):
        source = inputs / f"{name}_list_thumb.png"
        if not source.is_file():
            raise FileNotFoundError(f"missing corpus source: {source}")
        cases[name] = source
        if references is not None:
            reference = references / (
                f"{index:02d}_{name}_APPROVED_GEOMETRIC_REFERENCE.png"
            )
            if not reference.is_file():
                raise FileNotFoundError(f"missing approved reference: {reference}")
            refs[name] = reference
    return cases, refs


def validate_corpus_images(
    cases: Mapping[str, Path],
    references: Mapping[str, Path],
) -> None:
    for kind, items in (("source", cases), ("reference", references)):
        for name, path in items.items():
            try:
                load_rgb_file(path)
            except (OSError, ValueError) as exc:
                raise ValueError(
                    f"invalid corpus {kind} image for {name}: {path}"
                ) from exc


def summarize(results: Mapping[str, object]) -> dict[str, dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}
    for name, result in results.items():
        summary[name] = {
            "invariant_failures": len(result.invariant_failures),
            "initial_region_count": result.metrics.initial_region_count,
            "selected_region_count": result.metrics.selected_region_count,
            "contour_iou": result.metrics.contour_iou,
            "primitive_conversion_rate": result.metrics.primitive_conversion_rate,
            "palette_count": result.metrics.palette_count,
            "visual_group_count": result.metrics.visual_group_count,
            "runtime_seconds": result.metrics.runtime_seconds,
            "algorithm_digest": result.algorithm_digest,
            "reference_hash": result.manifest.reference_hash,
        }
    return summary
def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the canonical Minimalizer 2.0 18-case visual regression corpus."
    )
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--reference-dir")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--artifact-level",
        choices=("none", "summary", "standard", "full"),
        default="standard",
    )
    parser.add_argument(
        "--preset",
        choices=("ultra_minimal", "minimal", "balanced", "detailed"),
        default="minimal",
    )
    parser.add_argument("--code-revision")
    return parser


def main() -> int:
    args = _parser().parse_args()
    cases, references = canonical_corpus_paths(args.input_dir, args.reference_dir)
    validate_corpus_images(cases, references)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = run_visual_regression_corpus(
        cases,
        reference_paths=(references or None),
        regression_config=RegressionConfig(
            artifact_level=args.artifact_level,
            main_preset=args.preset,
        ),
        output_root=output_dir,
        code_revision=args.code_revision or resolve_code_revision(),
    )
    summary = summarize(results)
    summary_path = output_dir / "corpus_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    failures = sum(item["invariant_failures"] for item in summary.values())
    print(f"cases={len(summary)} invariant_failures={failures}")
    print(summary_path)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
