from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel

from minimalizer_zerobase.refine.dino_spatial import (
    compare_dino_spatial,
    observation_from_feature_map,
)
from minimalizer_zerobase.refine.semantic import SemanticObservation
from minimalizer_zerobase.semantic_abstraction.semantic_retention_observer import (
    evaluate_semantic_retention,
)

MODEL = "facebook/dinov3-convnext-tiny-pretrain-lvd1689m"
ARTIFACT_VERSION = "sa10.9-v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_sha256(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise ValueError(
            f"sha256 mismatch for {path}: expected {expected}, got {actual}"
        )


def extract(processor, model, path: Path):
    image = Image.open(path).convert("RGB")
    pixels = processor(images=image, return_tensors="pt")["pixel_values"].cuda()
    with torch.inference_mode():
        output = model(pixel_values=pixels, output_hidden_states=True)
    feature_map = (
        output.hidden_states[-1][0]
        .permute(1, 2, 0)
        .float()
        .cpu()
        .numpy()
    )
    return observation_from_feature_map(feature_map)


def build_artifact(
    *,
    case_id: str,
    source: Path,
    source_sha256: str,
    candidate: Path,
    candidate_sha256: str,
) -> dict:
    require_sha256(source, source_sha256)
    require_sha256(candidate, candidate_sha256)

    processor = AutoImageProcessor.from_pretrained(MODEL, local_files_only=True)
    model = AutoModel.from_pretrained(MODEL, local_files_only=True).cuda().eval()

    source_obs = extract(processor, model, source)
    candidate_obs = extract(processor, model, candidate)
    spatial = compare_dino_spatial(source_obs, candidate_obs)

    source_semantic = SemanticObservation(
        global_feature=source_obs.global_feature,
        patch_features=source_obs.features,
    )
    candidate_semantic = SemanticObservation(
        global_feature=candidate_obs.global_feature,
        patch_features=candidate_obs.features,
    )
    retention = evaluate_semantic_retention(
        observer="dinov3-convnext-tiny",
        source=source_semantic,
        candidate=candidate_semantic,
    )

    return {
        "artifact_version": ARTIFACT_VERSION,
        "candidate": {
            "path": candidate.name,
            "sha256": candidate_sha256,
        },
        "case_id": case_id,
        "grid_shape": list(source_obs.grid_shape),
        "hard_gate_override_allowed": False,
        "model": MODEL,
        "production_output_changed": False,
        "semantic_retention": retention.to_dict(),
        "source": {
            "path": source.name,
            "sha256": source_sha256,
        },
        "spatial": {
            "aligned_patch_cosine": spatial.aligned_patch_cosine,
            "coarse_patch_cosine": spatial.coarse_patch_cosine,
            "global_cosine": spatial.global_cosine,
            "research_score": spatial.score,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    artifact = build_artifact(
        case_id=args.case_id,
        source=args.source,
        source_sha256=args.source_sha256,
        candidate=args.candidate,
        candidate_sha256=args.candidate_sha256,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(sha256(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
