from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from minimalize_engine.v2 import AnalysisGuidance
from minimalize_engine.v2.pipeline import (
    LayeredPersonConfig,
    PipelineConfig,
    minimalize_v2,
)
from minimalize_engine.v2.semantic_advisor import (
    collect_semantic_advisor_candidates,
)


CONTRACT = "minimalizer-semantic-advisor-v1"


def _load_rgba_with_subject_alpha(path: Path):
    image = Image.open(path).convert("RGBA")
    rgba = np.asarray(image, dtype=np.uint8)
    alpha = rgba[..., 3].astype(np.float32) / 255.0
    if float(alpha.min()) >= 1.0:
        raise ValueError(
            "input has no transparent background; "
            "this opt-in dev exporter currently requires source alpha"
        )
    rgb = rgba[..., :3].copy()
    guidance = AnalysisGuidance(
        subject_prob=alpha,
        subject_confidence=np.ones_like(alpha, dtype=np.float32),
        subject_provider="source-alpha",
        subject_model="source-alpha",
    )
    return rgb, guidance


def export_candidates(
    input_path: Path,
    output_path: Path,
    *,
    analysis_max_side: int = 320,
) -> dict[str, object]:
    rgb, guidance = _load_rgba_with_subject_alpha(input_path)
    result = minimalize_v2(
        rgb,
        presets=("minimal",),
        config=PipelineConfig(
            analysis_max_side=analysis_max_side,
            layered_person=LayeredPersonConfig(enabled=True),
        ),
        guidance=guidance,
    )
    candidates = collect_semantic_advisor_candidates(
        result,
        preset="minimal",
    )
    payload: dict[str, object] = {
        "contract": CONTRACT,
        "mode": "advisory_only",
        "source_input": str(input_path),
        "preset": "minimal",
        "analysis_max_side": analysis_max_side,
        "candidate_count": len(candidates),
        "render_changes_authority": False,
        "merge_prune_authority": False,
        "image_bytes_for_jev": False,
        "candidates": [candidate.as_dict() for candidate in candidates],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export render-impacting hidden semantic planes for the "
            "optional Jev QA advisor. This tool never changes Minimalizer output."
        )
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--analysis-max-side", type=int, default=320)
    args = parser.parse_args()

    payload = export_candidates(
        args.input,
        args.output,
        analysis_max_side=args.analysis_max_side,
    )
    print(
        json.dumps(
            {
                "contract": payload["contract"],
                "candidate_count": payload["candidate_count"],
                "output": str(args.output),
                "render_changes_authority": False,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
