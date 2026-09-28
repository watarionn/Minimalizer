from __future__ import annotations

import argparse
import json
import sys
from importlib.metadata import version
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from minimalize_engine.v2.rembg_guidance import (
    RembgGuidanceConfig,
    build_rembg_guidance,
    create_rembg_session,
)
from minimalizer_zerobase.analyzers.contracts import Provenance
from minimalizer_zerobase.subject.artifacts import write_phase3_artifacts
from minimalizer_zerobase.subject.extraction import extract_canonical_subject


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 3 subject extraction.",
    )
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts/zerobase2"),
    )
    parser.add_argument("--rembg-model", default="isnet-anime")
    parser.add_argument("--mask-threshold", type=float, default=0.5)
    parser.add_argument("--max-alpha-foreground-ratio", type=float, default=0.97)
    parser.add_argument(
        "--minimum-component-area-ratio",
        type=float,
        default=0.0002,
    )
    return parser.parse_args()


def case_id(path: Path) -> str:
    return path.stem.replace("_list_thumb", "").replace("(4)", "").strip("_-")


def main() -> int:
    args = parse_args()
    rembg_config = RembgGuidanceConfig(model=args.rembg_model)
    session = None

    def probability_provider(rgb):
        nonlocal session
        if session is None:
            session = create_rembg_session(rembg_config)
        guidance = build_rembg_guidance(
            rgb,
            config=rembg_config,
            session=session,
        )
        provenance = Provenance(
            producer=guidance.subject_provider or "rembg",
            producer_version=version("rembg"),
            model_id=guidance.subject_model,
        )
        return guidance.subject_prob, provenance

    config = {
        "mask_threshold": args.mask_threshold,
        "max_alpha_foreground_ratio": args.max_alpha_foreground_ratio,
        "minimum_component_area_ratio": args.minimum_component_area_ratio,
        "fallback_provider": "rembg",
        "fallback_model": args.rembg_model,
        "alpha_policy": "use_only_when_foreground_ratio_is_informative",
    }

    summaries = []
    for source_path in args.inputs:
        with Image.open(source_path) as image:
            extraction = extract_canonical_subject(
                image,
                probability_provider=probability_provider,
                mask_threshold=args.mask_threshold,
                minimum_component_area_ratio=args.minimum_component_area_ratio,
                max_alpha_foreground_ratio=args.max_alpha_foreground_ratio,
            )
        output_dir = args.output_root / case_id(source_path) / "phase_03"
        stage = write_phase3_artifacts(
            source_path,
            extraction,
            output_dir,
            config=config,
        )
        summaries.append(
            {
                "case_id": case_id(source_path),
                "output_dir": str(output_dir),
                "evidence_source": extraction.metadata.evidence_source,
                "foreground_ratio": extraction.metadata.foreground_ratio,
                "bbox_xywh": extraction.metadata.bbox_xywh,
                "alpha_informative": extraction.metadata.alpha_informative,
                "source_sha256": stage["source"]["sha256"],
            }
        )

    print(json.dumps(summaries, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
