from __future__ import annotations

import argparse
import json
import sys
from importlib.metadata import version
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from minimalize_engine.v2.analysis_guidance import AnalysisGuidance
from minimalize_engine.v2.person_parts import build_person_part_partition
from minimalize_engine.v2.mediapipe_guidance import (
    MediaPipeSemanticConfig,
    build_mediapipe_semantic_guide,
    create_mediapipe_segmenter,
)
from minimalize_engine.v2.rtmlib_guidance import (
    RtmlibStructuralConfig,
    attach_rtmlib_structure,
    create_rtmlib_wholebody,
)
from minimalizer_zerobase.parts.artifacts import write_phase4_artifacts
from minimalizer_zerobase.parts.decomposition import decompose_semantic_parts
from minimalizer_zerobase.subject.artifacts import sha256_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ZeroBase 2nd Cycle Phase 4 semantic part decomposition.",
    )
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts/zerobase2"),
    )
    parser.add_argument("--rtmlib-mode", default="balanced")
    parser.add_argument("--rtmlib-device", default="cpu")
    parser.add_argument(
        "--mediapipe-model",
        type=Path,
        default=Path.home()
        / ".cache"
        / "minimalizer"
        / "mediapipe"
        / "selfie_multiclass_256x256.tflite",
    )
    return parser.parse_args()


def case_id(path: Path) -> str:
    return path.stem.replace("_list_thumb", "").replace("(4)", "").strip("_-")


def main() -> int:
    args = parse_args()
    structural_config = RtmlibStructuralConfig(
        mode=args.rtmlib_mode,
        device=args.rtmlib_device,
    )
    model = create_rtmlib_wholebody(structural_config)

    semantic_segmenter = None
    semantic_config = None
    semantic_model_sha256 = None
    if args.mediapipe_model.is_file():
        semantic_config = MediaPipeSemanticConfig(
            model_path=str(args.mediapipe_model),
            foreground_only=True,
        )
        semantic_segmenter = create_mediapipe_segmenter(semantic_config)
        semantic_model_sha256 = sha256_file(args.mediapipe_model)

    config = {
        "subject_source": "phase03-canonical-mask",
        "structural_provider": "rtmlib",
        "structural_model": structural_config.model_name,
        "rtmlib_mode": args.rtmlib_mode,
        "rtmlib_device": args.rtmlib_device,
        "face_locator": "structure-face-locator-v1",
        "hair_growth": "seed-color-connected-v2-with-optional-mediapipe-guard",
        "accessory_detection": "peripheral-linear-or-vivid-accent-v1",
        "overlap_policy": "appearance-over-structural-for-display",
        "semantic_hint_provider": (
            "mediapipe" if semantic_segmenter is not None else "none"
        ),
        "semantic_hint_model": (
            None if semantic_config is None else semantic_config.model_name
        ),
        "semantic_hint_model_sha256": semantic_model_sha256,
        "mediapipe_version": (
            None if semantic_segmenter is None else version("mediapipe")
        ),
    }

    summaries = []
    for source_path in args.inputs:
        cid = case_id(source_path)
        phase3_dir = args.output_root / cid / "phase_03"
        subject_path = phase3_dir / "03_subject_mask.png"
        if not subject_path.exists():
            raise FileNotFoundError(
                f"Phase 3 canonical subject mask is missing: {subject_path}"
            )

        with Image.open(source_path) as image:
            rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
        subject = np.asarray(
            Image.open(subject_path).convert("L"),
            dtype=np.uint8,
        ) > 0
        base = AnalysisGuidance(
            subject_prob=subject.astype(np.float32),
            subject_provider="zerobase2-phase3",
            subject_model="canonical-subject-mask",
        )
        guided, selection = attach_rtmlib_structure(
            rgb,
            config=structural_config,
            base_guidance=base,
            model=model,
        )
        partition = build_person_part_partition(guided)
        quality = 0.0 if selection is None else float(selection.quality)

        semantic_hints = None
        semantic_summary = {
            "provider": "none",
            "model": None,
            "hair_high_confidence_ratio": 0.0,
        }
        if semantic_segmenter is not None and semantic_config is not None:
            semantic = build_mediapipe_semantic_guide(
                rgb,
                config=semantic_config,
                segmenter=semantic_segmenter,
                subject_prob=subject.astype(np.float32),
            )
            semantic_hints = {
                label: semantic.confidence_maps[index]
                for index, label in enumerate(semantic.labels)
            }
            hair_map = semantic_hints.get("hair")
            semantic_summary = {
                "provider": semantic.provider,
                "model": semantic.model,
                "hair_high_confidence_ratio": (
                    0.0
                    if hair_map is None
                    else float(np.mean(hair_map >= 0.20))
                ),
            }

        face_landmarks = None
        face_landmark_scores = None
        if selection is not None and len(selection.keypoints) >= 91:
            face_landmarks = selection.keypoints[23:91]
            face_landmark_scores = selection.scores[23:91]

        result = decompose_semantic_parts(
            rgb,
            subject,
            partition.part_masks,
            structural_quality=quality,
            semantic_hints=semantic_hints,
            face_landmarks=face_landmarks,
            face_landmark_scores=face_landmark_scores,
        )

        output_dir = args.output_root / cid / "phase_04"
        structural = {
            "provider": "rtmlib",
            "model": structural_config.model_name,
            "selection_present": selection is not None,
            "quality": quality,
            "person_index": None if selection is None else int(selection.person_index),
            "duplicate_indices": [] if selection is None else list(selection.duplicate_indices),
            "keypoints_body17": (
                None
                if selection is None
                else np.round(selection.keypoints[:17], 4).tolist()
            ),
            "scores_body17": (
                None
                if selection is None
                else np.round(selection.scores[:17], 6).tolist()
            ),
            "keypoints_face68": (
                None
                if selection is None or len(selection.keypoints) < 91
                else np.round(selection.keypoints[23:91], 4).tolist()
            ),
            "scores_face68": (
                None
                if selection is None or len(selection.scores) < 91
                else np.round(selection.scores[23:91], 6).tolist()
            ),
            "semantic_hint": semantic_summary,
        }
        stage = write_phase4_artifacts(
            source_path,
            phase3_dir,
            result,
            output_dir,
            config=config,
            structural=structural,
        )
        summaries.append(
            {
                "case_id": cid,
                "output_dir": str(output_dir),
                "structural_quality": quality,
                "face_score": result.face_score,
                "face_source": result.face_source,
                "face_landmark_confidence": result.face_landmark_confidence,
                "face_bbox_xywh": result.face_bbox_xywh,
                "accessory_kind": result.accessory_kind,
                "accessory_score": result.accessory_score,
                "part_coverage": result.coverage(),
                "source_sha256": stage["source"]["sha256"],
            }
        )

    if semantic_segmenter is not None:
        try:
            semantic_segmenter.close()
        except Exception:
            pass
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
