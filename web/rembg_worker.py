from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from minimalize_engine.io.image_loader import load_image
from minimalize_engine.v2.rembg_guidance import (
    RembgGuidanceConfig,
    build_rembg_guidance,
    create_rembg_session,
)


def _session_options():
    import onnxruntime as ort

    options = ort.SessionOptions()
    options.enable_cpu_mem_arena = False
    options.enable_mem_pattern = False
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
    return options


def run_worker(input_path: Path, output_path: Path, *, model: str) -> None:
    config = RembgGuidanceConfig(model=model)
    session = create_rembg_session(config, sess_opts=_session_options())
    guidance = build_rembg_guidance(
        load_image(input_path),
        config=config,
        session=session,
    )
    mask = np.clip(np.rint(guidance.subject_prob * 255.0), 0, 255).astype(np.uint8)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(mask, mode="L").save(output_path, format="PNG")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one isolated rembg inference.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", default="u2netp")
    args = parser.parse_args()
    run_worker(args.input, args.output, model=args.model)


if __name__ == "__main__":
    main()
